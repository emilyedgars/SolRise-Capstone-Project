"""
Atlantic Digital - Flask API v5
===============================
- Proper MongoDB integration
- Fixed routing
- Better error handling
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from bson import ObjectId
from bson.json_util import dumps
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from pipeline import AtlanticDigitalPipeline

app = Flask(__name__)
CORS(app)

# =============================================================================
# CONFIGURATION
# =============================================================================

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')

# Use smaller, faster model for generation
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2:1.5b')  # Much faster than 7b

# =============================================================================
# DATABASE SETUP
# =============================================================================

db = None
using_mongodb = False

try:
    from pymongo import MongoClient
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Force connection check
    db = client.atlantic_digital
    
    # Create indexes for better performance
    db.projects.create_index('client_name')
    db.projects.create_index('created_at')
    
    using_mongodb = True
    print(f"✅ MongoDB connected: {MONGODB_URI}")
    print(f"   Using Database: atlantic_digital")
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

pipeline = AtlanticDigitalPipeline(ollama_host=OLLAMA_HOST)

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
        
        # Generate prompt
        project_with_results = {**project, '_id': project_id, 'results': analysis_results}
        prompt = pipeline.generate_prompt(project_with_results)
        analysis_results['generatedPrompt'] = prompt
        
        # Update project with results
        db.projects.update_one(
            {'_id': project_id},
            {'$set': {
                'status': 'complete',
                'results': analysis_results,
                'updated_at': datetime.utcnow()
            }}
        )
        
        print(f"✅ Analysis complete for project {project_id}")
        
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
    """Generate optimized website HTML using Ollama"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    project_id = data.get('project_id')
    if not project_id:
        return jsonify({'error': 'Missing project_id'}), 400
    
    try:
        # Find project
        try:
            project = db.projects.find_one({'_id': ObjectId(project_id)})
        except:
            return jsonify({'error': 'Invalid project_id format'}), 400
        
        if not project:
            return jsonify({'error': f'Project not found: {project_id}'}), 404
        
        # Get or generate prompt
        custom_prompt = data.get('custom_prompt')
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = pipeline.generate_prompt(project)
        
        # Get client HTML for improvement mode
        client_html = project.get('results', {}).get('clientHtml', '') if isinstance(project.get('results'), dict) else ''

        print(f"\n🤖 Generating website for project: {project_id}")
        print(f"   Prompt length: {len(prompt)} chars")
        print(f"   Client HTML available: {bool(client_html)} ({len(client_html)} chars)")

        # Check Ollama
        ollama = check_ollama()
        
        if not ollama['connected']:
            return jsonify({
                'success': False,
                'error': 'Ollama not connected. Start with: ollama serve',
                'html': '',
                'method': 'error'
            }), 503
        
        gen_model = OLLAMA_MODEL
        if not ollama['model_available']:
            return jsonify({
                'success': False,
                'error': f"Model {OLLAMA_MODEL} not found. Install with: ollama pull {OLLAMA_MODEL}",
                'html': '',
                'method': 'error'
            }), 503

        print(f"   Using model: {gen_model}")

        import time, json as _json
        from bs4 import BeautifulSoup as _BS
        start_time = time.time()

        # ── Programmatic patching when client HTML is available ───────────────
        if client_html:
            results_data = project.get('results', {})
            top_kw  = [k.get('keyword','') for k in results_data.get('topKeywords', [])[:6]]
            gaps    = [g.get('keyword','') for g in results_data.get('keywordGaps', [])[:5]]
            biz_name   = project.get('client_name', 'Business')
            location_p = project.get('location', '')
            industry_p = project.get('industry', '')

            soup = _BS(client_html, 'html.parser')

            # 1. Update <title>
            kw_phrase = f"{gaps[0]} {location_p}".strip() if gaps else biz_name
            new_title = f"{biz_name} — {kw_phrase}"[:60]
            if soup.title:
                soup.title.string = new_title
            else:
                head = soup.find('head') or soup.new_tag('head')
                t = soup.new_tag('title'); t.string = new_title; head.append(t)

            # 2. Update / add <meta name="description">
            kw_str = ', '.join(gaps[:3]) if gaps else industry_p
            meta_desc = f"{biz_name} in {location_p}. Expert in {kw_str}. Contact us today."[:160]
            existing_desc = soup.find('meta', attrs={'name': 'description'})
            if existing_desc:
                existing_desc['content'] = meta_desc
            else:
                head = soup.find('head')
                if head:
                    head.append(soup.new_tag('meta', attrs={'name': 'description', 'content': meta_desc}))

            # 3. Inject JSON-LD LocalBusiness schema
            head = soup.find('head')
            if head and not soup.find('script', attrs={'type': 'application/ld+json'}):
                schema = {
                    "@context": "https://schema.org",
                    "@type": "LocalBusiness",
                    "name": biz_name,
                    "description": meta_desc,
                    "address": {"@type": "PostalAddress", "addressLocality": location_p},
                    "keywords": ', '.join(top_kw[:5]),
                }
                ld = soup.new_tag('script', type='application/ld+json')
                ld.string = _json.dumps(schema, ensure_ascii=False)
                head.append(ld)

            # 4. FAQ — try Claude API first, fall back to Ollama
            faq_kw = ', '.join((gaps + top_kw)[:5])
            faq_prompt = (
                f'Write a concise FAQ section in HTML for "{biz_name}" ({industry_p}, {location_p}). '
                f'Include exactly 4 questions and answers naturally using these keywords: {faq_kw}. '
                f'Use this exact structure with no extra text:\n'
                f'<section id="faq"><h2>Preguntas Frecuentes</h2>'
                f'<details><summary>Q1?</summary><p>A1.</p></details>'
                f'<details><summary>Q2?</summary><p>A2.</p></details>'
                f'<details><summary>Q3?</summary><p>A3.</p></details>'
                f'<details><summary>Q4?</summary><p>A4.</p></details></section>'
            )

            faq_html = ''
            anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
            method_used = 'programmatic'

            if anthropic_key:
                try:
                    import anthropic as _anthropic
                    _claude = _anthropic.Anthropic(api_key=anthropic_key)
                    print("   🤖 Using Claude API for FAQ generation...")
                    with _claude.messages.stream(
                        model='claude-opus-4-6',
                        max_tokens=900,
                        messages=[{'role': 'user', 'content': faq_prompt}]
                    ) as stream:
                        raw_faq = stream.get_final_message().content[0].text
                    if '<section' in raw_faq:
                        faq_html = raw_faq[raw_faq.index('<section'):raw_faq.rindex('</section>')+10]
                    method_used = 'programmatic+claude'
                    print(f"   ✅ Claude FAQ: {len(faq_html)} chars")
                except Exception as e:
                    print(f"   ⚠️  Claude API FAQ failed ({e}), trying Ollama...")

            if not faq_html:
                try:
                    faq_resp = requests.post(
                        f'{OLLAMA_HOST}/api/generate',
                        json={'model': gen_model, 'prompt': faq_prompt, 'stream': False,
                              'options': {'temperature': 0.3, 'num_predict': 600}},
                        timeout=90
                    )
                    raw_faq = faq_resp.json().get('response', '')
                    if '<section' in raw_faq:
                        faq_html = raw_faq[raw_faq.index('<section'):raw_faq.rindex('</section>')+10]
                    method_used = 'programmatic+ollama'
                except Exception:
                    pass  # FAQ optional

            # 5. Inject FAQ into page
            if faq_html:
                for old in soup.find_all('section', id='faq'):
                    old.decompose()
                target = soup.find('main') or soup.find('body')
                if target:
                    target.append(_BS(faq_html, 'html.parser'))
                # FAQPage schema
                head = soup.find('head')
                if head:
                    ld2 = soup.new_tag('script', type='application/ld+json')
                    ld2.string = _json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":f"FAQ about {biz_name}","acceptedAnswer":{"@type":"Answer","text":f"Contact {biz_name} for more information."}}]}, ensure_ascii=False)
                    head.append(ld2)

            html = str(soup)
            duration = time.time() - start_time
            print(f"   ✅ Programmatic improvement done: {len(html)} chars in {duration:.1f}s (method: {method_used})")

        else:
            # ── No client HTML: generate from scratch with Ollama ─────────────
            try:
                resp = requests.post(
                    f'{OLLAMA_HOST}/api/generate',
                    json={'model': gen_model, 'prompt': prompt, 'stream': False,
                          'options': {'temperature': 0.4, 'num_predict': 8000}},
                    timeout=180
                )
                resp.raise_for_status()
                html = resp.json().get('response', '')
            except requests.exceptions.Timeout:
                return jsonify({'success': False, 'error': 'Ollama timeout', 'html': '', 'method': 'error'}), 504
            except requests.exceptions.RequestException as e:
                return jsonify({'success': False, 'error': f'Ollama error: {e}', 'html': '', 'method': 'error'}), 502

            duration = time.time() - start_time
            if '```html' in html:
                html = html.split('```html')[1].split('```')[0]
            elif '```' in html:
                parts = html.split('```')
                if len(parts) >= 2:
                    html = parts[1]
            html = html.strip()
            method_used = 'ollama'

        if not html or len(html) < 100:
            return jsonify({'success': False, 'error': 'Generated HTML too short or empty', 'html': html, 'method': 'error'}), 500

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
            'model': OLLAMA_MODEL,
            'generation_time': round(duration, 1),
            'prompt_length': len(prompt),
            'html_length': len(html),
            'validation': validation
        })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/geo-analyze', methods=['POST'])
def geo_analyze():
    """Quick standalone GEO analysis"""
    data = request.json
    
    if not data or not data.get('url'):
        return jsonify({'error': 'Missing url'}), 400
    
    try:
        result = pipeline.analyze_geo_only(data['url'])
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/report', methods=['POST'])
def generate_report():
    """Generate a PDF report from analysis results (accepts JSON data directly)"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io

    data = request.json or {}
    project_id = data.get('project_id')
    results = data.get('results')

    # Load from DB if project_id provided
    if project_id and not results:
        try:
            project = db.projects.find_one({'_id': ObjectId(project_id)})
            if project:
                results = serialize_doc(project)
        except Exception:
            pass

    if not results:
        return jsonify({'error': 'No results data provided'}), 400

    mode = data.get('mode', 'full')  # 'full' or 'teaser'

    # ── helpers ──────────────────────────────────────────────────────────────
    def pct(v):
        try: return f"{float(v)*100:.0f}%"
        except: return "N/A"

    def score_color(v):
        try:
            f = float(v)
            if f >= 0.7: return colors.HexColor('#27ae60')
            if f >= 0.5: return colors.HexColor('#f39c12')
            return colors.HexColor('#e74c3c')
        except:
            return colors.HexColor('#95a5a6')

    BRAND   = colors.HexColor('#1a2332')
    TEAL    = colors.HexColor('#4ECDC4')
    LIGHT   = colors.HexColor('#ecf0f1')
    SUBTLE  = colors.HexColor('#7f8c8d')

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    h1  = ParagraphStyle('h1',  fontSize=22, fontName='Helvetica-Bold', textColor=BRAND,   spaceBefore=10, spaceAfter=12, alignment=TA_CENTER)
    h2  = ParagraphStyle('h2',  fontSize=13, fontName='Helvetica-Bold', textColor=BRAND,   spaceBefore=14, spaceAfter=6)
    sub = ParagraphStyle('sub', fontSize=10, fontName='Helvetica',      textColor=SUBTLE,  alignment=TA_CENTER, spaceBefore=6, spaceAfter=18)
    body= ParagraphStyle('body',fontSize=9,  fontName='Helvetica',      textColor=BRAND,   spaceAfter=3,  leading=14)
    tip = ParagraphStyle('tip', fontSize=8,  fontName='Helvetica-Oblique', textColor=SUBTLE, spaceAfter=2)

    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("ATLANTIC DIGITAL", ParagraphStyle('brand', fontSize=12, fontName='Helvetica-Bold', textColor=TEAL, alignment=TA_CENTER, spaceAfter=4)))
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph("SEO / GEO Analysis Report", h1))
    client_name = results.get('clientName', results.get('client_name', 'Client'))
    story.append(Paragraph(f"{client_name}  ·  {datetime.utcnow().strftime('%B %d, %Y')}", sub))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=24))

    # ── Score cards ───────────────────────────────────────────────────────────
    story.append(Paragraph("Performance Scores", h2))
    scores = [
        ('Overall Score',      results.get('overallScore', 0)),
        ('SEO Score',          results.get('seoScore', 0)),
        ('GEO Score',          results.get('geoScore', 0)),
        ('Competitive Parity', results.get('competitiveScore', 0)),
    ]
    score_data = [['Metric', 'Score', 'Status']]
    for label, val in scores:
        status = 'Good' if float(val or 0) >= 0.7 else 'Needs Work' if float(val or 0) >= 0.5 else 'Poor'
        score_data.append([label, pct(val), status])

    t = Table(score_data, colWidths=[8*cm, 4*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND),
        ('TEXTCOLOR',  (0,0), (-1,0), LIGHT),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f6f7')]),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#d5d8dc')),
        ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    # Color status column
    for i, (_, val) in enumerate(scores, start=1):
        t.setStyle(TableStyle([('TEXTCOLOR', (2,i), (2,i), score_color(val))]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # ── Teaser: show only scores + 3 keyword gaps then lock wall ─────────────
    if mode == 'teaser':
        gaps_t = results.get('keywordGaps', [])
        if gaps_t:
            story.append(Paragraph("Keyword Opportunities (Preview)", h2))
            story.append(Paragraph("A sample of the keyword gaps identified. Full analysis unlocked after onboarding.", tip))
            for g in gaps_t[:3]:
                story.append(Paragraph(
                    f"• <b>{g.get('keyword','')}</b> — Priority: {g.get('priority','').upper()}",
                    ParagraphStyle('kp', fontSize=9, fontName='Helvetica', textColor=BRAND, spaceAfter=5, leading=14)
                ))
            if len(gaps_t) > 3:
                story.append(Paragraph(f"  + {len(gaps_t)-3} more keyword gaps in the full report…", tip))
            story.append(Spacer(1, 0.5*cm))

        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d5d8dc'), spaceAfter=12))

        lock_row_style = ParagraphStyle('lrow', fontSize=8, fontName='Helvetica', textColor=colors.HexColor('#bdc3c7'))
        for label in [
            'GEO Metrics & AI Readiness Analysis',
            'Full Keyword Gap Analysis',
            'Top Keywords & Key Phrases Charts',
            'GEO Component Scores',
            'GEO Improvement Suggestions',
            'Priority Recommendations (10+ items)',
        ]:
            blocked = Table(
                [[Paragraph(f"  {label}", lock_row_style),
                  Paragraph("🔒 LOCKED", ParagraphStyle('lk', fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#bdc3c7'), alignment=TA_LEFT))]],
                colWidths=[13.5*cm, 3.5*cm],
            )
            blocked.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f4f6f7')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e8eaec')),
            ]))
            story.append(blocked)

        story.append(Spacer(1, 0.8*cm))
        cta_h = ParagraphStyle('cta_h', fontSize=16, fontName='Helvetica-Bold', textColor=BRAND, alignment=TA_CENTER, spaceAfter=8)
        cta_sub = ParagraphStyle('cta_s', fontSize=10, fontName='Helvetica', textColor=SUBTLE, alignment=TA_CENTER, spaceAfter=6, leading=16)
        cta_contact = ParagraphStyle('cta_c', fontSize=10, fontName='Helvetica-Bold', textColor=TEAL, alignment=TA_CENTER, spaceAfter=4)
        cta_inner = [
            [Paragraph("🔒  Unlock Your Full SEO / GEO Report", cta_h)],
            [Paragraph("This report contains detailed GEO metrics, complete keyword gap analysis, AI improvement suggestions, and 10+ priority recommendations — all personalised for your business.", cta_sub)],
            [Spacer(1, 0.2*cm)],
            [Paragraph("Contact Atlantic Digital to get your complete report and a custom action plan.", cta_sub)],
            [Spacer(1, 0.3*cm)],
            [Paragraph("📧  atlanticdigitalusa@gmail.com   ·   📞  +34 611 512 450", cta_contact)],
            [Spacer(1, 0.2*cm)],
            [Paragraph("🌐  atlantic-digital.com  ·  Book a free 30-minute consultation", cta_contact)],
        ]
        cta_table = Table(cta_inner, colWidths=[17*cm])
        cta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0faf9')),
            ('BOX', (0,0), (-1,-1), 1.5, TEAL),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 20),
            ('RIGHTPADDING', (0,0), (-1,-1), 20),
        ]))
        story.append(cta_table)

        buf.seek(0)
        doc.build(story)
        buf.seek(0)
        fname = (results.get('clientName') or results.get('client_name') or 'report').replace(' ', '_').lower()
        return send_file(buf, mimetype='application/pdf', as_attachment=True,
                         download_name=f'atlantic_digital_preview_{fname}.pdf')

    # ── GEO Metrics (full mode only below) ────────────────────────────────────
    geo = results.get('geoMetrics', {})
    if geo:
        story.append(Paragraph("GEO Metrics", h2))
        geo_data = [['Metric', 'Value', 'Benchmark', 'Status']]
        geo_rows = [
            ('Extractability',       geo.get('extractability',0),    0.6,  '%'),
            ('Citability',           geo.get('citability',0),         0.6,  '%'),
            ('Readability',          geo.get('readability',0),        0.6,  '%'),
            ('Claim Density (/100w)',geo.get('claimDensity',0),       4,    ''),
            ('Avg Sentence Length',  geo.get('avgSentenceLength',0),  0,    ' words'),
            ('AI Coverage Prediction',geo.get('coveragePrediction',0),50,  '%'),
        ]
        for label, val, bench, unit in geo_rows:
            try:
                fval = float(val)
                display = f"{fval*100:.0f}%" if unit == '%' and fval <= 1 else f"{fval:.1f}{unit}"
                ok = fval >= bench if bench else True
                status = 'Good' if ok else 'Low'
            except:
                display, status = str(val), '–'
            geo_data.append([label, display, f"≥{bench}{unit}" if bench else '–', status])

        tg = Table(geo_data, colWidths=[7*cm, 3.5*cm, 4*cm, 2.5*cm])
        tg.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BRAND),
            ('TEXTCOLOR',  (0,0), (-1,0), LIGHT),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f6f7')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#d5d8dc')),
            ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(tg)
        story.append(Spacer(1, 0.4*cm))

    # ── Keyword Gaps ──────────────────────────────────────────────────────────
    gaps = results.get('keywordGaps', [])
    if gaps:
        story.append(Paragraph("Top Keyword Gaps", h2))
        story.append(Paragraph("Keywords competitors rank for that your site is missing or underutilising.", tip))
        gap_data = [['Keyword', 'Gap Score', 'Your Score', 'Competitor Score', 'Priority']]
        for g in gaps[:12]:
            gap_data.append([
                g.get('keyword',''),
                f"{float(g.get('score',0)):.3f}",
                f"{float(g.get('client',0)):.3f}",
                f"{float(g.get('competitor',0)):.3f}",
                g.get('priority','').upper(),
            ])
        tgap = Table(gap_data, colWidths=[5*cm, 2.8*cm, 2.8*cm, 3.5*cm, 2.9*cm])
        tgap.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BRAND),
            ('TEXTCOLOR',  (0,0), (-1,0), LIGHT),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 8.5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f6f7')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#d5d8dc')),
            ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(tgap)
        story.append(Spacer(1, 0.4*cm))

    # ── Top Keywords ──────────────────────────────────────────────────────────
    keywords = results.get('topKeywords', [])
    bigrams  = results.get('topBigrams', [])
    if keywords or bigrams:
        story.append(Paragraph("Keyword Analysis", h2))
        col_items = []
        for kw in keywords[:10]:
            col_items.append(Paragraph(f"• {kw.get('keyword','')}  ({kw.get('score',0):.0f})", body))
        kw_table_data = [['Top Keywords', 'Top Bigrams']]
        kw_left  = '\n'.join(f"• {k.get('keyword','')}  ({k.get('score',0):.0f})" for k in keywords[:10])
        kw_right = '\n'.join(f"• {b.get('phrase','')}  ({b.get('score',0):.0f})" for b in bigrams[:8])
        kw_table_data.append([
            Paragraph(kw_left  or '–', body),
            Paragraph(kw_right or '–', body),
        ])
        tkw = Table(kw_table_data, colWidths=[8.5*cm, 8.5*cm])
        tkw.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BRAND),
            ('TEXTCOLOR',  (0,0), (-1,0), LIGHT),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,0), 9),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#d5d8dc')),
            ('VALIGN',     (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ]))
        story.append(tkw)
        story.append(Spacer(1, 0.4*cm))

    # ── GEO Components ────────────────────────────────────────────────────────
    geo_comps = results.get('geoComponents', [])
    if geo_comps:
        story.append(Paragraph("GEO Component Scores", h2))
        gc_data = [['Component', 'Score', 'Status', 'Current Value / Tip']]
        for c in geo_comps:
            val = float(c.get('score', 0))
            status = 'Good' if val >= 0.7 else 'Needs Work' if val >= 0.5 else 'Poor'
            gc_data.append([
                c.get('name', ''),
                f"{val*100:.0f}%",
                status,
                Paragraph(c.get('tip', ''), ParagraphStyle('tiny', fontSize=8, fontName='Helvetica', textColor=SUBTLE)),
            ])
        tgc = Table(gc_data, colWidths=[4.5*cm, 2.5*cm, 3*cm, 7*cm])
        tgc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BRAND),
            ('TEXTCOLOR',  (0,0), (-1,0), LIGHT),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 8.5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f6f7')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#d5d8dc')),
            ('ALIGN',      (1,0), (2,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        for i, c in enumerate(geo_comps, start=1):
            tgc.setStyle(TableStyle([('TEXTCOLOR', (1,i), (2,i), score_color(c.get('score',0)))]))
        story.append(tgc)
        story.append(Spacer(1, 0.4*cm))

    # ── GEO Improvement Suggestions ───────────────────────────────────────────
    geo_m = results.get('geoMetrics', {})
    if geo_m:
        suggestions = []
        if float(geo_m.get('claimDensity', 0)) < 4:
            suggestions.append(('CRITICAL', 'Claim Density', f"Current: {float(geo_m.get('claimDensity',0)):.1f}/100 words (target ≥4). Add statistics, percentages, and verifiable facts."))
        if float(geo_m.get('citability', 0)) < 0.6:
            suggestions.append(('HIGH', 'Citability', f"Score: {float(geo_m.get('citability',0))*100:.0f}%. Include 5+ quotable expert statements and data-backed claims."))
        if float(geo_m.get('extractability', 0)) < 0.6:
            suggestions.append(('HIGH', 'Extractability', f"Score: {float(geo_m.get('extractability',0))*100:.0f}%. Use H2/H3 headers, bullet points, and short paragraph blocks."))
        if float(geo_m.get('avgSentenceLength', 0)) > 25:
            suggestions.append(('MEDIUM', 'Sentence Length', f"Avg: {float(geo_m.get('avgSentenceLength',0)):.0f} words. Reduce to 15–20 words per sentence."))
        if float(geo_m.get('readability', 0)) < 0.6:
            suggestions.append(('MEDIUM', 'Readability', f"Score: {float(geo_m.get('readability',0))*100:.0f}%. Simplify vocabulary and add clear topic sentences."))
        if float(geo_m.get('coveragePrediction', 0)) < 50:
            suggestions.append(('MEDIUM', 'AI Coverage', f"{float(geo_m.get('coveragePrediction',0)):.0f}% AI citation probability. Add schema markup, FAQ section, and local authority signals."))

        if suggestions:
            story.append(Paragraph("GEO Improvement Suggestions", h2))
            pri_colors = {'CRITICAL': colors.HexColor('#e74c3c'), 'HIGH': colors.HexColor('#f39c12'), 'MEDIUM': colors.HexColor('#3498db')}
            sug_data = [['Priority', 'Area', 'Action Required']]
            for pri, area, action in suggestions:
                sug_data.append([
                    Paragraph(f"<b>{pri}</b>", ParagraphStyle('sp', fontSize=8, fontName='Helvetica-Bold', textColor=pri_colors.get(pri, SUBTLE))),
                    Paragraph(area, ParagraphStyle('sa', fontSize=8.5, fontName='Helvetica-Bold', textColor=BRAND)),
                    Paragraph(action, body),
                ])
            tsug = Table(sug_data, colWidths=[2.5*cm, 3.5*cm, 11*cm])
            tsug.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), BRAND),
                ('TEXTCOLOR',  (0,0), (-1,0), LIGHT),
                ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0,0), (-1,0), 9),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f6f7')]),
                ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#d5d8dc')),
                ('VALIGN',     (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(tsug)
            story.append(Spacer(1, 0.4*cm))

    # ── Recommendations (full mode) ────────────────────────────────────────────
    recs = results.get('recommendations', [])
    if recs:
        story.append(Paragraph("Priority Recommendations", h2))
        priority_colors = {'CRITICAL': colors.HexColor('#e74c3c'), 'HIGH': colors.HexColor('#f39c12'), 'MEDIUM': colors.HexColor('#3498db')}
        for r in recs[:10]:
            pri   = r.get('priority', 'MEDIUM').upper()
            cat   = r.get('category', '')
            msg   = r.get('message', '')
            color = priority_colors.get(pri, SUBTLE)
            story.append(Table(
                [[Paragraph(f"<b>[{pri}]</b> {cat}", ParagraphStyle('rec_h', fontSize=9, fontName='Helvetica-Bold', textColor=color)),
                  Paragraph(msg, body)]],
                colWidths=[4*cm, 13*cm],
                style=TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#eaecee')),
                ])
            ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SUBTLE))
    story.append(Paragraph(
        "Generated by Atlantic Digital Intelligence Platform  ·  Confidential",
        ParagraphStyle('footer', fontSize=7.5, fontName='Helvetica-Oblique', textColor=SUBTLE, alignment=TA_CENTER, spaceBefore=6)
    ))

    doc.build(story)
    buf.seek(0)

    safe_name = client_name.replace(' ', '_').lower()
    from flask import send_file
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f"atlantic_digital_report_{safe_name}.pdf")


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
    print("🌊 ATLANTIC DIGITAL API v5")
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
