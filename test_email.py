import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = "gearradarservices@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
RECEIVER_EMAIL = "gearradarservices@gmail.com"

def send_greeting_test():
    if not GMAIL_APP_PASSWORD:
        print("❌ لم يتم العثور على GMAIL_APP_PASSWORD في ملف .env")
        return

    print("🚀 جاري الاتصال بخادم Gmail SMTP وإرسال رسالة التحية...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "👋 Greetings from Kam Tyler | GearRadar Digital Solutions"
    msg["From"] = f"Kam Tyler (GearRadar) <{SENDER_EMAIL}>"
    msg["To"] = RECEIVER_EMAIL

    html_content = """
    <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 15px; color: #334155; line-height: 1.7; max-width: 600px;">
        <p style="font-size: 16px; font-weight: 600; color: #0f172a;">مرحباً كيمو،</p>
        
        <p>أنا <strong>Kam Tyler</strong>، مستشار النمو والحلول الرقمية في <strong>GearRadar Digital Solutions</strong>.</p>
        
        <p>تم ربط نظام المراسلات التلقائي بنجاح! الأيجنت الآن جاهز للبحث عن الفرص التسويقية وتقديم خدمات تصميم المواقع، تحسين السيو، وإدارة الحملات الرقمية للعملاء.</p>

        <table style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; color: #334155; margin-top: 30px; border-top: 2px solid #e2e8f0; padding-top: 15px;">
          <tr>
            <td style="padding-right: 15px; vertical-align: middle;">
              <div style="background: #2563eb; color: #ffffff; border-radius: 8px; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 18px; text-align: center; line-height: 44px;">
                GR
              </div>
            </td>
            <td style="border-left: 2px solid #2563eb; padding-left: 15px;">
              <div style="font-weight: 700; font-size: 16px; color: #0f172a;">Kam Tyler</div>
              <div style="font-size: 13px; color: #2563eb; font-weight: 600;">Marketing & Web Solutions Consultant</div>
              <div style="font-size: 13px; color: #64748b; font-weight: 700;">GearRadar Digital Solutions</div>
              <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                ✉️ gearradarservices@gmail.com | 🌐 <a href="https://mkamtaha-maker.github.io/affiliate-reviews/" style="color: #2563eb; text-decoration: none;">gearradar.co.uk</a>
              </div>
            </td>
          </tr>
        </table>
    </div>
    """

    msg.attach(MIMEText(html_content, "html"))

    try:
        clean_password = GMAIL_APP_PASSWORD.replace(" ", "")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, clean_password)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"✅ تم إرسال الإيميل بنجاح إلى: {RECEIVER_EMAIL}!")
    except Exception as e:
        print(f"❌ خطأ أثناء الإرسال: {e}")

if __name__ == "__main__":
    send_greeting_test()