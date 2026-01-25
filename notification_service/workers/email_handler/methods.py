"""
Email sending methods using aiosmtplib
"""
import asyncio
from typing import Optional
from dataclasses import dataclass

import aiosmtplib
from email.message import EmailMessage
from datetime import datetime


@dataclass
class EmailConfig:
    """Конфигурация SMTP"""
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_email: Optional[str] = None
    use_tls: bool = True

    def __post_init__(self):
        if self.from_email is None:
            self.from_email = self.username


async def send_email(
    config: EmailConfig,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> dict:
    """
    Отправка email через SMTP с aiosmtplib

    Args:
        config: Конфигурация SMTP
        to_email: Email получателя
        subject: Тема письма
        html_body: HTML содержимое
        text_body: Текстовое содержимое (опционально)

    Returns:
        dict с результатом отправки
    """
    message = EmailMessage()
    message["From"] = config.from_email
    message["To"] = to_email
    message["Subject"] = subject
    message["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Устанавливаем содержимое
    if text_body:
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")
    else:
        message.set_content(html_body, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=config.smtp_host,
            port=config.smtp_port,
            start_tls=config.use_tls,
            username=config.username,
            password=config.password,
            timeout=30,
        )

        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "message_id": message.get("Message-ID"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except aiosmtplib.SMTPException as e:
        return {
            "status": "failed",
            "to": to_email,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "failed",
            "to": to_email,
            "error": str(e),
            "error_type": "UnexpectedError",
            "timestamp": datetime.utcnow().isoformat(),
        }
#
#
# # ============================================================================
# # TEST RUNNER
# # ============================================================================
# async def test_email():
#     """
#     Тестовая функция для проверки отправки
#
#     Инструкция по настройке Gmail App Password:
#     1. Перейти: https://myaccount.google.com/apppasswords
#     2. Создать App Password для "Mail"
#     3. Использовать сгенерированный пароль (не обычный пароль!)
#
#     Для Yandex:
#     - smtp.yandex.ru:587
#     - Использовать обычный пароль (или app password если включена 2FA)
#
#     Для Mail.ru:
#     - smtp.mail.ru:587
#     """
#
#     # === ЗАПОЛНИТЕ ВАШИ ДАННЫЕ ===
#     config = EmailConfig(
#         smtp_host="smtp.gmail.com",        # или smtp.yandex.ru, smtp.mail.ru
#         smtp_port=587,
#         username="your-email@gmail.com",    # ЗАМЕНИТЬ
#         password="your-app-password",       # ЗАМЕНИТЬ (для Gmail - App Password!)
#         from_email="your-email@gmail.com",  # ЗАМЕНИТЬ (можно не указывать, будет = username)
#     )
#
#     # === Тестовое письмо ===
#     html_content = f"""
#     <html>
#         <body style="font-family: Arial, sans-serif; padding: 20px;">
#             <h1 style="color: #333;">🚀 Test Email</h1>
#             <p>Hello from Notification Service!</p>
#             <p>This is a test email sent via aiosmtplib.</p>
#             <hr>
#             <p style="color: #666; font-size: 12px;">
#                 Sent at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#             </p>
#         </body>
#     </html>
#     """
#
#     text_content = "Hello from Notification Service! This is a plain text version."
#
#     # === Отправка ===
#     result = await send_email(
#         config=config,
#         to_email="recipient@example.com",  # ЗАМЕНИТЬ на ваш email для теста
#         subject="Test Email from Notification Service",
#         html_body=html_content,
#         text_body=text_content,
#     )
#
#     print("=" * 60)
#     print("Email Sending Result:")
#     print("=" * 60)
#     for key, value in result.items():
#         print(f"{key:15}: {value}")
#     print("=" * 60)
#
#     return result


if __name__ == "__main__":
    # Запуск: python -m notification_service.workers.email_handler.methods
    # asyncio.run(test_email())
    import asyncio
    from email.message import EmailMessage

    import aiosmtplib

    message = EmailMessage()
    message["From"] = "root@localhost"
    message["To"] = "farakhov0ruslan@gmail.com"
    message["Subject"] = "Hello World!"
    message.set_content("Sent via aiosmtplib")

    asyncio.run(aiosmtplib.send(message, hostname="127.0.0.1", port=25))