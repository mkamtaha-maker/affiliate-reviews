import os
import sys
import time
import json
import glob
import smtplib
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "gearradarservices@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
REPORT_RECIPIENT = os.environ.get("REPORT_RECIPIENT", "gearradarservices@gmail.com")

class AgencyOrchestrator:
    def __init__(self):
        # 1. الخدمات الدائمة على مدار الساعة (Always-On)
        self.continuous_services = {
            "WhatsApp Agent": "whatsapp_agent.py",
            "Inbox Monitor": "inbox_monitor.py"
        }
        self.processes = {}

        # 2. جدولة التقارير والدورات الدورية
        self.last_report_time = time.time()
        self.report_interval = 21600  # تقرير تنفيذي كل 6 ساعات

        self.last_outreach_cycle = 0
        self.outreach_interval = 86400  # دورة جلب وتواصل لعملاء الوكالة (كل 24 ساعة)

        self.last_affiliate_cycle = 0
        self.affiliate_interval = 43200  # دورة توليد مراجعات أمازون للأفيلييت (كل 12 ساعة)

    def start_agent(self, name: str, script: str):
        """تشغيل أيجنت دائم باستخدام مفسر البيئة الحالية (venv)"""
        if os.path.exists(script):
            print(f"🚀 [Orchestrator] Starting {name} ({script})...")
            self.processes[name] = subprocess.Popen([sys.executable, script])
        else:
            print(f"⚠️ [Warning] File {script} not found for {name}.")

    def start_background_agents(self):
        """بدء وكلاء الاستماع والرد الدائمين"""
        print("\n" + "="*65)
        print("👑 [Master Orchestrator] Initialising Gear Radar Unified AI Engine")
        print("="*65)
        for name, script in self.continuous_services.items():
            self.start_agent(name, script)

    def run_lead_generation_and_outreach(self):
        """تشغيل محرك استخراج الليدات وإرسال عروض الـ £30"""
        print("\n🔍 [Agency Task] Launching Lead Finder...")
        if os.path.exists("lead_finder.py"):
            subprocess.run([sys.executable, "lead_finder.py"])

        print("📨 [Agency Task] Launching Outreach Engine (£30 Package)...")
        if os.path.exists("agency_outreach.py"):
            subprocess.run([sys.executable, "agency_outreach.py"])

        print("✅ [Agency Task] Local Outreach Cycle Complete.\n")

    def run_affiliate_engine(self):
        """تشغيل أيجنت التسويق بالعمولة لتوليد مقالات ومراجعات أمازون"""
        print("\n🛍️ [Affiliate Task] Launching Amazon Affiliate Content Engine...")
        if os.path.exists("affiliate_agent.py"):
            try:
                subprocess.run([sys.executable, "affiliate_agent.py"])
                print("✅ [Affiliate Task] Product Reviews & Articles Generation Complete.\n")
            except Exception as e:
                print(f"❌ [Affiliate Error]: {e}")
        else:
            print("⚠️ [Warning] affiliate_agent.py not found.")

    def monitor_and_heal(self):
        """مراقبة الوكلاء وإعادة التشغيل عند التوقف لمنع التعطل"""
        for name, proc in list(self.processes.items()):
            if proc.poll() is not None:
                print(f"🚨 [Alert] {name} stopped (Code: {proc.poll()}). Restarting in 5s...")
                time.sleep(5)
                self.start_agent(name, self.continuous_services[name])

    def generate_report_content(self) -> str:
        """تجميع إحصائيات الأداء لكافة الفروع (الوكالة + التسويق بالعمولة)"""
        # 1. إحصائيات الوكالة الرقمية
        outreach_count = 0
        if os.path.exists("outreach_log.json"):
            try:
                with open("outreach_log.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    outreach_count = len(data) if isinstance(data, list) else len(data.keys())
            except Exception:
                pass

        replies_count = 0
        if os.path.exists("processed_replies.json"):
            try:
                with open("processed_replies.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    replies_count = len(data) if isinstance(data, list) else len(data.keys())
            except Exception:
                pass

        # 2. إحصائيات مقالات أمازون
        article_files = glob.glob("generated_articles/*.html")
        articles_count = len(article_files)

        # 3. حالة الوكلاء الدائمين
        status_lines = [
            f"- {name}: {'Active & Running 🟢' if p.poll() is None else 'Stopped 🔴'}"
            for name, p in self.processes.items()
        ]

        return f"""
Gear Radar Group - Master Executive AI Report
==================================================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. SUB-AGENT HEALTH:
{chr(10).join(status_lines)}

2. DIGITAL AGENCY PIPELINE (£30 Fast Web Setup):
- Outreach Emails Dispatched: {outreach_count}
- Inquiries & Reponses Handled: {replies_count}
- WhatsApp Inbound Closer: Active (Kam Tyler Persona)

3. AMAZON AFFILIATE ENGINE:
- Published Product Reviews / Articles: {articles_count}
- Content Automation Cycle: Running every 12h

==================================================
Automated Master Report dispatched by Agency Orchestrator.
"""

    def send_email_report(self, report_text: str):
        """إرسال التقرير النهائي بالبريد"""
        if not EMAIL_PASSWORD:
            return
        msg = MIMEMultipart()
        msg["From"] = f"Gear Radar Master <{EMAIL_SENDER}>"
        msg["To"] = REPORT_RECIPIENT
        msg["Subject"] = f"📊 [Gear Radar Operations Update] {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        msg.attach(MIMEText(report_text, "plain", "utf-8"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
            print(f"📧 [Report Sent] Master operations report emailed to {REPORT_RECIPIENT}")
        except Exception as e:
            print(f"❌ [Email Error] {e}")

    def run(self):
        self.start_background_agents()

        # تشغيل الدورة الأولى فوراً عند بدء التشغيل
        self.run_affiliate_engine()
        self.last_affiliate_cycle = time.time()

        self.run_lead_generation_and_outreach()
        self.last_outreach_cycle = time.time()

        # إرسال التقرير الأولي الشامل
        self.send_email_report(self.generate_report_content())

        while True:
            try:
                self.monitor_and_heal()
                now = time.time()

                # دورة الأفيلييت (أمازون) كل 12 ساعة
                if now - self.last_affiliate_cycle >= self.affiliate_interval:
                    self.run_affiliate_engine()
                    self.last_affiliate_cycle = now

                # دورة استهداف ليدات الوكالة كل 24 ساعة
                if now - self.last_outreach_cycle >= self.outreach_interval:
                    self.run_lead_generation_and_outreach()
                    self.last_outreach_cycle = now

                # إرسال التقرير التنفيذي كل 6 ساعات
                if now - self.last_report_time >= self.report_interval:
                    self.send_email_report(self.generate_report_content())
                    self.last_report_time = now

                time.sleep(15)
            except KeyboardInterrupt:
                print("\n🛑 [Orchestrator] Gracefully shutting down all processes...")
                for proc in self.processes.values():
                    proc.terminate()
                break

if __name__ == "__main__":
    AgencyOrchestrator().run()