# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from mailjet_rest import Client
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware



# Load environment variables from .env file
dotenv_path = os.getenv('DOTENV_PATH', '.env')
load_dotenv(dotenv_path)

# Read Mailjet credentials and emails from environment\NPJ_APIKEY_PUBLIC = os.getenv('MJ_APIKEY_PUBLIC')
MJ_APIKEY_PUBLIC = os.getenv('MJ_APIKEY_PUBLIC')
MJ_APIKEY_PRIVATE = os.getenv('MJ_APIKEY_PRIVATE')
MJ_SENDER_EMAIL = os.getenv('MJ_SENDER_EMAIL')
MJ_SENDER_NAME = os.getenv('MJ_SENDER_NAME', 'Transfer99 Booking')

CLIENT_URL = os.getenv('CLIENT_URL', 'http://localhost:8000')

if not all([MJ_APIKEY_PUBLIC, MJ_APIKEY_PRIVATE, MJ_SENDER_EMAIL]):
    raise EnvironmentError("Missing one or more Mailjet credentials or email addresses in environment variables.")

# Initialize Mailjet client
mailjet_client = Client(auth=(MJ_APIKEY_PUBLIC, MJ_APIKEY_PRIVATE), version='v3.1')

app = FastAPI(title="Transfer99 Booking API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    from_location: str
    to_location: str
    message: str = None
    price: str

@app.post("/api/send-booking")
async def send_booking(request: BookingRequest):
    payload = {
        'Messages': [
            {
                'From': {
                    'Email': MJ_SENDER_EMAIL,
                    'Name': MJ_SENDER_NAME
                },
                'To': [
                    {
                        'Email': request.email,
                        'Name': request.name
                    }
                ],
                'Subject': 'New Transfer Booking Request',
                'TextPart': (
                    f"New booking request from: {request.name}\n"
                    f"Email: {request.email}\n"
                    f"Phone: {request.phone}\n"
                    f"From: {request.from_location}\n"
                    f"To: {request.to_location}\n"
                    f"Price: {request.price}\n"
                    f"Message: {request.message or ''}"
                ),
                'HTMLPart': (
                    f"<h3>New Transfer Booking Request</h3>"
                    f"<p><strong>Customer:</strong> {request.name}</p>"
                    f"<p><strong>Email:</strong> {request.email}</p>"
                    f"<p><strong>Phone:</strong> {request.phone}</p>"
                    f"<p><strong>From:</strong> {request.from_location}</p>"
                    f"<p><strong>To:</strong> {request.to_location}</p>"
                    f"<p><strong>Estimated Price:</strong> {request.price}</p>"
                    f"<p><strong>Message:</strong> {request.message or ''}</p>"
                )
            }
        ]
    }

    # Send email via Mailjet
    result = mailjet_client.send.create(data=payload)
    if result.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send email via Mailjet")

    return {"ok": True, "message": "Booking request sent successfully."}

# To run: uvicorn app:app --host 0.0.0.0 --port 8000
