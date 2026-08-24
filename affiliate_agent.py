import base64
import glob
import itertools
import json
import os
import re
import subprocess
import time
import urllib.parse
from datetime import datetime
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
SITE_BASE_URL = "https://mkamtaha-maker.github.io/affiliate-reviews"

NICHES_LIST = [
    # Motorcycle & Action Gear
    "Motorcycle Action Cameras and Helmets",
    "Motorcycle Bluetooth Intercoms and Phone Mounts",
    
    # Smart Home & Security
    "Smart Video Doorbells and Outdoor Security Cameras",
    "Smart Thermostats and Energy Saving Home Automation",
    "Robot Vacuum Cleaners with Auto-Empty Docks",
    
    # Computing & Ergonomics
    "Ergonomic Standing Desks and High-Back Mesh Chairs",
    "Mechanical Keyboards and Wireless Productivity Mice",
    "Ultrawide Productivity and Gaming Monitors",
    
    # Audio & Tech Accessories
    "Active Noise-Canceling Wireless Over-Ear Headphones",
    "Portable Waterproof Bluetooth Speakers",
    "High-Capacity GaN Fast Chargers and Power Banks",
    
    # Health, Fitness & Outdoor
    "GPS Running Smartwatches and Heart Rate Monitors",
    "Home Gym Adjustable Dumbbells and Workout Benches",
    "Smart Air Purifiers and Dehumidifiers for UK Homes"
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
# 3. Product Discovery & Content Generation
# ==========================================
def agent_discover_products(niche: str, count: int = 4) -> list:
    print(f"\n🔍 [Step 1] Exploring niche: '{niche}' (Fetching top {count} products)...")
    prompt = f"""
    You are an expert e-commerce product researcher specializing in the UK market.
    Identify the top {count} trending, best-selling products in the niche: "{niche}".

    For each product, provide:
    1. name: Exact commercial product title.
    2. category: Specific category.
    3. estimated_price: Approximate retail price in GBP (e.g. "£149.99" or "£199 - £249").
    4. availability: "In Stock (Prime Eligible)".
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

            for prod in products:
                query_formatted = urllib.parse.quote_plus(prod["search_query"])
                prod["affiliate_link"] = f"https://www.amazon.co.uk/s?k={query_formatted}&tag={AFFILIATE_TAG}"

            return products
        except Exception as e:
            print(f"⚠️ API delay. Retrying in 5 seconds... (Attempt {attempt+1}/3)")
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
            print(f"⚠️ API delay. Retrying in 5 seconds... (Attempt {attempt+1}/3)")
            time.sleep(5)

    return {}


# ==========================================
# 4. SEO Schema & HTML UI Builders
# ==========================================
LOGO_SVG = """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>"""

def build_article_html(article_data: dict, product_data: dict) -> str:
    pros_html = "".join([f"<li>✅ {p}</li>" for p in article_data.get("pros", ["Class-leading performance", "Exceptional UK reliability", "Premium build quality", "High customer satisfaction"])])
    cons_html = "".join([f"<li>⚠️ {c}</li>" for c in article_data.get("cons", ["Premium investment", "Fast-moving stock"])])
    affiliate_url = product_data.get("affiliate_link", f"https://www.amazon.co.uk/s?k={urllib.parse.quote_plus(product_data['name'])}&tag={AFFILIATE_TAG}")
    price_val = str(product_data.get('estimated_price', 'Check on Amazon UK')).replace("$", "£")
    numeric_price = re.sub(r'[^\d.]', '', price_val) or "99.99"
    rating_val = article_data.get('rating', 4.8)

    # Google Rich Snippet Structured Data (JSON-LD)
    schema_json = json.dumps({
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": product_data['name'],
        "description": article_data.get('excerpt', ''),
        "brand": {
            "@type": "Brand",
            "name": product_data['name'].split()[0]
        },
        "offers": {
            "@type": "Offer",
            "url": affiliate_url,
            "priceCurrency": "GBP",
            "price": numeric_price,
            "availability": "https://schema.org/InStock"
        },
        "review": {
            "@type": "Review",
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": str(rating_val),
                "bestRating": "5"
            },
            "author": {
                "@type": "Organization",
                "name": "GearRadar UK"
            }
        }
    }, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article_data.get('title', product_data['name'])}</title>
    <meta name="description" content="{article_data.get('excerpt', '')}">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script type="application/ld+json">
{schema_json}
    </script>
    <style>
        :root {{ --primary: #2563eb; --primary-hover: #1d4ed8; --dark: #0f172a; --light-bg: #f8fafc; --border: #e2e8f0; --text-main: #334155; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: var(--light-bg); color: var(--text-main); line-height: 1.7; padding-bottom: 5rem; }}
        
        .nav-wrapper {{ background: #fff; border-bottom: 1px solid var(--border); box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
        .nav {{ padding: 1.2rem 2rem; display: flex; justify-content: space-between; align-items: center; max-width: 900px; margin: 0 auto; }}
        .brand-logo {{ display: flex; align-items: center; gap: 0.75rem; text-decoration: none; font-weight: 800; color: var(--dark); font-size: 1.25rem; }}
        .brand-logo span {{ color: var(--primary); }}
        
        .container {{ max-width: 860px; margin: 2.5rem auto; padding: 0 1.5rem; }}
        .disclosure {{ background: #eff6ff; border-left: 4px solid var(--primary); padding: 0.85rem 1.25rem; border-radius: 0 8px 8px 0; font-size: 0.85rem; color: #1e40af; margin-bottom: 2rem; }}
        h1.article-title {{ font-size: 2.3rem; font-weight: 800; color: var(--dark); line-height: 1.3; margin-bottom: 1rem; }}
        .meta-bar {{ display: flex; gap: 1rem; font-size: 0.9rem; color: #64748b; margin-bottom: 2rem; align-items: center; }}
        .badge {{ background: #e0e7ff; color: #3730a3; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; font-size: 0.8rem; }}
        
        .product-spotlight {{ background: #fff; border: 1px solid var(--border); border-radius: 16px; padding: 2.5rem; margin-bottom: 2.5rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04); }}
        .spotlight-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }}
        .spotlight-header h2 {{ font-size: 1.8rem; color: var(--dark); }}
        .price-tag {{ font-size: 2.2rem; font-weight: 800; color: #059669; }}
        .rating-box {{ display: inline-flex; align-items: center; gap: 0.35rem; background: #fef3c7; color: #92400e; font-weight: 700; padding: 0.3rem 0.75rem; border-radius: 6px; font-size: 0.95rem; margin-bottom: 1rem; }}
        
        .cta-btn {{ display: block; text-align: center; background: #ff9900; background: linear-gradient(180deg, #f7dfa5 0%, #f0c14b 100%); border: 1px solid #a88734; color: #111; padding: 1rem 1.5rem; border-radius: 10px; font-weight: 700; text-decoration: none; font-size: 1.1rem; box-shadow: 0 2px 5px rgba(213,217,217,.5); transition: transform 0.1s; margin-top: 1.5rem; }}
        .cta-btn:hover {{ background: #f0c14b; transform: scale(1.01); }}
        
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
        table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; background: #fff; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }}
        th, td {{ padding: 0.85rem 1.2rem; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #f1f5f9; color: var(--dark); font-weight: 700; }}
        @media(max-width: 768px) {{ .pros-cons-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <header class="nav-wrapper">
        <div class="nav">
            <a href="../index.html" class="brand-logo">
                {LOGO_SVG}
                <span>GearRadar</span> UK
            </a>
            <span class="badge">Verified UK Review</span>
        </div>
    </header>

    <div class="container">
        <div class="disclosure"><strong>Affiliate Disclosure:</strong> When you purchase through links on our site, we may earn an affiliate commission at no extra cost to you.</div>
        <h1 class="article-title">{article_data.get('title', product_data['name'])}</h1>
        <div class="meta-bar"><span>By Technical Editorial Team</span> • <span>UK Edition</span> • <span class="badge">{product_data.get('category', 'Gear & Tech')}</span></div>
        
        <div class="product-spotlight">
            <div class="spotlight-header">
                <div>
                    <h2>{product_data['name']}</h2>
                    <div class="rating-box">★ {rating_val} / 5.0 Overall Rating</div>
                </div>
                <div class="price-tag">{price_val}</div>
            </div>
            <p style="font-size: 1rem; color: #64748b; line-height: 1.6;">{article_data.get('excerpt', 'Comprehensive testing, specifications, and buying guide for UK consumers.')}</p>
            <a href="{affiliate_url}" target="_blank" rel="nofollow sponsored" class="cta-btn">Check Best Price on Amazon UK &rarr;</a>
        </div>

        <div class="pros-cons-grid">
            <div class="pros-box"><h3>Reasons to Buy</h3><ul>{pros_html}</ul></div>
            <div class="cons-box"><h3>Reasons to Avoid</h3><ul>{cons_html}</ul></div>
        </div>

        <div class="content-body">{article_data.get('content_body', '')}</div>

        <div style="text-align: center; margin-top: 3.5rem; padding: 2.5rem; background: #fff; border-radius: 16px; border: 1px solid var(--border);">
            <h3 style="font-size: 1.4rem; margin-bottom: 0.5rem; color: var(--dark);">Ready to Purchase?</h3>
            <p style="color: #64748b; margin-bottom: 1.5rem;">Check real-time stock and fast Prime delivery on Amazon UK.</p>
            <a href="{affiliate_url}" target="_blank" rel="nofollow sponsored" class="cta-btn" style="display: inline-block; padding: 1rem 2.5rem; width: auto;">View on Amazon.co.uk &rarr;</a>
        </div>
    </div>
</body>
</html>"""


# ==========================================
# 5. Automated Sitemap & Robots Generator
# ==========================================
def generate_sitemap_and_robots():
    """Generates an up-to-date sitemap.xml and robots.txt for Google Search Console."""
    articles = glob.glob("generated_articles/*.html")
    today = datetime.now().strftime("%Y-%m-%d")
    
    url_nodes = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <priority>1.00</priority>
  </url>
"""
    for article in sorted(articles, key=os.path.getmtime, reverse=True):
        filename = os.path.basename(article)
        safe_url = f"{SITE_BASE_URL}/generated_articles/{urllib.parse.quote(filename)}"
        url_nodes += f"""  <url>
    <loc>{safe_url}</loc>
    <lastmod>{today}</lastmod>
    <priority>0.80</priority>
  </url>
"""

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{url_nodes}</urlset>"""

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    robots_txt = f"""User-agent: *
Allow: /
Sitemap: {SITE_BASE_URL}/sitemap.xml
"""
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots_txt)

    print("🗺️  'sitemap.xml' and 'robots.txt' generated successfully for Google Search Console.")


def sync_all_site_pages():
    """Synchronizes homepage, subpages, sitemap, and deploys everything."""
    os.makedirs("generated_articles", exist_ok=True)
    articles = glob.glob("generated_articles/*.html")
    cards_html = ""

    for article in sorted(articles, key=os.path.getmtime, reverse=True):
        filename = os.path.basename(article)
        clean_name = filename.replace(".html", "")
        affiliate_url = f"https://www.amazon.co.uk/s?k={urllib.parse.quote_plus(clean_name)}&tag={AFFILIATE_TAG}"

        try:
            with open(article, "r", encoding="utf-8") as f:
                old_html = f.read()

            body_match = re.search(r'(<h2.*|<div class="content-body">.*)', old_html, re.DOTALL)
            body_text = body_match.group(0) if body_match else f"<p>Complete hands-on review and specifications for {clean_name}.</p>"
            body_text = body_text.replace("$", "£")

            refactored_article = build_article_html(
                article_data={
                    "title": f"{clean_name} Review (2026): Is It Worth It?",
                    "excerpt": f"An in-depth review, lab testing breakdown, and UK price comparison for {clean_name}.",
                    "rating": 4.9 if "Shoei" in clean_name else 4.8,
                    "content_body": body_text
                },
                product_data={
                    "name": clean_name,
                    "category": "Gear & Technology",
                    "estimated_price": "£499.99" if "Insta360" in clean_name else "£589.00",
                    "affiliate_link": affiliate_url
                }
            )
            with open(article, "w", encoding="utf-8") as f:
                f.write(refactored_article)
        except Exception as e:
            print(f"Error syncing {filename}: {e}")

        badge_name = "Action Cam" if "Insta360" in clean_name or "Camera" in clean_name else ("Motorcycle" if "Shoei" in clean_name or "Helmet" in clean_name else "Tech Gear")

        cards_html += f"""
        <article class="card">
            <div class="card-top">
                <span class="badge">{badge_name}</span>
                <span class="rating">★ 4.8/5</span>
            </div>
            <div class="card-content">
                <h3>{clean_name}</h3>
                <p>Complete UK buyer's guide, lab testing analysis, pros & cons, and long-term verdict.</p>
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
    <meta name="description" content="Unbiased, data-driven buying recommendations and tech evaluations tailored for the UK market.">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #2563eb; --dark: #0f172a; --light-bg: #f8fafc; --border: #e2e8f0; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: var(--light-bg); color: #334155; line-height: 1.6; }}
        
        .navbar {{ background: #fff; border-bottom: 1px solid var(--border); padding: 1.25rem 2rem; }}
        .nav-inner {{ max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
        .brand {{ display: flex; align-items: center; gap: 0.75rem; text-decoration: none; font-size: 1.4rem; font-weight: 800; color: var(--dark); }}
        .brand span {{ color: var(--primary); }}
        .nav-badge {{ background: #eff6ff; color: var(--primary); font-weight: 700; font-size: 0.85rem; padding: 0.35rem 0.85rem; border-radius: 9999px; border: 1px solid #bfdbfe; }}

        .hero-section {{ text-align: center; padding: 4.5rem 1.5rem 3.5rem; background: #fff; border-bottom: 1px solid var(--border); }}
        .hero-section h1 {{ font-size: 2.9rem; font-weight: 800; color: var(--dark); margin-bottom: 0.75rem; letter-spacing: -0.025em; }}
        .hero-section p {{ font-size: 1.15rem; color: #64748b; max-width: 620px; margin: 0 auto; }}

        .container {{ max-width: 1200px; margin: 3.5rem auto; padding: 0 1.5rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 2rem; }}
        
        .card {{ background: #fff; border-radius: 16px; border: 1px solid var(--border); padding: 2rem; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s ease, box-shadow 0.2s ease; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }}
        .card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 24px -10px rgba(0,0,0,0.08); border-color: #cbd5e1; }}
        
        .card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }}
        .badge {{ background: #eff6ff; color: var(--primary); padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; }}
        .rating {{ font-weight: 700; font-size: 0.85rem; color: #d97706; }}
        
        .card-content h3 {{ font-size: 1.3rem; color: var(--dark); font-weight: 700; margin-bottom: 0.75rem; line-height: 1.4; }}
        .card-content p {{ color: #64748b; font-size: 0.95rem; margin-bottom: 1.75rem; }}
        
        .btn {{ display: block; padding: 0.85rem 1.25rem; background: #f8fafc; color: var(--dark); text-decoration: none; border-radius: 8px; font-weight: 700; text-align: center; border: 1px solid var(--border); transition: all 0.2s; }}
        .btn:hover {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
        
        footer {{ text-align: center; padding: 3rem 1.5rem; color: #94a3b8; font-size: 0.85rem; border-top: 1px solid var(--border); margin-top: 4rem; background: #fff; }}
    </style>
</head>
<body>
    <header class="navbar">
        <div class="nav-inner">
            <a href="index.html" class="brand">
                {LOGO_SVG}
                <div><span>GearRadar</span> UK</div>
            </a>
            <span class="nav-badge">Autonomous AI Product Hub</span>
        </div>
    </header>

    <section class="hero-section">
        <h1>Smart Product Reviews & Guides</h1>
        <p>Unbiased, data-driven buying recommendations and tech evaluations tailored for the UK market.</p>
    </section>

    <main class="container">
        <div class="grid">{cards_html}</div>
    </main>

    <footer>
        <p>© 2026 GearRadar UK. As an Amazon Associate, we earn from qualifying purchases.</p>
    </footer>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    generate_sitemap_and_robots()
    print("🏠 Homepage, Structured Schemas, and Sitemap synchronized successfully.")


def deploy_to_github():
    print("🚀 Pushing updates to GitHub Pages...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Automated SEO Sitemap & Schema Push: {time.strftime('%Y-%m-%d %H:%M')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Live site deployed with full SEO Architecture!")
    except Exception as e:
        print(f"⚠️ Git deploy note: {e}")


# ==========================================
# 6. Autonomous Pipeline Runner
# ==========================================
def run_autonomous_pipeline():
    current_niche = next(niche_cycle)
    print(f"\n{'='*60}\n⏰ Starting Cycle for Niche: {current_niche}\n{'='*60}")
    
    products = agent_discover_products(niche=current_niche, count=4)
    if not products:
        return

    os.makedirs("generated_articles", exist_ok=True)
    for idx, prod in enumerate(products, 1):
        print(f"--- [Processing {idx}/{len(products)}]: {prod['name']} (Est: {prod.get('estimated_price')}) ---")
        article_data = agent_write_seo_review(prod)
        if not article_data:
            continue
        full_html = build_article_html(article_data, prod)
        safe_name = "".join(c for c in prod["name"] if c.isalnum() or c in (" ", "_", "-")).rstrip()
        file_path = os.path.join("generated_articles", f"{safe_name[:40]}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_html)

    sync_all_site_pages()
    deploy_to_github()
    print("\n✅ Batch published! Next run in 6 hours.")


if __name__ == "__main__":
    sync_all_site_pages()
    deploy_to_github()

    schedule.every(6).hours.do(run_autonomous_pipeline)

    print("\n⏳ Autonomous agent is running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)