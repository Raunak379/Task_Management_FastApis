
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

#class EmailSchema(BaseModel):
#    email: List[EmailStr]

conf = ConnectionConfig(
    MAIL_USERNAME = "sherraunaksingh@gmail.com",
    MAIL_PASSWORD = "ftkl ewtt mpsw ncry",          ###that is App password not mail password
    MAIL_FROM = "sherraunaksingh@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="Raunak FastApi",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


async def send_email(email: str):
    html = """<p>Hi, Thanks for registraction. our team will connect you soon !</p> """

    message = MessageSchema(
        subject="Registration confirmation",
        recipients=[email],
        body=html,
        subtype=MessageType.html)

    fm = FastMail(conf)
    await fm.send_message(message)
    print({"messgae": "email has been sent"})