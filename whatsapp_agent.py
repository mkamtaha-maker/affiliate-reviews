import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

# إعدادات Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# إعدادات Green-API
ID_INSTANCE = "710722719616"
API_TOKEN = "e226b61e324d416f89d015cb56bc835c287bbf173cf0409c83"
API_URL = "https://7107.api.greenapi.com"

BANK_DETAILS = """
*Payment Details (Revolut UK)*:
- Bank: Revolut UK
- Account Name: Kamal Mohammed Taha
- Sort Code: 04-29-09
- Account Number: 16721489
- Fixed Price: £30.00 (Paid in full upfront to get started)
"""

SYSTEM_PROMPT = f"""
You are Kam Tyler, Growth & Web Solutions Consultant at 'Gear Radar Digital Solutions' in the UK.
You are chatting with a business owner on WhatsApp who received your outreach email or found your contact.

Key Business Rules:
1. Core Offer: Quick-Launch One-Page Business Website, Mobile Integration, and Local UK Google Setup.
2. Pricing: Fixed £30 total (paid in full upfront). No recurring monthly platform fees.
3. Tone: Professional, British English, concise, conversational, and direct.
4. If the client agrees, asks how to pay, or asks how to get started, provide the payment details:
{BANK_DETAILS}
5. Keep WhatsApp replies brief (under 2-3 sentences).
"""

def generate_ai_reply(incoming_msg: str) -> str:
    if not client:
        return (
            "Hi! Thanks for contacting Gear Radar Digital Solutions. "
            "Our quick-launch business web setup is a fixed £30 one-off fee. "
            "Would you like to get started?"
        )
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"{SYSTEM_PROMPT}\n\nClient WhatsApp Message: \"{incoming_msg}\"\n\nKam Tyler Reply:"
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return "Hi! Thanks for getting in touch. Our quick-launch local web package is £30 total. Let me know if you would like to proceed!"

def send_whatsapp_message(chat_id: str, message_text: str):
    """إرسال الرد عبر Green-API"""
    url = f"{API_URL}/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": message_text
    }
    headers = {'Content-Type': 'application/json'}
    try:
        res = requests.post(url, json=payload, headers=headers)
        print(f"🚀 [Message Sent via Green-API] Status: {res.status_code}")
    except Exception as e:
        print(f"❌ Error sending via Green-API: {e}")

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "no data"}), 400

    type_webhook = data.get("typeWebhook")

    if type_webhook == "incomingMessageReceived":
        msg_data = data.get("messageData", {})
        type_msg = msg_data.get("typeMessage")
        sender_data = data.get("senderData", {})
        chat_id = sender_data.get("chatId")

        # تجاهل المجموعات
        if "@g.us" in chat_id:
            return jsonify({"status": "group message ignored"}), 200

        text_message = ""
        if type_msg == "textMessage":
            text_message = msg_data.get("textMessageData", {}).get("textMessage", "")
        elif type_msg == "extendedTextMessage":
            text_message = msg_data.get("extendedTextMessageData", {}).get("text", "")

        if text_message:
            print(f"\n💬 [Incoming Message] From: {chat_id} | Message: {text_message}")
            ai_reply = generate_ai_reply(text_message)
            print(f"🤖 [Kam Tyler Replying]: {ai_reply}")
            send_whatsapp_message(chat_id, ai_reply)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 [Kam Tyler] Green-API WhatsApp Autonomous Agent Running on Port 5000")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)