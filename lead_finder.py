import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ملف حفظ الليدات المستخرجة لتجنب التكرار
LEADS_FILE = "leads.json"

# قائمة الأنشطة المستهدفة (كافيهات، صوالين، عيادات، خدمات)
TARGET_NICHES = [
    # صوالين التجميل، الحلاقة، العناية بالبشرة
    "beauty salon in Bolton",
    "hair salon in Bolton",
    "barbershop in Bolton",
    "nail salon in Bolton",
    "aesthetic clinic in Greater Manchester",
    "beauty salon in Greater Manchester",
    "hair salon in Manchester",
    "spa and wellness in Manchester",

    # الكافيهات والمطاعم والمخابز
    "cafe in Bolton",
    "coffee shop in Bolton",
    "artisan bakery in Bolton",
    "restaurant in Bolton",
    "italian restaurant in Greater Manchester",
    "cafe in Manchester",

    # العيادات ومراكز الصحة
    "dental clinic in Bolton",
    "physiotherapy clinic in Bolton",
    "chiropractor in Greater Manchester",

    # الخدمات المهنية والحرفية
    "electrician in Bolton",
    "plumber in Bolton",
    "car detailing in Bolton",
    "car repair in Lancashire",
    "motorcycle garage in Greater Manchester"
]

def load_existing_leads():
    """تحميل الليدات المحفوظة مسبقاً"""
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_leads(leads):
    """حفظ الليدات في ملف JSON"""
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

def search_osm_leads(query: str):
    """البحث عن الأنشطة عبر OpenStreetMap Nominatim API مجاناً"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 10
    }
    headers = {
        "User-Agent": "GearRadarLeadFinder/2.0 (gearradarservices@gmail.com)"
    }
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"⚠️ Search error for query '{query}': {e}")
    return []

def run_lead_generation():
    print("\n" + "="*60)
    print("🔍 [Lead Finder] Starting Targeted Search (Salons, Cafes, Clinics, Trades)")
    print("="*60)

    existing_leads = load_existing_leads()
    existing_names = {lead.get("name", "").lower() for lead in existing_leads}
    new_leads = []

    for niche in TARGET_NICHES:
        print(f"📡 Searching live map data for [{niche}]...")
        results = search_osm_leads(niche)

        for item in results:
            name = item.get("name") or item.get("display_name", "").split(",")[0]
            if not name or name.lower() in existing_names:
                continue

            address = item.get("display_name", "")
            lead_info = {
                "name": name,
                "category": niche.split(" in ")[0],
                "location": niche.split(" in ")[1] if " in " in niche else "UK",
                "address": address,
                "lat": item.get("lat"),
                "lon": item.get("lon"),
                "email": "",  # سيتم استهدافه أو استكماله بواسطة outreach
                "status": "new",
                "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            existing_names.add(name.lower())
            new_leads.append(lead_info)
            existing_leads.append(lead_info)

        # احترام قيود الاستخدام لـ Nominatim API (فاصل زمني ثانية واحدة)
        time.sleep(1.2)

    save_leads(existing_leads)
    print(f"\n✅ [Lead Finder Complete] Found {len(new_leads)} new businesses. Total leads: {len(existing_leads)}")

if __name__ == "__main__":
    run_lead_generation()