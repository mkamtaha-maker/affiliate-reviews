import os
import time
import email
import imaplib
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from google import genai

load_dotenv()

# إعدادات البريد
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "gearradarservices@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
WHATSAPP_NUMBER = "447442309417"

# إعدادات Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

BANK_DETAILS = """
Payment Details (Revolut UK):
- Bank: Revolut UK
- Account Name: Kamal Mohammed Taha
- Sort Code: 04-29-09
- Account Number: 16721489
- Fixed Package Fee: £30.00 (One-Off Upfront)
"""

def get_email_signature() -> str:
    return f"""Best regards,

Kam Tyler
Growth & Web Solutions Consultant
Gear Radar Digital Solutions
Email: {EMAIL_SENDER}
WhatsApp: +44 7442 309417
Bolton / Greater Manchester, UK

---
Opt-out: If you prefer not to receive commercial suggestions from us in the future, please reply with 'Unsubscribe' and we will remove your business from our outreach records."""

def decode_mime_words(s):
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    header_text = []
    for frag, encoding in decoded_fragments:
        if isinstance(frag, bytes):
            try:
                header_text.append(frag.decode(encoding or "utf-8", errors="ignore"))
            except Exception:
                header_text.append(frag.decode("latin1", errors="ignore"))
        else:
            header_text.append(str(frag))
    return "".join(header_text)

def generate_email_reply(sender_email: str, subject: str, body: str) -> str:
    prompt = f"""
You are Kam Tyler, Growth & Web Solutions Consultant at Gear Radar Digital Solutions in the UK.
You received an incoming email reply to your business outreach.

Rules:
1. Core Offer: £30 One-Off fast web presence setup & Google local setup.
2. If they are interested or ask for details, explain the £30 package and invite them to WhatsApp: https://wa.me/{WHATSAPP_NUMBER}
3. If they ask how to pay, provide bank details:
{BANK_DETAILS}
4. If they say "unsubscribe", "remove", or "stop", confirm politely that they have been removed.
5. Keep the reply polite, professional (British English), and concise. Do NOT include the signature (it will be added automatically).

Incoming Subject: {subject}
Incoming Body: {body}

Your Email Reply Body:
"""
    if not client:
        return f"Hi,\n\nThanks for reaching out! Our quick-launch local web setup is a fixed £30 one-off fee. You can reach me directly on WhatsApp at https://wa.me/{WHATSAPP_NUMBER} to get started.\n"
    
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return f"Hi,\n\nThanks for your reply! Our complete setup is £30 one-off. Message me on WhatsApp at https://wa.me/{WHATSAPP_NUMBER} to proceed.\n"

def send_reply(to_email: str, subject: str, reply_body: str):
    full_body = f"{reply_body}\n\n{get_email_signature()}"
    reply_subj = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    
    msg = MIMEMultipart()
    msg["From"] = f"Kam Tyler <{EMAIL_SENDER}>"
    msg["To"] = to_email
    msg["Subject"] = reply_subj
    msg.attach(MIMEText(full_body, "plain", "utf-8"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"📧 [Email Reply Dispatched] Sent to: {to_email}")
    except Exception as e:
        print(f"❌ [SMTP Send Error]: {e}")

def check_inbox_and_reply():
    if not EMAIL_PASSWORD:
        return

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_SENDER, EMAIL_PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            mail.logout()
            return

        for num in messages[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_header = decode_mime_words(msg.get("From"))
            subject = decode_mime_words(msg.get("Subject"))

            # استخراج عنوان البريد الحقيقي
            sender_email = from_header
            if "<" in from_header and ">" in from_header:
                sender_email = from_header.split("<")[1].split(">")[0]

            # تصفية إيميلات النظام، إشعارات الارتداد، والرسائل التلقائية
            ignored_senders = [
                EMAIL_SENDER.lower(),
                "mailer-daemon",
                "postmaster",
                "noreply",
                "no-reply",
                "googlemail.com",
                "notifications@"
            ]
            if any(ignored in sender_email.lower() for ignored in ignored_senders):
                continue

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            print(f"\n📩 [New Inbound Email] From: {sender_email} | Subject: {subject}")
            reply_content = generate_email_reply(sender_email, subject, body)
            send_reply(sender_email, subject, reply_content)

        mail.logout()
    except Exception as e:
        print(f"⚠️ [Inbox Check Warning]: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📬 [Inbox Monitor Agent] Listening for incoming business replies...")
    print("="*60 + "\n")
    while True:
        check_inbox_and_reply()
        time.sleep(30)