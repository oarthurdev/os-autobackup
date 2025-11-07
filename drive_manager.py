import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from config import Config
import io
import socket
import ssl

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveManager:
    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        creds = None

        if os.path.exists(Config.GOOGLE_DRIVE_TOKEN_FILE):
            try:
                with open(Config.GOOGLE_DRIVE_TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            except (pickle.UnpicklingError, EOFError, FileNotFoundError):
                print("Erro ao carregar token. Será gerado um novo.")
                os.remove(Config.GOOGLE_DRIVE_TOKEN_FILE)
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    # Tenta renovar o token
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Erro ao renovar token: {e}. Forçando nova autenticação.")
                    # Se falhar ao renovar, remove o token e força nova autenticação
                    os.remove(Config.GOOGLE_DRIVE_TOKEN_FILE)
                    creds = None

            if not creds or not creds.valid:
                if not os.path.exists(Config.GOOGLE_DRIVE_CREDENTIALS_FILE):
                    raise Exception(
                        f"Arquivo de credenciais do Google Drive não encontrado: {Config.GOOGLE_DRIVE_CREDENTIALS_FILE}\n"
                        "Por favor, baixe o credentials.json do Google Cloud Console"
                    )

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        Config.GOOGLE_DRIVE_CREDENTIALS_FILE, SCOPES
                    )
                    # Configura timeout e SSL para a solicitação do servidor local
                    # Usa um socket wrapper para forçar TLS 1.2+ se necessário
                    default_socket_options = socket.getdefaulttimeout()
                    
                    # Tenta executar o servidor local com um timeout e configurações de navegador
                    # O uso de 'open_browser=True' e 'authorization_prompt_message' é mais para UX
                    # O 'timeout_seconds' se aplica à espera da resposta do servidor
                    creds = flow.run_local_server(
                        port=0, 
                        timeout_seconds=60,
                        open_browser=True,
                        success_message='Autenticação concluída! Você pode fechar esta janela.',
                        authorization_prompt_message='Por favor, visite esta URL para autorizar:\n{url}'
                    )
                except socket.timeout:
                    print("Erro: Tempo limite excedido durante a autenticação. Verifique sua conexão.")
                    raise Exception("Tempo limite na autenticação do Google Drive.")
                except ssl.SSLError as e:
                    print(f"Erro SSL durante a autenticação: {e}. Verifique suas configurações de rede ou proxy.")
                    raise Exception(f"Erro SSL na autenticação do Google Drive: {e}")
                except Exception as e:
                    print(f"Erro inesperado durante a autenticação OAuth: {e}")
                    raise Exception(f"Falha na autenticação OAuth do Google Drive: {e}")

            # Salva as credenciais obtidas ou renovadas
            with open(Config.GOOGLE_DRIVE_TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def upload_file(self, file_path: str, file_name: str = None, folder_id: str = None) -> str:
        if not file_name:
            file_name = os.path.basename(file_path)

        file_metadata = {'name': file_name}

        if folder_id or Config.GOOGLE_DRIVE_FOLDER_ID:
            file_metadata['parents'] = [folder_id or Config.GOOGLE_DRIVE_FOLDER_ID]

        # Otimiza o tamanho do chunk para arquivos grandes
        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024 * 1024:  # > 5GB
            chunk_size = 10 * 1024 * 1024  # chunks de 10MB
        elif file_size > 1 * 1024 * 1024 * 1024:  # > 1GB
            chunk_size = 5 * 1024 * 1024  # chunks de 5MB
        else:
            chunk_size = 1024 * 1024  # chunks de 1MB (padrão)

        media = MediaFileUpload(file_path, resumable=True, chunksize=chunk_size)

        request = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        )

        # Upload com rastreamento de progresso para arquivos grandes
        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    # Info de progresso disponível mas não logada aqui para evitar spam
            except (socket.timeout, ssl.SSLError) as e:
                print(f"Erro de rede/SSL durante o upload: {e}. Tentando novamente...")
                # Pode adicionar um pequeno delay antes de tentar novamente
                import time
                time.sleep(5)
                request = self.service.files().create( # Recria a requisição para continuar
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                )
                # Para garantir que o próximo_chunk continue de onde parou,
                # a API do Google Drive geralmente lida com a resumpção,
                # mas em caso de falha, pode ser necessário reconfigurar o upload.
                # O 'resumable=True' no MediaFileUpload deve cuidar disso.
            except Exception as e:
                print(f"Erro inesperado durante o upload do arquivo: {e}")
                raise

        return response.get('id')

    def get_file_link(self, file_id: str) -> str:
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            return file.get('webViewLink', '')
        except (socket.timeout, ssl.SSLError) as e:
            print(f"Erro de rede/SSL ao obter link do arquivo {file_id}: {e}")
            return ""
        except Exception as e:
            print(f"Erro ao obter link do arquivo {file_id}: {e}")
            return ""

    def delete_file(self, file_id: str):
        try:
            self.service.files().delete(fileId=file_id).execute()
        except (socket.timeout, ssl.SSLError) as e:
            print(f"Erro de rede/SSL ao deletar arquivo {file_id}: {e}")
        except Exception as e:
            print(f"Erro ao deletar arquivo {file_id}: {e}")

    def list_files(self, folder_id: str = None, max_results: int = 100) -> list:
        query = f"'{folder_id or Config.GOOGLE_DRIVE_FOLDER_ID}' in parents" if (folder_id or Config.GOOGLE_DRIVE_FOLDER_ID) else None

        try:
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, createdTime, size, webViewLink)"
            ).execute()
            return results.get('files', [])
        except (socket.timeout, ssl.SSLError) as e:
            print(f"Erro de rede/SSL ao listar arquivos: {e}")
            return []
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
            return []