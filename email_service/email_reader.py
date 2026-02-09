from email_service.gmail_reader import GmailReader
from email_service.outlook_reader import OutlookReader

class EmailReader:
    def __init__(self, gmail_email=None, gmail_password=None):
        self.gmail = None
        if gmail_email and gmail_password:
            self.gmail = GmailReader(gmail_email, gmail_password)

        self.outlook = OutlookReader()

    def read_latest_email(self):
        try:
            print("📥 Trying Gmail...")
            return self.gmail.read_latest_email()
        except Exception:
            print("📥 Gmail failed, switching to Outlook...")
            return self.outlook.read_latest_email()
