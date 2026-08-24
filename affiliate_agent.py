import base64
import glob
import itertools
import json
import os
import subprocess
import time
import urllib.parse
import schedule
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

# ==========================================
# 1. Configurations & Amazon Associates Setup
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AFFILIATE_TAG = "kamalgear-21"

NICHES_LIST = [
    "Motorcycle Action Cameras and Helmets",
    "Smart Home Security Systems and Cameras",
    "High-Performance Running Shoes and Fitness Trackers",
    "Ergonomic Home Office Chairs and Standing Desks",
    "Wireless Noise-Canceling Gaming Headsets"
]

TECH_IMAGES = [
    "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=800&auto=format&fit=crop&q=80"
]

niche_cycle = itertools.cycle(NICHES_LIST)
client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================
# 2. Pydantic Schemas for Strict JSON
# ==========================================
class ProductItem(BaseModel):
    name: str
    category: str
    estimated_price: str
    availability: str
    features: list[str]
    target_audience: str
    search_query: str

class ProductDiscoveryResult(BaseModel):
    products: list[ProductItem]

class SEOArticle(BaseModel):
    title: str
    excerpt: str
    rating: float
    pros: list[str]
    cons: list[str]
    content_body: str


# ==========================================
# 3. Product Discovery & SEO Generator
# ==========================================
def agent_discover_products(niche: str, count: int = 2) -> list:
    print(f"\n🔍 [Step 1] Exploring niche: '{niche}' (Fetching top {count} products)...")
    prompt = f"""
    You are an expert e-commerce product researcher specializing in the UK market.
    Identify the top {count} trending, best-selling products in the niche: "{niche}".

    For each product, provide:
    1. name: Exact commercial product title.
    2. category: Specific category.
    3. estimated_price: Approximate retail price in GBP (e.g. "£149.99" or "£199 - £249").
    4. availability: Stock status (e.g. "In Stock (Prime Eligible)").
    5. features: 4-5 bullet points of actual technical specifications.
    6. target_audience: Primary users.
    7. search_query: Precise search term for Amazon UK.
    """
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ProductDiscoveryResult,
                    temperature=0.4,
                )
            )
            result = json.loads(response.text)
            products = result.get("products", [])

            for idx, prod in enumerate(products):
                query_formatted = urllib.parse.quote_plus(prod["search_query"])
                prod["affiliate_link"] = f"https://www.amazon.co.uk/s?k={query_formatted}&tag={AFFILIATE_TAG}"
                prod["image_url"] = TECH_IMAGES[idx % len(TECH_IMAGES)]

            return products
        except Exception as e:
            print(f"⚠️ API spike or delay: {e}. Retrying in 5 seconds... (Attempt {attempt+1}/3)")
            time.sleep(5)

    return []


def agent_write_seo_review(product_data: dict) -> dict:
    print(f"✍️  [Step 2] Drafting SEO review for: {product_data['name']}...")
    prompt = f"""
    You are an elite affiliate copywriter and SEO specialist.
    Write an in-depth, conversion-focused product review article for UK consumers:
    Product: {product_data['name']}
    Category: {product_data['category']}
    Price: {product_data.get('estimated_price', 'Check on Amazon.co.uk')}
    Stock: {product_data.get('availability', 'In Stock')}
    Key Features: {product_data['features']}
    Target Audience: {product_data.get('target_audience', 'Consumers')}
    Affiliate URL: {product_data['affiliate_link']}

    Structure the JSON output with:
    - title: High-CTR SEO title (e.g. "[Product Name] Review (2026): Is It Worth It?").
    - excerpt: A compelling 2-sentence summary hook.
    - rating: A score out of 5.0 (e.g. 4.8).
    - pros: List of 4 distinct advantages.
    - cons: List of 2 minor disadvantages.
    - content_body: Semantic HTML paragraphs and <h2>/<h3> headers providing a comprehensive breakdown of build quality, performance, comparison with alternatives, and who should buy it.
    """
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SEOArticle,
                    temperature=0.7,
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"⚠️ API spike or delay: {e}. Retrying in 5 seconds... (Attempt {attempt+1}/3)")
            time.sleep(5)

    return {}


# ==========================================
# 4. Premium HTML Layout Builders
# ==========================================
def build_article_html(article_data: dict, product_data: dict) -> str:
    """Wraps article content inside a modern, conversion-optimized standalone webpage."""
    pros_html = "".join([f"<li>✅ {p}</li>" for p in article_data.get("pros", [])])
    cons_html = "".join([f"<li>⚠️ {c}</li>" for c in article_data.get("cons", [])])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article_data.get('title', product_data['name'])}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --dark: #0f172a;
            --light-bg: #f8fafc;
            --border: #e2e8f0;
            --text-main: #334155;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: var(--light-bg); color: var(--text-main); line-height: 1.7; padding-bottom: 5rem; }}
        
        .nav {{ background: #fff; border-bottom: 1px solid var(--border); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; max-width: 1100px; margin: 0 auto; border-radius: 0 0 16px 16px; }}
        .nav a {{ text-decoration: none; font-weight: 700; color: var(--dark); font-size: 1.1rem; }}
        .nav a span {{ color: var(--primary); }}

        .container {{ max-width: 900px; margin: 2.5rem auto; padding: 0 1.5rem; }}

        .disclosure {{ background: #eff6ff; border-left: 4px solid var(--primary); padding: 0.85rem 1.25rem; border-radius: 0 8px 8px 0; font-size: 0.85rem; color: #1e40af; margin-bottom: 2rem; }}
        
        h1.article-title {{ font-size: 2.3rem; font-weight: 800; color: var(--dark); line-height: 1.3; margin-bottom: 1rem; }}
        .meta-bar {{ display: flex; gap: 1rem; font-size: 0.9rem; color: #64748b; margin-bottom: 2rem; align-items: center; }}
        .badge {{ background: #e0e7ff; color: #3730a3; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; font-size: 0.8rem; }}

        .product-hero {{ background: #fff; border: 1px solid var(--border); border-radius: 16px; padding: 2rem; margin-bottom: 2.5rem; display: grid; grid-template-columns: 1fr 1.2fr; gap: 2rem; align-items: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04); }}
        .product-hero img {{ width: 100%; height: 260px; border-radius: 12px; object-fit: cover; background: #e2e8f0; }}
        .hero-info h2 {{ font-size: 1.5rem; color: var(--dark); margin-bottom: 0.5rem; }}
        .price-tag {{ font-size: 1.8rem; font-weight: 800; color: #059669; margin: 0.75rem 0; }}
        .rating-box {{ display: inline-flex; align-items: center; gap: 0.35rem; background: #fef3c7; color: #92400e; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.9rem; margin-bottom: 1rem; }}
        
        .cta-btn {{ display: block; text-align: center; background: #ff9900; background: linear-gradient(180deg, #f7dfa5 0%, #f0c14b 100%); border: 1px solid #a88734; color: #111; padding: 0.85rem 1.5rem; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 1.05rem; box-shadow: 0 2px 5px rgba(213,217,217,.5); transition: all 0.2s ease; }}
        .cta-btn:hover {{ background: #f0c14b; transform: translateY(-1px); }}

        .pros-cons-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 2.5rem 0; }}
        .pros-box {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 1.5rem; }}
        .cons-box {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 1.5rem; }}
        .pros-box h3 {{ color: #166534; font-size: 1.15rem; margin-bottom: 1rem; }}
        .cons-box h3 {{ color: #991b1b; font-size: 1.15rem; margin-bottom: 1rem; }}
        .pros-box ul, .cons-box ul {{ list-style: none; }}
        .pros-box li, .cons-box li {{ margin-bottom: 0.6rem; font-size: 0.95rem; }}

        .content-body {{ font-size: 1.05rem; color: #334155; }}
        .content-body h2 {{ font-size: 1.6rem; color: var(--dark); margin: 2rem 0 1rem; }}
        .content-body h3 {{ font-size: 1.3rem; color: var(--dark); margin: 1.5rem 0 0.75rem; }}
        .content-body p {{ margin-bottom: 1.25rem; }}

        @media(max-width: 768px) {{
            .product-hero {{ grid-template-columns: 1fr; }}
            .pros-cons-grid {{ grid-template-columns: 1fr; }}
            h1.article-title {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="../index.html">← <span>Gear</span>Radar UK</a>
        <span class="badge">Verified Review</span>
    </div>

    <div class="container">
        <div class="disclosure">
            <strong>Affiliate Disclosure:</strong> When you purchase through links on our site, we may earn an affiliate commission at no extra cost to you.
        </div>

        <h1 class="article-title">{article_data.get('title', product_data['name'])}</h1>
        <div class="meta-bar">
            <span>By Tech Editorial Team</span> • 
            <span>UK Edition</span> • 
            <span class="badge">{product_data['category']}</span>
        </div>

        <div class="product-hero">
            <img src="{product_data['image_url']}" alt="{product_data['name']}">
            <div class="hero-info">
                <h2>{product_data['name']}</h2>
                <div class="rating-box">★ {article_data.get('rating', 4.8)} / 5.0 Editorial Rating</div>
                <div class="price-tag">{product_data.get('estimated_price', 'Check Price')}</div>
                <p style="font-size: 0.95rem; color: #64748b; margin-bottom: 1.25rem;">{article_data.get('excerpt', '')}</p>
                <a href="{product_data['affiliate_link']}" target="_blank" rel="nofollow sponsored" class="cta-btn">
                    Check Best Price on Amazon UK &rarr;
                </a>
            </div>
        </div>

        <div class="pros-cons-grid">
            <div class="pros-box">
                <h3>Reasons to Buy</h3>
                <ul>{pros_html}</ul>
            </div>
            <div class="cons-box">
                <h3>Reasons to Avoid</h3>
                <ul>{cons_html}</ul>
            </div>
        </div>

        <div class="content-body">
            {article_data.get('content_body', '')}
        </div>

        <div style="text-align: center; margin-top: 3.5rem; padding: 2.5rem; background: #fff; border-radius: 16px; border: 1px solid var(--border);">
            <h3 style="font-size: 1.4rem; margin-bottom: 0.5rem; color: var(--dark);">Ready to Grab This Deal?</h3>
            <p style="color: #64748b; margin-bottom: 1.5rem;">Check real-time stock and expedited Prime delivery on Amazon UK.</p>
            <a href="{product_data['affiliate_link']}" target="_blank" rel="nofollow sponsored" class="cta-btn" style="display: inline-block; padding: 1rem 2.5rem;">
                View on Amazon.co.uk &rarr;
            </a>
        </div>
    </div>
</body>
</html>"""


def update_homepage():
    """Builds a magazine-style homepage with high-res active images."""
    articles = glob.glob("generated_articles/*.html")
    cards_html = ""

    for idx, article in enumerate(sorted(articles, key=os.path.getmtime, reverse=True)):
        filename = os.path.basename(article)
        clean_name = filename.replace(".html", "")
        img_url = TECH_IMAGES[idx % len(TECH_IMAGES)]

        cards_html += f"""
        <article class="card">
            <div class="card-thumb">
                <img src="{img_url}" alt="{clean_name}" loading="lazy">
                <span class="badge">In-Depth Review</span>
            </div>
            <div class="card-content">
                <h3>{clean_name}</h3>
                <p>Complete UK buyer's guide, lab testing results, price analysis, and long-term verdict.</p>
                <a href="generated_articles/{filename}" class="btn">Read Full Review &rarr;</a>
            </div>
        </article>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GearRadar UK - Smart Product Reviews & Buying Guides</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2563eb;
            --dark: #0f172a;
            --light-bg: #f8fafc;
            --border: #e2e8f0;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: var(--light-bg); color: #334155; line-height: 1.6; }}
        
        .header {{ background: #fff; border-bottom: 1px solid var(--border); padding: 3.5rem 1.5rem; text-align: center; }}
        .header-badge {{ background: #eff6ff; color: var(--primary); padding: 0.4rem 1rem; border-radius: 9999px; font-weight: 700; font-size: 0.85rem; display: inline-block; margin-bottom: 1rem; }}
        .header h1 {{ font-size: 2.8rem; font-weight: 800; color: var(--dark); margin-bottom: 0.75rem; letter-spacing: -0.025em; }}
        .header p {{ font-size: 1.15rem; color: #64748b; max-width: 600px; margin: 0 auto; }}

        .container {{ max-width: 1200px; margin: 3rem auto; padding: 0 1.5rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 2rem; }}

        .card {{ background: #fff; border-radius: 16px; border: 1px solid var(--border); overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s ease, box-shadow 0.2s ease; }}
        .card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 24px -10px rgba(0,0,0,0.08); }}
        
        .card-thumb {{ position: relative; height: 200px; width: 100%; overflow: hidden; background: #e2e8f0; }}
        .card-thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
        .card-thumb .badge {{ position: absolute; top: 12px; left: 12px; background: rgba(15, 23, 42, 0.85); color: #fff; padding: 0.25rem 0.65rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }}

        .card-content {{ padding: 1.5rem; display: flex; flex-direction: column; flex-grow: 1; justify-content: space-between; }}
        .card-content h3 {{ font-size: 1.2rem; color: var(--dark); font-weight: 700; margin-bottom: 0.75rem; line-height: 1.4; }}
        .card-content p {{ color: #64748b; font-size: 0.92rem; margin-bottom: 1.5rem; }}

        .btn {{ display: inline-block; padding: 0.75rem 1.25rem; background: var(--primary); color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; text-align: center; transition: background 0.2s; }}
        .btn:hover {{ background: #1d4ed8; }}

        footer {{ text-align: center; padding: 3rem 1.5rem; color: #94a3b8; font-size: 0.85rem; border-top: 1px solid var(--border); margin-top: 4rem; background: #fff; }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-badge">AI-Powered UK Product Hub</div>
        <h1>Smart Product Reviews & Guides</h1>
        <p>Unbiased, data-driven buying recommendations and tech evaluations tailored for the UK market.</p>
    </header>

    <main class="container">
        <div class="grid">
            {cards_html}
        </div>
    </main>

    <footer>
        <p>© 2026 GearRadar UK. As an Amazon Associate, we earn from qualifying purchases.</p>
    </footer>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("🏠 Premium homepage 'index.html' updated with high-res active images.")


def deploy_to_github():
    """Commits and pushes changes directly to GitHub Pages."""
    print("🚀 Pushing updates to GitHub Pages...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"UI and Image Update: {time.strftime('%Y-%m-%d %H:%M')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Live site deployed successfully!")
    except Exception as e:
        print(f"⚠️ Git deploy note: {e}")


# ==========================================
# 5. Pipeline Runner & Scheduling
# ==========================================
def run_autonomous_pipeline():
    current_niche = next(niche_cycle)
    print(f"\n{'='*60}\n⏰ [{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Cycle for Niche: {current_niche}\n{'='*60}")

    products = agent_discover_products(niche=current_niche, count=2)
    if not products:
        print("⚠️ No products retrieved this cycle. Skipping to next loop.")
        return

    os.makedirs("generated_articles", exist_ok=True)

    for idx, prod in enumerate(products, 1):
        print(f"\n--- [Processing {idx}/{len(products)}]: {prod['name']} (Est: {prod.get('estimated_price')}) ---")
        article_data = agent_write_seo_review(prod)
        if not article_data:
            continue

        full_html = build_article_html(article_data, prod)
        safe_name = "".join(c for c in prod["name"] if c.isalnum() or c in (" ", "_", "-")).rstrip()
        file_path = os.path.join("generated_articles", f"{safe_name[:40]}.html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"💾 Article saved with standalone UI: {file_path}")

    update_homepage()
    deploy_to_github()
    print("\n✅ Cycle finished! Next run scheduled in 24 hours.")


if __name__ == "__main__":
    # تشغيل تحديث فوري للواجهة ثم بدء الجدولة
    update_homepage()
    deploy_to_github()

    schedule.every(24).hours.do(run_autonomous_pipeline)

    print("\n⏳ Autonomous agent is running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)