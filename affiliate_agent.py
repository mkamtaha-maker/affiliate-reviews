import base64
import glob
import itertools
import json
import os
import subprocess
import time
import schedule
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ==========================================
# 1. Configurations
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AFFILIATE_TAG = "yourtag-20"  # ضع كود تتبع أمازون الخاص بك هنا

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
# 2. Product Discovery & SEO Writing
# ==========================================
def agent_discover_products(niche: str, count: int = 2) -> list:
    print(f"\n🔍 [Step 1] Exploring niche: '{niche}' (Fetching top {count} products)...")
    prompt = f"""
    You are an expert e-commerce product researcher.
    Identify the top {count} trending, best-selling products in the niche: "{niche}".

    For each product, provide:
    1. "name": Exact commercial product title.
    2. "category": Specific category.
    3. "estimated_price": Approximate retail price (e.g. "$199.99").
    4. "availability": Stock availability status (e.g. "In Stock (Prime Eligible)").
    5. "features": 4-5 bullet points of actual technical specifications.
    6. "target_audience": Primary users.
    7. "search_query": Precise search term for Amazon.

    Return the result strictly as a JSON list of objects.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.4)
    )
    products = json.loads(response.text)
    for prod in products:
        query_formatted = prod["search_query"].replace(" ", "+")
        prod["affiliate_link"] = f"https://www.amazon.com/s?k={query_formatted}&tag={AFFILIATE_TAG}"
        prod["image_url"] = "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800&auto=format&fit=crop&q=80"
    return products


def agent_write_seo_review(product_data: dict) -> dict:
    print(f"✍️  [Step 2] Drafting SEO review for: {product_data['name']}...")
    prompt = f"""
    You are an elite affiliate copywriter and SEO specialist.
    Write an exhaustive product review article for:
    Product: {product_data['name']}
    Price: {product_data.get('estimated_price', 'Check on Amazon')}
    Stock: {product_data.get('availability', 'In Stock')}
    Features: {product_data['features']}
    Affiliate URL: {product_data['affiliate_link']}
    Image URL: {product_data['image_url']}

    Structure the response strictly in JSON format with keys: "title", "summary", and "content".
    Ensure "content" is clean semantic HTML including specs table, pros/cons, and high-CTR affiliate buttons.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7)
    )
    return json.loads(response.text)


# ==========================================
# 3. Dynamic Homepage Builder & Git Automation
# ==========================================
def update_homepage():
    """Builds a modern, responsive index.html showcasing all generated articles."""
    articles = glob.glob("generated_articles/*.html")
    cards_html = ""

    for article in sorted(articles, key=os.path.getmtime, reverse=True):
        filename = os.path.basename(article)
        clean_name = filename.replace(".html", "")
        cards_html += f"""
        <div class="card">
            <h3>{clean_name}</h3>
            <p>Comprehensive buying guide, features breakdown, and pros/cons review.</p>
            <a href="generated_articles/{filename}" class="btn">Read Full Review &rarr;</a>
        </div>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Affiliate Hub - Expert Product Reviews</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 2rem; color: #1e293b; }}
        header {{ text-align: center; margin-bottom: 3rem; }}
        h1 {{ font-size: 2.5rem; color: #0f172a; margin-bottom: 0.5rem; }}
        p.subtitle {{ font-size: 1.1rem; color: #64748b; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; flex-direction: column; justify-content: space-between; }}
        .card h3 {{ font-size: 1.25rem; margin-top: 0; color: #1e293b; }}
        .card p {{ color: #64748b; font-size: 0.95rem; line-height: 1.5; }}
        .btn {{ display: inline-block; padding: 0.75rem 1.25rem; background: #2563eb; color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; text-align: center; }}
        .btn:hover {{ background: #1d4ed8; }}
    </style>
</head>
<body>
    <header>
        <h1>Smart Product Reviews & Guides</h1>
        <p class="subtitle">AI-curated buying guides and unbiased technical breakdowns</p>
    </header>
    <main class="grid">
        {cards_html}
    </main>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("🏠 Homepage 'index.html' updated successfully.")


def deploy_to_github():
    """Automatically commits and pushes new content to GitHub Pages."""
    print("🚀 Pushing updates to GitHub Pages...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-publish batch: {time.strftime('%Y-%m-%d %H:%M')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Successfully deployed to live site!")
    except Exception as e:
        print(f"⚠️ Git auto-deploy note: {e}")


# ==========================================
# 4. Main Autonomous Runner
# ==========================================
def run_autonomous_pipeline():
    current_niche = next(niche_cycle)
    print(f"\n{'='*55}\n⏰ [{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Cycle for Niche: {current_niche}\n{'='*55}")

    products = agent_discover_products(niche=current_niche, count=2)
    os.makedirs("generated_articles", exist_ok=True)

    for idx, prod in enumerate(products, 1):
        print(f"\n--- [Processing {idx}/{len(products)}]: {prod['name']} ---")
        article_data = agent_write_seo_review(prod)
        safe_name = "".join(c for c in prod["name"] if c.isalnum() or c in (" ", "_", "-")).rstrip()
        file_path = os.path.join("generated_articles", f"{safe_name[:40]}.html")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"<h1>{article_data['title']}</h1>\n\n{article_data['content']}")
        print(f"💾 Article saved: {file_path}")

    update_homepage()
    deploy_to_github()
    print("\n✅ Cycle complete! Next batch scheduled in 24 hours.")


if __name__ == "__main__":
    run_autonomous_pipeline()
    schedule.every(24).hours.do(run_autonomous_pipeline)

    print("\n⏳ Scheduler active. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)