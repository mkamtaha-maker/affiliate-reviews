import base64
import itertools
import json
import os
import time
import requests
import schedule
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# ==========================================
# 1. Configurations & Credentials
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AFFILIATE_TAG = "yourtag-20"

WP_SITE_URL = os.environ.get("WP_SITE_URL", "https://yourwebsite.com")
WP_USERNAME = os.environ.get("WP_USERNAME", "your_username")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "xxxx xxxx xxxx xxxx")

NICHES_LIST = [
    "Motorcycle Action Cameras and Helmets",
    "Smart Home Security Systems and Cameras",
    "High-Performance Running Shoes and Fitness Trackers",
    "Ergonomic Home Office Chairs and Standing Desks",
    "Wireless Noise-Canceling Gaming Headsets"
]

niche_cycle = itertools.cycle(NICHES_LIST)
client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================
# 2. Step 1: Product Discovery
# ==========================================
def agent_discover_products(niche: str, count: int = 2) -> list:
    print(f"\n🔍 [Step 1] Exploring niche: '{niche}' (Fetching top {count} products)...")

    prompt = f"""
    You are an expert e-commerce product researcher.
    Identify the top {count} trending, best-selling products in the niche: "{niche}".

    For each product, provide:
    1. "name": Exact commercial product title.
    2. "category": Specific category.
    3. "estimated_price": Approximate retail price range (e.g. "$199.99" or "$299 - $349").
    4. "availability": Stock availability status (e.g. "In Stock (Prime Eligible)").
    5. "features": 4-5 bullet points of actual technical specifications.
    6. "target_audience": Primary users.
    7. "search_query": Precise search term for Amazon.

    Return the result strictly as a JSON list of objects.
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.4,
        )
    )

    products = json.loads(response.text)
    
    for prod in products:
        query_formatted = prod["search_query"].replace(" ", "+")
        prod["affiliate_link"] = f"https://www.amazon.com/s?k={query_formatted}&tag={AFFILIATE_TAG}"
        prod["image_url"] = "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800&auto=format&fit=crop&q=80"

    return products


# ==========================================
# 3. Step 2: SEO Article Generation
# ==========================================
def agent_write_seo_review(product_data: dict) -> dict:
    print(f"✍️  [Step 2] Drafting SEO review for: {product_data['name']}...")

    prompt = f"""
    You are an elite affiliate copywriter and SEO specialist.
    Write an exhaustive, high-converting product review article for:
    Product: {product_data['name']}
    Category: {product_data['category']}
    Price: {product_data.get('estimated_price', 'Check on Amazon')}
    Stock Status: {product_data.get('availability', 'In Stock')}
    Key Features: {product_data['features']}
    Target Audience: {product_data.get('target_audience', 'Consumers')}
    Affiliate URL: {product_data['affiliate_link']}
    Image URL: {product_data['image_url']}

    Structure the response strictly in JSON format with two keys:
    - "title": High-CTR SEO title (e.g. "[Product Name] Review: Worth It in 2026?").
    - "content": Clean, semantic HTML.

    HTML Requirements:
    1. Top Affiliate Disclosure banner.
    2. Centered Product Image followed by a Price and Stock status badge.
    3. Specifications comparison table.
    4. Features breakdown using <h2> and <h3>.
    5. Pros and Cons comparison blocks.
    6. High-contrast CTA buttons linking to the Affiliate URL (target="_blank" rel="nofollow sponsored").
    7. FAQ section and Final Verdict score.
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        )
    )

    return json.loads(response.text)


# ==========================================
# 4. Step 3: WordPress Publish & Local Save
# ==========================================
def agent_publish_or_save(title: str, content: str, product_name: str):
    # 1. Local HTML Save
    os.makedirs("generated_articles", exist_ok=True)
    safe_filename = "".join(c for c in product_name if c.isalnum() or c in (" ", "_", "-")).rstrip()
    file_path = os.path.join("generated_articles", f"{safe_filename[:40]}.html")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"<h1>{title}</h1>\n\n{content}")
    print(f"💾 Article saved locally: {file_path}")

    # 2. WordPress REST API upload
    if "yourwebsite.com" not in WP_SITE_URL:
        print("🌐 Sending post to WordPress...")
        api_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/posts"
        token = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
        payload = {"title": title, "content": content, "status": "draft"}

        try:
            res = requests.post(api_endpoint, json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 201]:
                print(f"✅ Published to WordPress! Link: {res.json().get('link')}")
            else:
                print(f"⚠️ WP response status: {res.status_code}")
        except Exception as e:
            print(f"⚠️ Connection error with WP: {e}")


# ==========================================
# 5. Automated Pipeline Task
# ==========================================
def run_autonomous_pipeline():
    current_niche = next(niche_cycle)
    print(f"\n=======================================================")
    print(f"⏰ [{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Cycle for Niche: {current_niche}")
    print(f"=======================================================")

    products = agent_discover_products(niche=current_niche, count=2)
    
    for idx, prod in enumerate(products, 1):
        print(f"\n--- [Processing {idx}/{len(products)}]: {prod['name']} (Price: {prod.get('estimated_price')}) ---")
        article_data = agent_write_seo_review(prod)
        agent_publish_or_save(
            title=article_data["title"],
            content=article_data["content"],
            product_name=prod["name"]
        )
    print("\n✅ Batch completed! Waiting for next scheduled run...")


# ==========================================
# 6. Main Runner & Daily Scheduling
# ==========================================
if __name__ == "__main__":
    run_autonomous_pipeline()
    schedule.every(24).hours.do(run_autonomous_pipeline)

    print("\n⏳ Scheduler active. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)