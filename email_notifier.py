
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict
import logging
from database import Database

class EmailNotifier:
    def __init__(self):
        self.db = Database()
        self.logger = logging.getLogger('EmailNotifier')
        
    def get_email_config(self) -> Optional[Dict]:
        """Obtém a configuração de email do banco de dados"""
        config = self.db.get_email_config()
        return config if config and config.get('enabled') else None
    
    def send_backup_notification(self, backup_id: int, status: str, error_message: str = None):
        """Envia notificação sobre conclusão de backup"""
        config = self.get_email_config()
        if not config:
            return
        
        try:
            # Buscar informações do backup
            backup = self.db.get_backup_by_id(backup_id)
            if not backup:
                return
            
            # Preparar email
            subject = f"{'✅ Backup Concluído' if status == 'SUCCESS' else '❌ Backup Falhou'} - ID #{backup_id}"
            
            # Criar corpo do email em HTML
            html_body = self._create_backup_email_html(backup, status, error_message)
            
            # Enviar email
            self._send_email(
                config=config,
                subject=subject,
                html_body=html_body
            )
            
            self.logger.info(f"Email de notificação enviado para backup #{backup_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email de notificação: {str(e)}")
    
    def send_schedule_notification(self, schedule_id: int, backup_id: int, success: bool):
        """Envia notificação sobre execução de agendamento"""
        config = self.get_email_config()
        if not config or not config.get('notify_schedules'):
            return
        
        try:
            schedule = self.db.get_schedule(schedule_id)
            backup = self.db.get_backup_by_id(backup_id)
            
            if not schedule or not backup:
                return
            
            subject = f"{'✅ Agendamento Executado' if success else '❌ Agendamento Falhou'} - {schedule.get('host_name', 'N/A')}"
            html_body = self._create_schedule_email_html(schedule, backup, success)
            
            self._send_email(
                config=config,
                subject=subject,
                html_body=html_body
            )
            
            self.logger.info(f"Email de agendamento enviado para schedule #{schedule_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email de agendamento: {str(e)}")
    
    def send_test_email(self, config: Dict) -> bool:
        """Envia email de teste para validar configurações"""
        try:
            subject = "🧪 Teste de Notificação - OS Backup"
            html_body = """
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #0066ff; margin-bottom: 20px;">✅ Configuração de Email Testada com Sucesso!</h2>
                        <p style="color: #333; line-height: 1.6;">
                            Parabéns! Suas configurações de email estão funcionando corretamente.
                        </p>
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Este é um email de teste do sistema OS Backup.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            self._send_email(config, subject, html_body)
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email de teste: {str(e)}")
            raise
    
    def _send_email(self, config: Dict, subject: str, html_body: str):
        """Envia um email usando as configurações fornecidas"""
        msg = MIMEMultipart('alternative')
        msg['From'] = config['smtp_from']
        msg['To'] = config['notify_email']
        msg['Subject'] = subject
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Conectar ao servidor SMTP
        if config.get('smtp_use_tls'):
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        
        # Autenticar
        if config.get('smtp_username'):
            server.login(config['smtp_username'], config['smtp_password'])
        
        # Enviar email
        server.send_message(msg)
        server.quit()
    
    def _create_backup_email_html(self, backup: Dict, status: str, error_message: str = None) -> str:
        """Cria HTML formatado para email de backup"""
        success = status == 'SUCCESS'
        color = '#00c853' if success else '#ff3b30'
        icon = '✅' if success else '❌'
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: {color}; margin-bottom: 20px;">{icon} Backup {'Concluído' if success else 'Falhou'}</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h3 style="margin-top: 0; color: #333;">Detalhes do Backup</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #666; width: 40%;">ID do Backup:</td>
                                <td style="padding: 8px 0; color: #333; font-weight: bold;">#{backup.get('id')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;">Data/Hora:</td>
                                <td style="padding: 8px 0; color: #333;">{datetime.fromisoformat(backup.get('timestamp', '')).strftime('%d/%m/%Y %H:%M:%S')}</td>
                            </tr>
                            {'<tr><td style="padding: 8px 0; color: #666;">Arquivo:</td><td style="padding: 8px 0; color: #333;">' + backup.get('file_name', 'N/A') + '</td></tr>' if backup.get('file_name') else ''}
                            {'<tr><td style="padding: 8px 0; color: #666;">Tamanho:</td><td style="padding: 8px 0; color: #333;">' + self._format_bytes(backup.get('file_size', 0)) + '</td></tr>' if backup.get('file_size') else ''}
                            {'<tr><td style="padding: 8px 0; color: #666;">Duração:</td><td style="padding: 8px 0; color: #333;">' + f"{backup.get('duration_seconds', 0):.2f}s" + '</td></tr>' if backup.get('duration_seconds') else ''}
                        </table>
                    </div>
                    
                    {f'<div style="background-color: #fff3cd; border-left: 4px solid #ff9500; padding: 15px; border-radius: 4px;"><strong style="color: #856404;">Erro:</strong><br><span style="color: #856404;">{error_message}</span></div>' if error_message else ''}
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px; border-top: 1px solid #e0e0e0; padding-top: 20px;">
                        Esta é uma notificação automática do sistema OS Backup.
                    </p>
                </div>
            </body>
        </html>
        """
        return html
    
    def _create_schedule_email_html(self, schedule: Dict, backup: Dict, success: bool) -> str:
        """Cria HTML formatado para email de agendamento"""
        color = '#00c853' if success else '#ff3b30'
        icon = '✅' if success else '❌'
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: {color}; margin-bottom: 20px;">{icon} Agendamento {'Executado' if success else 'Falhou'}</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h3 style="margin-top: 0; color: #333;">Informações do Agendamento</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #666; width: 40%;">Servidor:</td>
                                <td style="padding: 8px 0; color: #333; font-weight: bold;">{schedule.get('host_name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;">Tipo:</td>
                                <td style="padding: 8px 0; color: #333;">{schedule.get('schedule_type', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;">Backup ID:</td>
                                <td style="padding: 8px 0; color: #333;">#{backup.get('id')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;">Executado em:</td>
                                <td style="padding: 8px 0; color: #333;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px; border-top: 1px solid #e0e0e0; padding-top: 20px;">
                        Esta é uma notificação automática do sistema OS Backup.
                    </p>
                </div>
            </body>
        </html>
        """
        return html
    
    def _format_bytes(self, bytes_size: int) -> str:
        """Formata bytes para formato legível"""
        if bytes_size < 0:
            return "0 B"
        size_float = float(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_float < 1024.0:
                return f"{size_float:.2f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.2f} PB"
