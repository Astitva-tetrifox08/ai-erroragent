import msal
import requests
import os

class OutlookReader:
    def __init__(self):
        self.client_id = os.getenv("03a5162f-5061-4585-aef9-8af3d8d122c1")
        self.authority = "https://login.microsoftonline.com/common"
        self.scopes = ["Mail.Read"]

    def read_latest_email(self):
        app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority
        )

        flow = app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise Exception("Device flow creation failed")

        print("\n🔐 LOGIN REQUIRED")
        print(flow["message"])  # Microsoft login message

        result = app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise Exception("Failed to obtain access token")

        headers = {
            "Authorization": f"Bearer {result['access_token']}"
        }

        url = "https://graph.microsoft.com/v1.0/me/messages?$top=1"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        email = response.json()["value"][0]
        return email["body"]["content"]
