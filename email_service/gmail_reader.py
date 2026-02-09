from imapclient import IMAPClient
import pyzmail
from bs4 import BeautifulSoup
from email_service.interface import EmailReader


class GmailReader(EmailReader):

    def __init__(self, email, app_password):
        self.email = email
        self.app_password = app_password

    def _get_latest_message(self):
        server = IMAPClient("imap.gmail.com")
        server.login(self.email, self.app_password)
        server.select_folder("INBOX")

        messages = server.search(["UNSEEN"])
        if not messages:
            return None

        latest_id = messages[-1]
        raw_message = server.fetch(
            [latest_id], ["RFC822"]
        )[latest_id][b"RFC822"]

        return pyzmail.PyzMessage.factory(raw_message)

    
    def read_latest_email(self) -> str:
        message = self._get_latest_message()
        if not message:
            return "No unread emails"

        if message.text_part:
            return message.text_part.get_payload().decode(
                message.text_part.charset
            )

        if message.html_part:
            html = message.html_part.get_payload().decode(
                message.html_part.charset
            )
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text(separator="\n").strip()

        return "No readable content"

    def read_latest_subject(self) -> str:
        message = self._get_latest_message()
        if not message:
            return "No subject"

        subject, charset = message.get_subject()
        return subject
