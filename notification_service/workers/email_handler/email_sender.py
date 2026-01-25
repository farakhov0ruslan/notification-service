# email_service.py
import aiosmtplib
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader
import asyncio
from typing import List


class AsyncEmailService:
    def __init__(self, smtp_host: str, smtp_port: int,
                 username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.env = Environment(loader=FileSystemLoader('templates'))

    async def send_email(self, to: str, subject: str,
                         template_name: str, context: dict):
        template = self.env.get_template(template_name)
        html_content = template.render(**context)

        message = EmailMessage()
        message["From"] = self.username
        message["To"] = to
        message["Subject"] = subject
        message.set_content(html_content, subtype='html')

        await aiosmtplib.send(
            message,
            hostname=self.smtp_host,
            port=self.smtp_port,
            start_tls=True,
            username=self.username,
            password=self.password
        )
