from fastapi import FastAPI, Request
import json

app = FastAPI()

@app.post("/azure-alert")
async def azure_alert(request: Request):
    payload = await request.json()

    print("\n🚨 AZURE ALERT RECEIVED 🚨")
    print(json.dumps(payload, indent=2))

    return {"status": "received"}
