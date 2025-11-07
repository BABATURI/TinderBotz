import smtplib
from email.message import EmailMessage
from typing import Any


class EmailHelper:
    @staticmethod
    def send_mail_match_found(to: str) -> None:
        match_msg: str = "Congratulations you've been matched with someone. Please check your profile for more details."

        msg: EmailMessage = EmailMessage()
        msg.set_content(match_msg)

        msg['Subject'] = 'NEW TINDER MATCH'
        msg['From'] = "github.tinderbotz@gmail.com"
        msg['To'] = to

        server: Any = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("github.tinderbotz@gmail.com", "kuzdys-1zafri-Pebzob")
        server.send_message(msg)
        server.quit()
