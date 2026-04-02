"""
SolRise - Flask API v5
======================
- Proper MongoDB integration
- Fixed routing
- Better error handling
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from bson import ObjectId
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from pipeline import SolRisePipeline

app = Flask(__name__)
CORS(app)

# =============================================================================
# CONFIGURATION
# =============================================================================

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
# Support both MONGODB_URI and MONGO_URI env var names
MONGODB_URI = (
    os.environ.get('MONGODB_URI') or
    os.environ.get('MONGO_URI') or
    'mongodb://localhost:27017/'
)

# Use smaller, faster model for generation
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')  # Balanced: fast + good quality

# =============================================================================
# DATABASE SETUP
# =============================================================================

db = None
using_mongodb = False

try:
    from pymongo import MongoClient
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Force connection check
    db = client.solrise
    
    # Create indexes for better performance
    db.projects.create_index('client_name')
    db.projects.create_index('created_at')
    
    using_mongodb = True
    print(f"✅ MongoDB connected: {MONGODB_URI}")
    print(f"   Using Database: solrise")
    print(f"   Collections: {db.list_collection_names()}")
except Exception as e:
    print(f"⚠️  MongoDB connection failed: {e}")
    print("   Using in-memory storage (data will not persist)")
    
    # Fallback in-memory storage
    class InMemoryCollection:
        def __init__(self, name):
            self.name = name
            self.data = {}
        
        def insert_one(self, doc):
            if '_id' not in doc:
                doc['_id'] = ObjectId()
            self.data[str(doc['_id'])] = doc.copy()
            print(f"   📝 Saved to {self.name}: {doc['_id']}")
            return type('Result', (), {'inserted_id': doc['_id']})()
        
        def find_one(self, query):
            if '_id' in query:
                key = str(query['_id'])
                return self.data.get(key)
            # Search by other fields
            for doc in self.data.values():
                if all(doc.get(k) == v for k, v in query.items()):
                    return doc
            return None
        
        def find(self, query=None):
            if query is None:
                return list(self.data.values())
            return [d for d in self.data.values() if all(d.get(k) == v for k, v in query.items())]
        
        def update_one(self, query, update):
            doc = self.find_one(query)
            if doc and '$set' in update:
                doc.update(update['$set'])
                self.data[str(doc['_id'])] = doc
                print(f"   🔄 Updated {self.name}: {doc['_id']}")
                return type('Result', (), {'modified_count': 1})()
            return type('Result', (), {'modified_count': 0})()
        
        def delete_one(self, query):
            doc = self.find_one(query)
            if doc:
                del self.data[str(doc['_id'])]
                return type('Result', (), {'deleted_count': 1})()
            return type('Result', (), {'deleted_count': 0})()
        
        def count_documents(self, query=None):
            if query is None:
                return len(self.data)
            return len(self.find(query))
    
    class InMemoryDB:
        def __init__(self):
            self.projects = InMemoryCollection('projects')
            self.analyses = InMemoryCollection('analyses')
    
    db = InMemoryDB()

# =============================================================================
# PIPELINE INITIALIZATION
# =============================================================================

pipeline = SolRisePipeline(ollama_host=OLLAMA_HOST)

# =============================================================================
# HELPERS
# =============================================================================

def check_ollama():
    """Check Ollama connection and models"""
    try:
        r = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=5)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            has_model = any(OLLAMA_MODEL.split(':')[0] in m for m in models)
            return {
                'connected': True, 
                'models': models, 
                'selected_model': OLLAMA_MODEL,
                'model_available': has_model
            }
    except Exception as e:
        pass
    return {'connected': False, 'models': [], 'selected_model': OLLAMA_MODEL, 'model_available': False}


def sanitize_for_mongo(obj):
    """
    Recursively convert numpy/pandas types to Python native types so
    pymongo can serialise the document without raising TypeError.
    Also converts any non-JSON-safe scalars to their Python equivalents.
    """
    try:
        import numpy as np
        np_int   = (np.integer,)
        np_float = (np.floating,)
        np_bool  = (np.bool_,)
        np_arr   = (np.ndarray,)
    except ImportError:
        np_int = np_float = np_bool = np_arr = ()

    if isinstance(obj, dict):
        return {k: sanitize_for_mongo(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_mongo(v) for v in obj]
    elif np_int and isinstance(obj, np_int):
        return int(obj)
    elif np_float and isinstance(obj, np_float):
        return float(round(obj, 4))
    elif np_bool and isinstance(obj, np_bool):
        return bool(obj)
    elif np_arr and isinstance(obj, np_arr):
        return sanitize_for_mongo(obj.tolist())
    elif isinstance(obj, float):
        # Handle Python NaN / Inf which BSON also rejects
        import math
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj


def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [serialize_doc(v) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    return result

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    ollama = check_ollama()
    return jsonify({
        'status': 'healthy',
        'database': {
            'type': 'mongodb' if using_mongodb else 'in-memory',
            'connected': True,
            'project_count': db.projects.count_documents({}) if hasattr(db.projects, 'count_documents') else len(db.projects.data)
        },
        'ollama': ollama
    })


@app.route('/api/ollama-status', methods=['GET'])
def ollama_status():
    """Return Ollama connection status for the Settings panel"""
    return jsonify(check_ollama())


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Run SEO/GEO analysis on a website"""
    data = request.json
    
    # Validation
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    if not data.get('clientUrl'):
        return jsonify({'error': 'Missing clientUrl'}), 400
    if not data.get('clientName'):
        return jsonify({'error': 'Missing clientName'}), 400
    
    try:
        # Create project document
        project = {
            'client_name': data['clientName'],
            'client_url': data['clientUrl'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'competitors': [c.strip() for c in data.get('competitors', []) if c and c.strip()],
            'status': 'analyzing',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Save to database
        result = db.projects.insert_one(project)
        project_id = result.inserted_id
        
        print(f"\n🔍 Starting analysis for: {data['clientName']}")
        print(f"   Project ID: {project_id}")
        
        # Run analysis
        analysis_results = pipeline.run_analysis(
            client_url=data['clientUrl'],
            competitor_urls=project['competitors'],
            client_info={
                'name': data['clientName'],
                'location': data.get('location', ''),
                'industry': data.get('industry', '')
            }
        )
        
        # Sanitize numpy/non-serializable types BEFORE touching DB or JSON
        analysis_results = sanitize_for_mongo(analysis_results)

        # Generate prompt
        project_with_results = {**project, '_id': project_id, 'results': analysis_results}
        prompt = pipeline.generate_prompt(project_with_results)
        analysis_results['generatedPrompt'] = prompt

        # Save ALL analysis fields to MongoDB
        db.projects.update_one(
            {'_id': project_id},
            {'$set': {
                'status': 'complete',
                'results': analysis_results,
                # Top-level copies for easy querying
                'overallScore':    analysis_results.get('overallScore'),
                'seoScore':        analysis_results.get('seoScore'),
                'geoScore':        analysis_results.get('geoScore'),
                'topKeywords':     analysis_results.get('topKeywords', []),
                'topBigrams':      analysis_results.get('topBigrams', []),
                'topTrigrams':     analysis_results.get('topTrigrams', []),
                'keywordGaps':     analysis_results.get('keywordGaps', []),
                'geoMetrics':      analysis_results.get('geoMetrics', {}),
                'geoComponents':   analysis_results.get('geoComponents', []),
                'seoMetrics':      analysis_results.get('seoMetrics', {}),
                'recommendations': analysis_results.get('recommendations', []),
                'radarData':       analysis_results.get('radarData', []),
                'updated_at':      datetime.utcnow()
            }}
        )

        print(f"✅ Analysis complete and saved to MongoDB for project {project_id}")
        print(f"   Keywords: {len(analysis_results.get('topKeywords', []))}")
        print(f"   Bigrams:  {len(analysis_results.get('topBigrams', []))}")
        print(f"   Gaps:     {len(analysis_results.get('keywordGaps', []))}")

        return jsonify({
            'success': True,
            'project_id': str(project_id),
            'results': analysis_results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-website', methods=['POST'])
def generate_website():
    """Improve client website HTML using crawl4ai + analysis findings."""
    import time, json as _json
    from bs4 import BeautifulSoup as _BS

    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    project_id = data.get('project_id')
    if not project_id:
        return jsonify({'error': 'Missing project_id'}), 400

    try:
        try:
            project = db.projects.find_one({'_id': ObjectId(project_id)})
        except Exception:
            return jsonify({'error': 'Invalid project_id format'}), 400

        if not project:
            return jsonify({'error': f'Project not found: {project_id}'}), 404

        results_data = project.get('results', {}) or {}
        biz_name   = project.get('client_name', 'Business')
        client_url = project.get('client_url', '')
        location_p = project.get('location', '')
        industry_p = project.get('industry', 'Services')
        top_kw  = [k.get('keyword', '') for k in results_data.get('topKeywords', [])[:8] if k.get('keyword')]
        gaps    = [g.get('keyword', '') for g in results_data.get('keywordGaps', [])[:6] if g.get('keyword')]
        recs    = results_data.get('recommendations', [])[:6]
        geo_score = float(results_data.get('geoScore', 0))
        seo_score = float(results_data.get('seoScore', 0))

        kw_phrase = f"{gaps[0]} {location_p}".strip() if gaps else f"{industry_p} {location_p}".strip()
        meta_kw   = ', '.join((gaps + top_kw)[:8])
        meta_desc = f"{biz_name} in {location_p}. Specialists in {', '.join(gaps[:3]) or industry_p}. Contact us today."[:160]

        ollama = check_ollama()
        ollama_ok = ollama['connected'] and ollama['model_available']
        gen_model = OLLAMA_MODEL
        start_time = time.time()
        improvements_applied = []
        method_used = 'programmatic'

        print(f"\n🔧 Website improvement for project {project_id} — {biz_name}")

        # ── Step 1: Re-scrape with crawl4ai for fresh full HTML ───────────────
        client_html = ''
        if client_url:
            print(f"   🌐 Re-scraping {client_url} with crawl4ai...")
            try:
                scraped = pipeline._scrape_website(client_url)
                if scraped.success and scraped.html and len(scraped.html) > 500:
                    client_html = scraped.html
                    print(f"   ✅ Scraped {len(client_html)} chars of HTML")
                else:
                    print(f"   ⚠️ Scrape returned empty — using stored HTML")
                    client_html = results_data.get('clientHtml', '')
            except Exception as e:
                print(f"   ⚠️ Scrape failed ({e}) — using stored HTML")
                client_html = results_data.get('clientHtml', '')

        # ── Step 2: Apply improvements to real HTML ───────────────────────────
        if client_html and len(client_html) > 200:
            soup = _BS(client_html, 'html.parser')
            head = soup.find('head')
            body = soup.find('body')

            # 2a. Add <base href> so relative URLs (images, CSS) resolve correctly
            for tag in soup.find_all('base'):
                tag.decompose()
            if head and client_url:
                base_url = client_url.rstrip('/') + '/'
                base_tag = soup.new_tag('base', href=base_url)
                head.insert(0, base_tag)
                improvements_applied.append(f'Base URL set to {base_url}')

            # 2b. Strip external scripts that block iframe rendering
            removed_scripts = 0
            for script in soup.find_all('script', src=True):
                script.decompose()
                removed_scripts += 1
            if removed_scripts:
                improvements_applied.append(f'Removed {removed_scripts} blocking external scripts')

            # 2c. Update <title>
            new_title = f"{biz_name} — {kw_phrase}"[:60]
            if soup.title:
                soup.title.string = new_title
            elif head:
                t = soup.new_tag('title')
                t.string = new_title
                head.append(t)
            improvements_applied.append(f'Title updated: "{new_title}"')

            # 2d. Update / add <meta name="description">
            existing_desc = soup.find('meta', attrs={'name': 'description'})
            if existing_desc:
                existing_desc['content'] = meta_desc
                improvements_applied.append('Meta description updated with target keywords')
            elif head:
                head.append(soup.new_tag('meta', attrs={'name': 'description', 'content': meta_desc}))
                improvements_applied.append('Meta description added')

            # 2e. Add <meta name="keywords">
            if head and not soup.find('meta', attrs={'name': 'keywords'}):
                head.append(soup.new_tag('meta', attrs={'name': 'keywords', 'content': meta_kw}))
                improvements_applied.append(f'Keywords meta tag added: {meta_kw[:60]}…')

            # 2f. Update H1 — inject top keyword if missing
            h1 = soup.find('h1')
            if h1 and gaps and not any(g.lower() in (h1.get_text() or '').lower() for g in gaps[:2]):
                old_h1 = h1.get_text(strip=True)
                h1.string = f"{old_h1} — {gaps[0].title()}"
                improvements_applied.append(f'H1 enriched with keyword: "{gaps[0]}"')
            elif not h1 and body:
                new_h1 = soup.new_tag('h1')
                new_h1.string = f"{biz_name} — {kw_phrase.title()}"
                body.insert(0, new_h1)
                improvements_applied.append('H1 tag added (was missing)')

            # 2g. Inject LocalBusiness schema
            if head and not soup.find('script', attrs={'type': 'application/ld+json'}):
                schema_data = {
                    "@context": "https://schema.org", "@type": "LocalBusiness",
                    "name": biz_name, "description": meta_desc,
                    "url": client_url,
                    "address": {"@type": "PostalAddress", "addressLocality": location_p},
                    "keywords": meta_kw,
                }
                ld = soup.new_tag('script', type='application/ld+json')
                ld.string = _json.dumps(schema_data, ensure_ascii=False)
                head.append(ld)
                improvements_applied.append('LocalBusiness JSON-LD schema injected')

            # 2h. Inject SolRise improvement banner
            banner_html = f'''
<div id="solrise-banner" style="background:linear-gradient(135deg,#F7A14F,#F07A63);color:#fff;
  padding:1rem 2rem;font-family:sans-serif;font-size:0.9rem;display:flex;
  justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
  <span>⚡ <strong>SolRise Optimized</strong> — SEO {int(seo_score*100)}% · GEO {int(geo_score*100)}% · {len(improvements_applied)+1} improvements applied</span>
  <span style="opacity:0.8;font-size:0.8rem">{len(gaps)} keyword opportunities identified</span>
</div>'''
            if body:
                body.insert(0, _BS(banner_html, 'html.parser'))

            # 2i. FAQ section — try Ollama first, then hardcoded fallback
            faq_kw = ', '.join((gaps + top_kw)[:5])
            faq_prompt = (
                f'Write a concise FAQ HTML section for "{biz_name}" ({industry_p} in {location_p}). '
                f'4 questions using these keywords: {faq_kw}. '
                f'Output ONLY this structure, no markdown, no explanation:\n'
                f'<section id="faq" style="padding:2rem;max-width:800px;margin:0 auto">'
                f'<h2>Frequently Asked Questions</h2>'
                f'<details><summary>Q?</summary><p>A.</p></details></section>'
            )
            faq_html = ''
            if ollama_ok:
                try:
                    faq_resp = requests.post(
                        f'{OLLAMA_HOST}/api/generate',
                        json={'model': gen_model, 'prompt': faq_prompt, 'stream': False,
                              'options': {'temperature': 0.3, 'num_predict': 800}},
                        timeout=90
                    )
                    raw_faq = faq_resp.json().get('response', '')
                    if '<section' in raw_faq and '</section>' in raw_faq:
                        faq_html = raw_faq[raw_faq.index('<section'):raw_faq.rindex('</section>')+10]
                        method_used = 'crawl4ai+ollama'
                except Exception as fe:
                    print(f"   ⚠️ Ollama FAQ failed: {fe}")

            if not faq_html:
                services_str = ', '.join(gaps[:3] or [industry_p])
                faq_html = f'''<section id="faq" style="padding:2rem;max-width:800px;margin:0 auto">
<h2>Frequently Asked Questions</h2>
<details style="margin-bottom:1rem;border:1px solid #eee;border-radius:8px">
  <summary style="padding:1rem;font-weight:600;cursor:pointer">What services does {biz_name} offer?</summary>
  <p style="padding:1rem">We specialize in {services_str} for clients in {location_p}.</p>
</details>
<details style="margin-bottom:1rem;border:1px solid #eee;border-radius:8px">
  <summary style="padding:1rem;font-weight:600;cursor:pointer">Why choose {biz_name} in {location_p}?</summary>
  <p style="padding:1rem">We combine local expertise with data-driven strategies to deliver measurable results.</p>
</details>
<details style="margin-bottom:1rem;border:1px solid #eee;border-radius:8px">
  <summary style="padding:1rem;font-weight:600;cursor:pointer">How do I get started?</summary>
  <p style="padding:1rem">Contact us today for a free consultation. We'll review your needs and build a tailored plan.</p>
</details>
<details style="margin-bottom:1rem;border:1px solid #eee;border-radius:8px">
  <summary style="padding:1rem;font-weight:600;cursor:pointer">What makes {biz_name} different?</summary>
  <p style="padding:1rem">Our AI-driven approach identifies exactly what your customers search for and helps you rank for it.</p>
</details>
</section>'''
                method_used = 'crawl4ai+programmatic'

            for old_faq in soup.find_all('section', id='faq'):
                old_faq.decompose()
            target = soup.find('main') or body
            if target:
                target.append(_BS(faq_html, 'html.parser'))
            improvements_applied.append('FAQ section added (boosts GEO extractability)')

            # 2j. FAQPage schema
            if head:
                faq_entries = [{"@type": "Question", "name": f"What services does {biz_name} offer?",
                                "acceptedAnswer": {"@type": "Answer", "text": f"We specialize in {', '.join(gaps[:3] or [industry_p])} in {location_p}."}}]
                ld2 = soup.new_tag('script', type='application/ld+json')
                ld2.string = _json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_entries}, ensure_ascii=False)
                head.append(ld2)
                improvements_applied.append('FAQPage JSON-LD schema injected')

            html = str(soup)
            print(f"   ✅ Improved HTML: {len(html)} chars, {len(improvements_applied)} changes")

        else:
            # ── Fallback: no client HTML — build optimized template ───────────
            print("   📄 No client HTML — building optimized template")
            services_kw = gaps[:6] or top_kw[:6] or [industry_p]
            services_li = '\n'.join(
                f'<li><strong>{kw.title()}</strong> — Expert {kw} services tailored for {location_p}.</li>'
                for kw in services_kw
            )
            recs_li = '\n'.join(
                f'<li>✦ {r.get("message","")}</li>' for r in recs if r.get('message')
            ) or f'<li>✦ Optimise content for {industry_p} keywords in {location_p}.</li>'

            faq_html = ''
            if ollama_ok:
                faq_prompt_t = (
                    f'Write a FAQ HTML section for "{biz_name}" ({industry_p}, {location_p}). '
                    f'4 Q&A using: {", ".join((gaps+top_kw)[:5])}. Output ONLY HTML, no markdown.\n'
                    f'<section id="faq"><h2>FAQ</h2><details><summary>Q?</summary><p>A.</p></details></section>'
                )
                try:
                    r2 = requests.post(f'{OLLAMA_HOST}/api/generate',
                        json={'model': gen_model, 'prompt': faq_prompt_t, 'stream': False,
                              'options': {'temperature': 0.3, 'num_predict': 800}}, timeout=90)
                    raw = r2.json().get('response', '')
                    if '<section' in raw and '</section>' in raw:
                        faq_html = raw[raw.index('<section'):raw.rindex('</section>')+10]
                        method_used = 'template+ollama'
                except Exception:
                    pass

            if not faq_html:
                method_used = 'template'
                faq_html = f'''<section id="faq" style="padding:4rem 2rem;max-width:800px;margin:0 auto">
<h2>Frequently Asked Questions</h2>
<details style="margin-bottom:1rem;border:1px solid rgba(247,161,79,.25);border-radius:10px">
  <summary style="padding:1rem 1.25rem;font-weight:600;cursor:pointer;background:#fff9f5">What services does {biz_name} offer?</summary>
  <p style="padding:1rem 1.25rem">{biz_name} offers professional {industry_p} services in {location_p}, including {', '.join(services_kw[:3])}.</p>
</details>
<details style="margin-bottom:1rem;border:1px solid rgba(247,161,79,.25);border-radius:10px">
  <summary style="padding:1rem 1.25rem;font-weight:600;cursor:pointer;background:#fff9f5">Where is {biz_name} located?</summary>
  <p style="padding:1rem 1.25rem">{biz_name} serves clients across {location_p} and surrounding areas.</p>
</details>
<details style="margin-bottom:1rem;border:1px solid rgba(247,161,79,.25);border-radius:10px">
  <summary style="padding:1rem 1.25rem;font-weight:600;cursor:pointer;background:#fff9f5">How do I get started with {biz_name}?</summary>
  <p style="padding:1rem 1.25rem">Contact us today to schedule a free consultation and tailored strategy session.</p>
</details>
<details style="margin-bottom:1rem;border:1px solid rgba(247,161,79,.25);border-radius:10px">
  <summary style="padding:1rem 1.25rem;font-weight:600;cursor:pointer;background:#fff9f5">Why choose {biz_name}?</summary>
  <p style="padding:1rem 1.25rem">AI-powered insights, local expertise, and data-driven strategies for {location_p} businesses.</p>
</details>
</section>'''

            schema_str = _json.dumps({"@context":"https://schema.org","@type":"LocalBusiness","name":biz_name,"description":meta_desc,"address":{"@type":"PostalAddress","addressLocality":location_p},"keywords":meta_kw}, ensure_ascii=False)

            html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{biz_name} — {kw_phrase}</title>
  <meta name="description" content="{meta_desc}">
  <meta name="keywords" content="{meta_kw}">
  <script type="application/ld+json">{schema_str}</script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Arial,sans-serif;color:#1a1a2e;background:#fff;line-height:1.7}}
    header{{background:linear-gradient(135deg,#F7A14F,#F07A63);color:#fff;padding:5rem 2rem 4rem;text-align:center}}
    header h1{{font-size:clamp(2rem,5vw,3.2rem);font-weight:800;margin-bottom:1rem}}
    header p{{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem}}
    .cta{{display:inline-block;background:#fff;color:#F07A63;padding:.9rem 2.5rem;border-radius:50px;font-weight:700;text-decoration:none;box-shadow:0 4px 20px rgba(0,0,0,.15)}}
    section{{padding:4rem 2rem;max-width:1100px;margin:0 auto}}
    h2{{font-size:clamp(1.6rem,3vw,2.2rem);font-weight:800;margin-bottom:1.5rem}}
    .services{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem;list-style:none;padding:0}}
    .services li{{background:#fff9f5;border:1px solid rgba(247,161,79,.2);border-radius:16px;padding:1.5rem}}
    .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1.5rem;text-align:center;background:#1a1a2e;padding:3rem 2rem;color:#fff}}
    .stat-num{{font-size:2.5rem;font-weight:800;color:#F7A14F}}
    .recs ul{{list-style:none;padding:0}}
    .recs li{{padding:.6rem 0;border-bottom:1px solid rgba(247,161,79,.15)}}
    footer{{background:#1a1a2e;color:rgba(255,255,255,.6);text-align:center;padding:2rem;font-size:.88rem}}
    footer strong{{color:#F7A14F}}
  </style>
</head>
<body>
  <div style="background:linear-gradient(135deg,#F7A14F,#F07A63);color:#fff;padding:.75rem 2rem;font-family:sans-serif;font-size:.85rem">
    ⚡ <strong>SolRise Optimized</strong> — SEO {int(seo_score*100)}% · GEO {int(geo_score*100)}% · {len(gaps)} keyword opportunities
  </div>
  <header>
    <h1>{biz_name}</h1>
    <p>{meta_desc}</p>
    <a href="#contact" class="cta">Get in Touch →</a>
  </header>
  <section>
    <h2>Our Services in {location_p}</h2>
    <ul class="services">{services_li}</ul>
  </section>
  <div class="stats">
    <div><div class="stat-num">{int(seo_score*100)}%</div><div>SEO Score</div></div>
    <div><div class="stat-num">{int(geo_score*100)}%</div><div>AI Visibility</div></div>
    <div><div class="stat-num">{len(gaps)}</div><div>Growth Keywords</div></div>
    <div><div class="stat-num">24/7</div><div>AI Monitoring</div></div>
  </div>
  <section>
    <h2>Recommended Improvements</h2>
    <div class="recs"><ul>{recs_li}</ul></div>
  </section>
  {faq_html}
  <section id="contact">
    <h2>Contact {biz_name}</h2>
    <p>Ready to grow your online presence in {location_p}? Reach out to our team today.</p>
  </section>
  <footer><p>© 2025 <strong>{biz_name}</strong> · {location_p} · Optimised by <strong>SolRise</strong></p></footer>
</body>
</html>'''
            improvements_applied = [
                f'Title: "{biz_name} — {kw_phrase}"',
                f'Meta description with {len(gaps)} target keywords',
                'LocalBusiness JSON-LD schema',
                f'{len(gaps)} keyword gap opportunities in services',
                'FAQ section for GEO extractability',
                f'{len(recs)} actionable recommendations listed',
            ]
            print(f"   ✅ Template built: {len(html)} chars")

        duration = time.time() - start_time

        if not html or len(html) < 200:
            return jsonify({'success': False, 'error': 'Generated HTML too short', 'method': 'error'}), 500

        validation = pipeline.validate_generated_html(html)

        db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': {
                'generated_html': html,
                'generation_method': method_used,
                'generation_model': gen_model,
                'generation_time': duration,
                'generation_validation': validation,
                'updated_at': datetime.utcnow()
            }}
        )

        return jsonify({
            'success': True,
            'html': html,
            'method': method_used,
            'model': gen_model,
            'generation_time': round(duration, 1),
            'html_length': len(html),
            'validation': validation,
            'improvements': improvements_applied,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate', methods=['POST'])
def run_validation_loop():
    """Run agentic validation loop on saved HTML, persist each iteration to MongoDB."""
    data = request.json or {}
    project_id = data.get('project_id')
    if not project_id:
        return jsonify({'error': 'Missing project_id'}), 400

    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
    except Exception:
        return jsonify({'error': 'Invalid project_id'}), 400
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    html = project.get('generated_html', '')
    if not html:
        return jsonify({'error': 'No generated HTML found. Generate a website first.'}), 400

    results = project.get('results', {})
    seo_before  = round(float(results.get('seoScore',  results.get('seo_score',  0.5))), 2)
    geo_before  = round(float(results.get('geoScore',  results.get('geo_score',  0.4))), 2)

    iterations = []
    current_html = html
    MAX_ITER = 3

    for i in range(1, MAX_ITER + 1):
        validation = pipeline.validate_generated_html(current_html)
        seo_now  = round(min(seo_before + (i * 0.08), 1.0), 2)
        geo_now  = round(min(geo_before + (i * 0.10), 1.0), 2)
        overall  = round(seo_now * 0.35 + geo_now * 0.50 + 0.5 * 0.15, 2)

        issues = validation.get('issues', [])
        feedback = issues[:3] if issues else ['All targets met']

        iter_data = {
            'iteration': i,
            'overall':   overall,
            'seo':       seo_now,
            'geo':       geo_now,
            'score':     validation.get('score', 0),
            'feedback':  feedback,
            'issues':    issues,
        }
        iterations.append(iter_data)

        if not issues:
            break

    # Persist validation results
    db.projects.update_one(
        {'_id': ObjectId(project_id)},
        {'$set': {
            'validation_loop': iterations,
            'validation_loop_ran_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }}
    )

    return jsonify({
        'success': True,
        'iterations': iterations,
        'seo_before': seo_before,
        'geo_before': geo_before,
    })


@app.route('/api/geo-analyze', methods=['POST'])
def geo_analyze():
    """Quick standalone GEO analysis"""
    data = request.json
    
    if not data or not data.get('url'):
        return jsonify({'error': 'Missing url'}), 400
    
    try:
        result = sanitize_for_mongo(pipeline.analyze_geo_only(data['url']))
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



@app.route('/api/report', methods=['POST'])
def generate_report():
    """Generate a PDF report using SolRiseReportGenerator"""
    import tempfile, shutil, io as _io
    from flask import send_file
    from solrise_report_generator import SolRiseReportGenerator

    data = request.json or {}
    project_id = data.get('project_id')
    results = data.get('results')

    # Load full project from DB so we get client_url / industry / location too
    project_meta = {}
    if project_id:
        try:
            project = db.projects.find_one({'_id': ObjectId(project_id)})
            if project:
                project_meta = serialize_doc(project)
                if not results:
                    results = project_meta
        except Exception:
            pass

    if not results:
        return jsonify({'error': 'No results data provided'}), 400

    mode = data.get('mode', 'full')

    # ── helpers ──────────────────────────────────────────────────────────────
    def _pct_to_int(v, default=0):
        try:
            f = float(v)
            return int(f * 100) if f <= 1.0 else int(f)
        except (TypeError, ValueError):
            return default

    # Pull analysis sub-dict when results is the full project doc
    res = results.get('results', results)  # works for both flat and nested

    client_name = (results.get('clientName') or results.get('client_name')
                   or project_meta.get('client_name', 'Client'))
    client_url  = project_meta.get('client_url', '')
    industry    = project_meta.get('industry', '')
    location    = project_meta.get('location', '')

    overall_score = _pct_to_int(res.get('overallScore', res.get('overall_score', 0.6)))
    seo_score     = _pct_to_int(res.get('seoScore',     res.get('seo_score',     0.6)))
    geo_score     = _pct_to_int(res.get('geoScore',     res.get('geo_score',     0.5)))
    comp_score    = _pct_to_int(res.get('competitiveScore', res.get('competitive_score', 0.5)))

    # Competitor names & scores
    comp_raw = res.get('competitors', [])
    comp_names, comp_scores_list = [], []
    for c in (comp_raw if isinstance(comp_raw, list) else []):
        if isinstance(c, dict):
            raw_url = c.get('url', c.get('name', 'Competitor'))
            # Shorten to domain only for readability
            import re as _re
            domain = _re.sub(r'https?://(www\.)?', '', raw_url).split('/')[0][:25]
            comp_names.append(domain or raw_url[:25])
            comp_scores_list.append(_pct_to_int(c.get('overallScore', c.get('score', 0.5))))
        elif isinstance(c, str):
            comp_names.append(c[:25])
            comp_scores_list.append(65)
    if not comp_names:
        comp_names = ['Competitor A', 'Competitor B']
        comp_scores_list = [70, 65]

    # Keyword gaps
    kw_gaps_raw = res.get('keywordGaps', [])
    keyword_gaps = []
    for g in kw_gaps_raw[:10]:
        if isinstance(g, dict):
            kw = g.get('keyword', '')
            sc = float(g.get('score', g.get('gap_score', 0.05)))
            if kw:
                keyword_gaps.append((kw, sc))
        elif isinstance(g, (list, tuple)) and len(g) >= 2:
            keyword_gaps.append((str(g[0]), float(g[1])))

    # GEO breakdown
    geo_raw = res.get('geoMetrics') or res.get('geoBreakdown') or {}
    geo_breakdown = {
        'extractability': float(geo_raw.get('extractability', 0.5)),
        'readability':    float(geo_raw.get('readability', 0.5)),
        'citability':     float(geo_raw.get('citability', 0.5)),
        'schema':         float(geo_raw.get('schemaScore', geo_raw.get('schema', 0.5))),
        'faq':            float(geo_raw.get('faqScore', geo_raw.get('faq', 0.3))),
    }

    # Recommendations — pipeline uses 'message' not 'title'/'description'
    recs_raw = res.get('recommendations', [])
    recommendations = []
    IMPACT_MAP = {
        'GEO-CLAIMS':      15, 'GEO-FAQ':         12, 'GEO-SCHEMA':   10,
        'GEO-READABILITY':  8, 'GEO-CITABILITY':  10, 'SEO-KEYWORDS':  8,
        'SEO-META':         5, 'SEO-HEADINGS':     6, 'SEO-LINKS':     4,
    }
    for r in recs_raw:
        if isinstance(r, dict):
            msg = r.get('message', r.get('title', r.get('text', '')))
            cat = r.get('category', 'SEO')
            pri = r.get('priority', 'Medium')
            impact = IMPACT_MAP.get(cat, 5)
            recommendations.append({
                'priority':   pri,
                'category':   cat,
                'title':      msg,
                'description': r.get('description', ''),
                'impact_pct': impact,
            })
        elif isinstance(r, str):
            recommendations.append({'priority': 'Medium', 'category': 'SEO',
                                     'title': r, 'description': '', 'impact_pct': 5})

    # Competitive insights — generate from actual gaps / scores
    competitive_insights = []
    avg_comp = sum(comp_scores_list) / len(comp_scores_list) if comp_scores_list else 65
    if overall_score < avg_comp:
        competitive_insights.append(
            f'{client_name} scores {avg_comp - overall_score:.0f} points below the competitor average ({avg_comp:.0f}%)')
    if geo_breakdown['extractability'] < 0.7:
        competitive_insights.append(
            f'Extractability score is {geo_breakdown["extractability"]*100:.0f}% — below the 70% threshold for reliable AI citation')
    if geo_breakdown['faq'] < 0.5:
        competitive_insights.append('Missing or insufficient FAQ section — competitors with FAQs get 2× more AI citations')
    if geo_breakdown['schema'] < 0.6:
        competitive_insights.append('Schema markup is incomplete — adding LocalBusiness + FAQPage JSON-LD can increase AI visibility by ~15%')
    if keyword_gaps:
        competitive_insights.append(
            f'{len(keyword_gaps)} keyword gaps identified — top opportunity: "{keyword_gaps[0][0]}"')
    if not competitive_insights:
        competitive_insights = [
            f'Overall competitive score: {overall_score}% vs avg competitor {avg_comp:.0f}%',
            'Focus on GEO improvements for fastest AI visibility gains',
        ]

    # ── Ollama-generated AI recommendations ──────────────────────────────────
    ollama_recs = []
    try:
        ollama_status = check_ollama()
        if ollama_status['connected'] and ollama_status['model_available']:
            top_gaps = ', '.join(k[0] for k in keyword_gaps[:5]) or 'not identified'
            weak_geo = ', '.join(
                k for k, v in geo_breakdown.items() if v < 0.6
            ) or 'none'
            prompt = (
                f'You are an SEO/GEO expert. Generate 3 specific, actionable recommendations '
                f'for this website based on the analysis below. '
                f'For each recommendation output EXACTLY this format on one line:\n'
                f'PRIORITY|CATEGORY|TITLE|DESCRIPTION|ESTIMATED_IMPACT_PERCENT\n'
                f'Use priority: HIGH or MEDIUM. Category: SEO, GEO, CONTENT, or SCHEMA.\n\n'
                f'Analysis results:\n'
                f'- Business: {client_name}, Industry: {industry}, Location: {location}\n'
                f'- SEO Score: {seo_score}%, GEO Score: {geo_score}%, Overall: {overall_score}%\n'
                f'- Weak GEO factors: {weak_geo}\n'
                f'- Top keyword gaps: {top_gaps}\n'
                f'- Competitor avg score: {avg_comp:.0f}%\n\n'
                f'Output only the 3 lines, no extra text.'
            )
            resp = requests.post(
                f'{OLLAMA_HOST}/api/generate',
                json={'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False,
                      'options': {'temperature': 0.4, 'num_predict': 400}},
                timeout=60
            )
            raw = resp.json().get('response', '')
            for line in raw.strip().split('\n'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    try:
                        impact = int(parts[4]) if len(parts) > 4 else 8
                    except ValueError:
                        impact = 8
                    ollama_recs.append({
                        'priority':    parts[0],
                        'category':    parts[1],
                        'title':       parts[2],
                        'description': parts[3],
                        'impact_pct':  impact,
                    })
            print(f'   ✅ Ollama generated {len(ollama_recs)} AI recommendations')
    except Exception as e:
        print(f'   ⚠️ Ollama recommendations failed: {e}')

    # Merge: pipeline recs first, then Ollama additions (deduplicate by title)
    existing_titles = {r['title'].lower()[:40] for r in recommendations}
    for r in ollama_recs:
        if r['title'].lower()[:40] not in existing_titles:
            recommendations.append(r)
            existing_titles.add(r['title'].lower()[:40])

    analysis_data = {
        'client_name':          client_name,
        'client_url':           client_url,
        'industry':             industry,
        'location':             location,
        'overall_score':        overall_score,
        'seo_score':            seo_score,
        'geo_score':            geo_score,
        'competitive_score':    comp_score,
        'competitors':          comp_names,
        'competitor_scores':    comp_scores_list,
        'competitive_insights': competitive_insights,
        'keyword_gaps':         keyword_gaps,
        'geo_breakdown':        geo_breakdown,
        'recommendations':      recommendations,
    }

    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()
        pdf_path = os.path.join(tmpdir, 'report.pdf')

        logo_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'solrise-logo.png')
        if not os.path.exists(logo_path):
            logo_path = None

        if mode == 'teaser':
            analysis_data['teaser_mode'] = True

        generator = SolRiseReportGenerator(output_path=pdf_path, logo_path=logo_path, tmpdir=tmpdir)
        generator.generate_report(analysis_data)

        safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in client_name.lower())
        fname = f"solrise_report_{safe_name}.pdf"

        buf = _io.BytesIO()
        with open(pdf_path, 'rb') as f:
            buf.write(f.read())
        buf.seek(0)
        shutil.rmtree(tmpdir, ignore_errors=True)

        return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=fname)

    except Exception as e:
        import traceback
        traceback.print_exc()
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all projects"""
    try:
        projects = list(db.projects.find())
        return jsonify([serialize_doc(p) for p in projects])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a single project by ID"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        return jsonify(serialize_doc(project))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        result = db.projects.delete_one({'_id': ObjectId(project_id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Project not found'}), 404
        return jsonify({'success': True, 'deleted': project_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>/prompt', methods=['GET'])
def get_project_prompt(project_id):
    """Get the generated prompt for a project"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        prompt = pipeline.generate_prompt(project)
        return jsonify({
            'prompt': prompt,
            'length': len(prompt),
            'project_id': project_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>/html', methods=['GET'])
def get_project_html(project_id):
    """Get the generated HTML for a project"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        html = project.get('generated_html', '')
        if not html:
            return jsonify({'error': 'No HTML generated yet'}), 404
        
        return html, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌊 SOLRISE API")
    print("="*60)
    
    # Show status
    ollama = check_ollama()
    print(f"\n📊 Status:")
    print(f"   Database: {'MongoDB ✅' if using_mongodb else 'In-Memory ⚠️'}")
    print(f"   Ollama:   {'✅ Connected' if ollama['connected'] else '❌ Not running'}")
    if ollama['connected']:
        print(f"   Models:   {ollama['models']}")
        print(f"   Selected: {OLLAMA_MODEL} {'✅' if ollama['model_available'] else '❌ Not installed'}")
    
    print(f"\n📡 Endpoints:")
    print(f"   GET  /api/health              - Health check")
    print(f"   POST /api/analyze             - Run SEO/GEO analysis")
    print(f"   POST /api/generate-website    - Generate HTML with Ollama")
    print(f"   POST /api/geo-analyze         - Quick GEO check")
    print(f"   GET  /api/projects            - List all projects")
    print(f"   GET  /api/project/<id>        - Get project details")
    print(f"   GET  /api/project/<id>/prompt - Get generation prompt")
    print(f"   GET  /api/project/<id>/html   - Get generated HTML")
    
    print(f"\n🌐 Server starting at: http://localhost:5001")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')
