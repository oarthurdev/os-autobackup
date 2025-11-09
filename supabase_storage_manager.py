import os
from supabase import create_client, Client
from config import Config

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

    def upload_file(self, file_path: str, file_name: str = None) -> str:
        """
        Faz upload de um arquivo para o Supabase Storage
        
        Args:
            file_path: Caminho do arquivo local
            file_name: Nome do arquivo no storage (se None, usa o nome original)
            
        Returns:
            str: ID/caminho do arquivo no storage
        """
        if not file_name:
            file_name = os.path.basename(file_path)

        # Determine content type based on file extension
        if file_name.endswith('.tar.gz') or file_name.endswith('.tgz'):
            content_type = "application/gzip"
        elif file_name.endswith('.zip'):
            content_type = "application/zip"
        else:
            content_type = "application/octet-stream"

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                
            response = self.client.storage.from_(self.bucket_name).upload(
                file_name,
                file_data,
                file_options={"content-type": content_type}
            )
            
            return file_name
        except Exception as e:
            raise Exception(f"Erro ao fazer upload para Supabase Storage: {str(e)}")

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
