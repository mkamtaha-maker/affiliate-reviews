import email
from email.header import decode_header
import imaplib
import json
import os
import re
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from agency_outreach import (
    ACCOUNT_NAME,
    ACCOUNT_NUMBER,
    BANK_NAME,
    GMAIL_APP_PASSWORD,
    SENDER_EMAIL,
    SORT_CODE,
    get_email_signature,
    send_onboarding_invoice,
)

load_dotenv()

NOTIFICATION_EMAIL = "mkam.taha@gmail.com"  # بريدك الشخصي المصرح له بإعطاء الأوامر
PROCESSED_THREADS_FILE = "processed_replies.json"
CHECK_INTERVAL_SECONDS = 60  # فحص كل دقيقة لالتقاط أوامرك سريعاً


# ==========================================
# 1. State Management
# ==========================================
def get_processed_ids() -> set:
    if os.path.exists(PROCESSED_THREADS_FILE):
        try:
            with open(PROCESSED_THREADS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_processed_id(msg_id: str):
    processed = get_processed_ids()
    processed.add(msg_id)
    with open(PROCESSED_THREADS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, indent=2)


# ==========================================
# 2. Automated Web Project Kickoff Generator
# ==========================================
def auto_build_project_assets(client_name: str):
    """Creates initial website build folder and high-converting staging template."""
    clean_folder_name = re.sub(r'[^a-zA-Z0-9_-]', '_', client_name).lower()
    project_dir = os.path.join("client_projects", clean_folder_name)
    os.makedirs(project_dir, exist_ok=True)

    landing_page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{client_name} | High Performance Services</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 font-sans">
    <header class="border-b border-slate-800 py-6 px-8 flex justify-between items-center max-w-6xl mx-auto">
        <h1 class="text-2xl font-bold tracking-tight text-blue-500">{client_name}</h1>
        <a href="#book" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg font-medium shadow-md transition">Book Service</a>
    </header>
    <main class="max-w-4xl mx-auto py-20 px-6 text-center">
        <span class="bg-blue-900 text-blue-300 text-xs uppercase px-3 py-1 rounded-full font-semibold">Fast Turnaround & Local UK Experts</span>
        <h2 class="text-4xl sm:text-5xl font-extrabold mt-6 leading-tight">Premium Servicing & Booking for <span class="text-blue-500">{client_name}</span></h2>
        <p class="text-slate-400 mt-4 text-lg">Optimised for seamless mobile browsing, instant booking requests, and fast response times.</p>
        <div id="book" class="mt-12 bg-slate-800 p-8 rounded-xl border border-slate-700 max-w-lg mx-auto text-left shadow-xl">
            <h3 class="text-xl font-bold mb-4">Request a Quick Booking / Enquiry</h3>
            <form onsubmit="event.preventDefault(); alert('Enquiry received!');" class="space-y-4">
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Your Name</label>
                    <input type="text" class="w-full bg-slate-900 border border-slate-700 rounded p-3 text-white" placeholder="John Doe" required>
                </div>
                <div>
                    <label class="block text-xs uppercase text-slate-400 mb-1">Phone / Email</label>
                    <input type="text" class="w-full bg-slate-900 border border-slate-700 rounded p-3 text-white" placeholder="07123456789" required>
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition">Submit Request</button>
            </form>
        </div>
    </main>
</body>
</html>
"""
    with open(os.path.join(project_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(landing_page_html)

    print(f"🏗️ [Project Initialized] Created build directory and staging assets at: {project_dir}")
    return project_dir


# ==========================================
# 3. Notification & Client Kickoff Emails
# ==========================================
def notify_client_and_owner_kickoff(client_name: str, target_client_email: str = None):
    # 1. Send confirmation to client if email was provided
    if target_client_email and "@" in target_client_email:
        client_body = f"""
        <p>Hi {client_name} Team,</p>
        <p>We are delighted to confirm that your 50% deposit has been received successfully. Thank you for your partnership!</p>
        <p>Our development team at <strong>GearRadar Digital Solutions</strong> has officially commenced work on your high-speed mobile build and local SEO setup.</p>
        <p>We will deliver your initial staging link within 3 business days for your feedback.</p>
        <p>Kind regards,<br><strong>Kam Tyler</strong><br>GearRadar Digital Solutions</p>
        {get_email_signature()}
        """
        send_outreach_raw(target_client_email, f"Project Kickoff Confirmed — {client_name}", client_body)

    # 2. Send owner confirmation alert
    owner_body = f"""
    <div style="font-family: Arial, sans-serif; font-size: 15px; color: #1e293b; padding: 20px; border: 1px solid #cbd5e1; border-radius: 8px;">
        <h2 style="color: #16a34a; margin-top: 0;">🚀 Project Started Successfully!</h2>
        <p><strong>Trigger Received:</strong> Deposit confirmed by you via email.</p>
        <p><strong>Client / Project:</strong> {client_name}</p>
        <p><strong>Action Taken:</strong> Web assets generated in <code>client_projects/{re.sub(r'[^a-zA-Z0-9_-]', '_', client_name).lower()}</code> and development cycle started.</p>
    </div>
    """
    send_outreach_raw(NOTIFICATION_EMAIL, f"✅ [Build Started] Project Launched: {client_name}", owner_body)


def send_outreach_raw(to_email: str, subject: str, html_content: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Kam Tyler (GearRadar) <{SENDER_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        clean_pwd = GMAIL_APP_PASSWORD.replace(" ", "")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, clean_pwd)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"🚀 [Email Delivered] Sent to: {to_email}")
    except Exception as e:
        print(f"⚠️ Error sending email: {e}")


# ==========================================
# 4. Inbound Email Router
# ==========================================
def handle_incoming_email(sender: str, subject: str, body_text: str):
    clean_sender = re.findall(r'<([^>]+)>', sender)
    sender_email = clean_sender[0] if clean_sender else sender.strip()

    # --- ACTION 1: ADMIN TRIGGER FROM YOU ---
    if NOTIFICATION_EMAIL.lower() in sender_email.lower():
        lower_sub = subject.lower()
        if any(w in lower_sub or w in body_text.lower() for w in ["start", "confirm", "deposit", "kickoff", "ابدأ"]):
            print(f"\n🔑 [Admin Command Detected] Payment verified by owner from: {sender_email}")
            
            # Extract client name
            client_name_match = re.search(r'(?:start|confirm|project|for|client)\s+([a-zA-Z0-9\s]+)', subject, re.IGNORECASE)
            client_name = client_name_match.group(1).strip() if client_name_match else "New Client"
            
            # Extract client email if written in body
            extracted_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body_text)
            target_client_email = [e for e in extracted_emails if e.lower() not in [SENDER_EMAIL.lower(), NOTIFICATION_EMAIL.lower()]]
            target_email = target_client_email[0] if target_client_email else None

            # Execute automated build
            auto_build_project_assets(client_name)
            notify_client_and_owner_kickoff(client_name, target_email)
            return

    # Ignore self-sent emails from agency address
    if SENDER_EMAIL.lower() in sender_email.lower():
        return

    # Filter bot and automated system notifications
    ignore_patterns = ["no-reply", "noreply", "donotreply", "google.com", "accounts.google", "mailer-daemon", "support@"]
    if any(pattern in sender_email.lower() for pattern in ignore_patterns):
        return

    # --- ACTION 2: INCOMING CLIENT REPLIES ---
    print(f"\n📩 Legitimate client reply from: {sender_email} | Subject: {subject}")
    lower_body = body_text.lower()

    if any(k in lower_body for k in ["proceed", "go ahead", "start", "agree", "bank details", "invoice", "payment", "yes please"]):
        print("🎯 Lead Intent: Agreement / Ready to Pay -> Sending Revolut Onboarding Invoice")
        send_onboarding_invoice(
            target_email=sender_email,
            client_name="Team",
            business_name="Your Project",
            total_amount=500.00
        )
        send_outreach_raw(
            NOTIFICATION_EMAIL,
            "🔔 [Deal Alert] Invoice Sent to Client",
            f"<p>Sent Revolut bank details to <strong>{sender_email}</strong>. Once they pay, reply or email me <em>'Start {sender_email}'</em> to launch the build.</p>"
        )

    elif any(k in lower_body for k in ["price", "cost", "how much", "quote", "pricing", "package"]):
        print("💡 Lead Intent: Pricing Inquiry -> Sending Pricing Breakdown")
        pricing_reply_html = f"""
        <p>Hi there,</p>
        <p>Thank you for getting back to me.</p>
        <p>At <strong>GearRadar Digital Solutions</strong>, our packages include:</p>
        <ul>
          <li><strong>Starter Mobile & SEO Build (£500):</strong> Fast responsive redesign, local UK SEO, and automated booking/enquiry funnels.</li>
          <li><strong>Full Catalog / Growth Package (£850):</strong> Multi-page layout, product inventory, and conversion optimization.</li>
        </ul>
        <p>We require a simple <strong>50% upfront deposit</strong> to secure development. Reply <em>'Go ahead'</em> to receive onboarding details.</p>
        <p>Kind regards,<br><strong>Kam Tyler</strong><br>GearRadar Digital Solutions</p>
        {get_email_signature()}
        """
        send_outreach_raw(sender_email, f"Re: {subject}", pricing_reply_html)


# ==========================================
# 5. Continuous IMAP Inbox Listener
# ==========================================
def listen_to_inbox():
    print(f"\n{'='*65}\n🤖 [Kam Tyler] Autonomous Inbox & Admin Command Listener\n{'='*65}")
    print(f"Monitoring: {SENDER_EMAIL} (Checking every {CHECK_INTERVAL_SECONDS}s)... Press Ctrl+C to stop.\n")

    while True:
        try:
            clean_pwd = GMAIL_APP_PASSWORD.replace(" ", "")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(SENDER_EMAIL, clean_pwd)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")
            if status == "OK" and messages[0]:
                email_ids = messages[0].split()
                processed_ids = get_processed_ids()

                for e_id in email_ids:
                    msg_uid = e_id.decode()
                    if msg_uid in processed_ids:
                        continue

                    res, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            subject, encoding = decode_header(msg.get("Subject", ""))[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")

                            sender = msg.get("From", "")
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode(errors="ignore")
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode(errors="ignore")

                            handle_incoming_email(sender, subject, body)
                            save_processed_id(msg_uid)

            mail.close()
            mail.logout()
        except Exception as e:
            print(f"⚠️ Inbox check notice: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    listen_to_inbox()