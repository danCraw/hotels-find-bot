import os
from email.message import EmailMessage
import smtplib
from lib import notisend

SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

NOTISEND_PROJECT = 'hotels-find-bot'  # Имя проекта
NOTISEND_API_KEY = '590aaaac792d2'  # API-ключ


async def send_email_code(email: str, code: str):
    msg = EmailMessage()
    msg.set_content(f"Ваш код подтверждения: {code}")
    msg['Subject'] = 'Код подтверждения бронирования'
    msg['From'] = SMTP_USER
    msg['To'] = email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


async def send_sms_code(phone: str, code: str):
    sms = notisend.SMS(NOTISEND_PROJECT, NOTISEND_API_KEY)
    message = sms.sendSMS(
        recipients=phone,
        message=f'Ваш код подтверждения: {code}',
    )
    return message.sid