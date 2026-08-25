import os
import re
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# إعدادات البريد الإلكتروني (بالمسميات المتوافقة مع كافة السكربتات)
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "gearradarservices@gmail.com")
SENDER_EMAIL = EMAIL_SENDER
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
GMAIL_APP_PASSWORD = EMAIL_PASSWORD

# التفاصيل المالية والبنكية
ACCOUNT_NAME = "Kamal Mohammed Taha"
SORT_CODE = "04-29-09"
ACCOUNT_NUMBER = "16721489"
BANK_NAME = "Revolut UK"
PRICE_FULL = "£30.00"
WHATSAPP_NUMBER = "447442309417"

LEADS_FILE = "leads.json"
LOG_FILE = "outreach_log.json"

def clean_business_name(name: str) -> str:
    """تنظيف اسم النشاط للاستخدام في النطاق والإيميل"""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    cleaned = cleaned.lower().replace("ltd", "").replace("limited", "").replace("uk", "").strip()
    return cleaned

def generate_target_emails(business_name: str) -> list:
    """توليد أكثر الإيميلات التجارية احتمالية في بريطانيا"""
    cleaned = clean_business_name(business_name)
    parts = cleaned.split()
    if not parts:
        return []
    
    slug = "".join(parts[:3])
    domains = [f"{slug}.co.uk", f"{slug}.com"]
    prefixes = ["info", "bookings", "enquiries", "contact"]
    
    generated = []
    for dom in domains:
        for pre in prefixes:
            generated.append(f"{pre}@{dom}")
    return generated

def load_sent_log():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_sent_log(log_data):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

def craft_email_body(business_name: str, category: str, location: str) -> tuple:
    """صياغة عرض الـ £30 المباشر"""
    wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text=Hi%20Kam,%20I%20want%20the%20£30%20web%20setup%20for%20{business_name.replace(' ', '%20')}"
    
    subject = f"Quick Online Setup & Mobile Page for {business_name} (£30 One-Off)"
    
    body = f"""Hi {business_name} Team,

I came across {business_name} while looking at {category} businesses in {location}.

At Gear Radar Digital Solutions, we are offering a direct, quick-launch package for local businesses:
- Fast, mobile-optimised one-page web presence
- Direct WhatsApp & booking button integration
- Local Google search visibility setup
- Complete setup for a one-off fee of £30 (paid in full upfront, no recurring monthly platform fees)

If you'd like us to set this up for {business_name}, message me directly on WhatsApp to get started:
👉 WhatsApp Direct: {wa_link}

Best regards,

Kam Tyler
Growth & Web Solutions Consultant
Gear Radar Digital Solutions
Email: {EMAIL_SENDER}
WhatsApp: +44 7442 309417
Bolton / Greater Manchester, UK
"""
    return subject, body

def send_outreach_campaign(batch_size: int = 10):
    if not EMAIL_PASSWORD:
        print("⚠️ [Error] EMAIL_PASSWORD is missing in .env")
        return

    if not os.path.exists(LEADS_FILE):
        print(f"⚠️ [Error] {LEADS_FILE} not found. Run lead_finder.py first.")
        return

    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        leads = json.load(f)

    sent_log = load_sent_log()
    sent_names = {entry.get("business_name", "").lower() for entry in sent_log}
    sent_count = 0

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        for lead in leads:
            if sent_count >= batch_size:
                print(f"🛑 [Batch Limit] Sent {batch_size} emails. Pausing.")
                break

            name = lead.get("name", "").strip()
            category = lead.get("category", "local business")
            location = lead.get("location", "Greater Manchester")

            if not name or name.lower() in sent_names:
                continue

            target_email = lead.get("email")
            if not target_email:
                candidate_emails = generate_target_emails(name)
                target_email = candidate_emails[0] if candidate_emails else f"info@{clean_business_name(name)}.co.uk"

            subject, body = craft_email_body(name, category, location)

            msg = MIMEMultipart()
            msg["From"] = f"Kam Tyler <{EMAIL_SENDER}>"
            msg["To"] = target_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            try:
                server.send_message(msg)
                print(f"📨 [Outreach Sent] To: {target_email} ({name})")

                sent_log.append({
                    "business_name": name,
                    "target_email": target_email,
                    "category": category,
                    "location": location,
                    "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                sent_names.add(name.lower())
                sent_count += 1
                time.sleep(3)
            except Exception as e:
                print(f"❌ Failed sending to {target_email}: {e}")

        server.quit()
        save_sent_log(sent_log)
        print(f"\n🎉 [Outreach Cycle Finished] Successfully dispatched {sent_count} outreach proposals.")

    except Exception as e:
        print(f"❌ [SMTP Connection Error]: {e}")

if __name__ == "__main__":
    send_outreach_campaign(batch_size=10)