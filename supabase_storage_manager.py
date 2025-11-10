import os
import time
from supabase import create_client, Client
from config import Config


class ProgressFileWrapper:
    """Wrapper para file handle que reporta progresso durante leitura"""
    def __init__(self, file_handle, file_size, progress_callback=None):
        self.file_handle = file_handle
        self.file_size = file_size
        self.progress_callback = progress_callback
        self.bytes_read = 0
        self.last_reported_progress = 0
        
    def read(self, size=-1):
        """Lê dados e reporta progresso"""
        data = self.file_handle.read(size)
        self.bytes_read += len(data)
        
        if self.progress_callback and self.file_size > 0:
            progress = (self.bytes_read / self.file_size) * 100
            
            # Reportar progresso a cada 5% para não sobrecarregar
            if progress - self.last_reported_progress >= 5 or self.bytes_read == self.file_size:
                self.progress_callback(
                    f"Enviando: {progress:.1f}% ({self.bytes_read / (1024*1024):.2f}/{self.file_size / (1024*1024):.2f} MB)"
                )
                self.last_reported_progress = progress
        
        return data
    
    def seek(self, offset, whence=0):
        """Implementar seek para compatibilidade"""
        return self.file_handle.seek(offset, whence)
    
    def tell(self):
        """Implementar tell para compatibilidade"""
        return self.file_handle.tell()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        return self.file_handle.__exit__(*args)

class SupabaseStorageManager:
    def __init__(self):
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        self.bucket_name = Config.SUPABASE_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Garante que o bucket existe no Supabase Storage"""
        try:
            buckets = self.client.storage.list_buckets()
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                self.client.storage.create_bucket(
                    self.bucket_name,
                    options={"public": False}
                )
        except Exception as e:
            print(f"Erro ao verificar/criar bucket: {e}")

    def upload_file(self, file_path: str, file_name: str | None = None, progress_callback=None) -> str:
        """
        Faz upload de um arquivo para o Supabase Storage usando streaming
        
        Args:
            file_path: Caminho do arquivo local
            file_name: Nome do arquivo no storage (se None, usa o nome original)
            progress_callback: Função para reportar progresso (recebe mensagem)
            
        Returns:
            str: ID/caminho do arquivo no storage
        """
        # Garantir que file_name sempre tem um valor
        if file_name is None:
            file_name = os.path.basename(file_path)

        # Determine content type based on file extension
        if file_name.endswith('.tar.gz') or file_name.endswith('.tgz'):
            content_type = "application/gzip"
        elif file_name.endswith('.zip'):
            content_type = "application/zip"
        else:
            content_type = "application/octet-stream"

        # Obter tamanho do arquivo
        file_size = os.path.getsize(file_path)
        
        # Configurações de retry para arquivos grandes
        max_retries = 3
        retry_delay = 5  # segundos
        
        for attempt in range(max_retries):
            try:
                if progress_callback:
                    if attempt > 0:
                        progress_callback(f"Tentativa {attempt + 1}/{max_retries}: Retomando upload de {file_size / (1024*1024):.2f} MB...")
                    else:
                        progress_callback(f"Iniciando upload de {file_size / (1024*1024):.2f} MB para Supabase Storage...")
                
                # SOLUÇÃO: Upload em streaming com callback de progresso
                # O SDK do Supabase vai fazer streaming automaticamente sem carregar tudo na memória
                with open(file_path, 'rb') as f:
                    # Usar wrapper para monitorar progresso durante o upload se callback fornecido
                    if progress_callback:
                        file_wrapper = ProgressFileWrapper(f, file_size, progress_callback)
                        # Type ignore pois wrapper implementa interface file-like necessária
                        response = self.client.storage.from_(self.bucket_name).upload(
                            file_name,
                            file_wrapper,  # type: ignore - Wrapper implementa read/seek/tell
                            file_options={"content-type": content_type}
                        )
                    else:
                        # Sem callback, usar file handle direto
                        response = self.client.storage.from_(self.bucket_name).upload(
                            file_name,
                            f,  # File handle - SDK faz streaming automaticamente
                            file_options={"content-type": content_type}
                        )
                
                if progress_callback:
                    progress_callback(f"Upload concluído: {file_name} ({file_size / (1024*1024):.2f} MB)")
                
                return file_name
                
            except Exception as e:
                error_msg = str(e)
                
                # Se for a última tentativa, lançar erro
                if attempt == max_retries - 1:
                    raise Exception(f"Erro ao fazer upload para Supabase Storage após {max_retries} tentativas: {error_msg}")
                
                # Caso contrário, aguardar e tentar novamente
                if progress_callback:
                    wait_time = retry_delay * (attempt + 1)  # Backoff exponencial
                    progress_callback(f"Erro temporário no upload: {error_msg}. Aguardando {wait_time}s antes de tentar novamente...")
                
                time.sleep(retry_delay * (attempt + 1))
                
                # Se o arquivo já existe de uma tentativa anterior, tentar remover
                try:
                    self.client.storage.from_(self.bucket_name).remove([file_name])
                except:
                    pass  # Ignorar erro se arquivo não existir
        
        # Este ponto nunca deve ser alcançado (loop sempre retorna ou lança exceção)
        # mas é necessário para satisfazer o type checker
        raise Exception("Falha inesperada no upload - todas as tentativas foram esgotadas")

    def get_file_url(self, file_name: str) -> str:
        """
        Obtém a URL pública de um arquivo (válida por tempo limitado)
        
        Args:
            file_name: Nome do arquivo no storage
            
        Returns:
            str: URL de download do arquivo
        """
        try:
            response = self.client.storage.from_(self.bucket_name).create_signed_url(
                file_name,
                expires_in=3600
            )
            return response.get('signedURL', '')
        except Exception as e:
            print(f"Erro ao obter URL do arquivo {file_name}: {e}")
            return ""

    def delete_file(self, file_name: str):
        """
        Deleta um arquivo do Supabase Storage
        
        Args:
            file_name: Nome do arquivo no storage
        """
        try:
            self.client.storage.from_(self.bucket_name).remove([file_name])
        except Exception as e:
            print(f"Erro ao deletar arquivo {file_name}: {e}")

    def list_files(self, max_results: int = 100) -> list:
        """
        Lista arquivos no bucket
        
        Args:
            max_results: Número máximo de resultados
            
        Returns:
            list: Lista de arquivos no storage
        """
        try:
            response = self.client.storage.from_(self.bucket_name).list()
            return response[:max_results] if response else []
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
            return []

    def download_file(self, file_name: str, local_path: str):
        """
        Baixa um arquivo do Supabase Storage
        
        Args:
            file_name: Nome do arquivo no storage
            local_path: Caminho local onde salvar o arquivo
        """
        try:
            response = self.client.storage.from_(self.bucket_name).download(file_name)
            
            with open(local_path, 'wb') as f:
                f.write(response)
        except Exception as e:
            raise Exception(f"Erro ao baixar arquivo {file_name}: {str(e)}")
