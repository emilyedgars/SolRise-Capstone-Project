"""
Atlantic Digital - Flask API v3
===============================
- Single-pass generation (no iterations)
- 2-minute timeout
- Fallback HTML when Ollama fails
- Better error messages
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from bson import ObjectId
import requests
import os
import re

# Use pipeline v3
from pipeline_v3 import AtlanticDigitalPipeline

app = Flask(__name__)
CORS(app)

# Config
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')

# ============================================================================
# MOCK DATABASE
# ============================================================================

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {}
    
    def insert_one(self, doc):
        if '_id' not in doc:
            doc['_id'] = ObjectId()
        self.data[str(doc['_id'])] = doc
        print(f"📝 [MockDB] Inserted: {doc['_id']}")
        return type('obj', (object,), {'inserted_id': doc['_id']})()
    
    def find_one(self, query):
        if '_id' in query:
            return self.data.get(str(query['_id']))
        return None
    
    def find(self, query=None):
        return list(self.data.values())
    
    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc and '$set' in update:
            doc.update(update['$set'])
            print(f"🔄 [MockDB] Updated: {doc.get('_id')}")


class MockDB:
    def __init__(self):
        self.projects = MockCollection('projects')
        print("⚠️ Running without MongoDB - data won't persist")


# Database connection
try:
    from pymongo import MongoClient
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.atlantic_digital
    db_uri = MONGODB_URI
    print("✅ MongoDB connected")
except:
    db = MockDB()
    db_uri = None

# Initialize pipeline
pipeline = AtlanticDigitalPipeline(mongodb_uri=db_uri, ollama_host=OLLAMA_HOST)

# Check Ollama
def check_ollama():
    try:
        r = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=5)
        if r.status_code == 200:
            models = [m.get('name', '') for m in r.json().get('models', [])]
            return {'connected': True, 'models': models, 'has_qwen': any('qwen' in m for m in models)}
    except:
        pass
    return {'connected': False, 'models': [], 'has_qwen': False}

ollama_status = check_ollama()
print(f"{'✅' if ollama_status['connected'] else '❌'} Ollama: {ollama_status}")


# ============================================================================
# FALLBACK HTML GENERATOR
# ============================================================================

def generate_fallback_html(project: dict) -> str:
    """Generate template HTML when Ollama unavailable"""
    name = project.get('client_name', 'Business')
    location = project.get('location', 'Your Area')
    industry = project.get('industry', 'Services')
    results = project.get('results', {})
    
    keywords = results.get('topKeywords', [])
    kw_str = ', '.join([k.get('keyword', str(k)) if isinstance(k, dict) else str(k) for k in keywords[:5]]) or industry
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | Expert {industry} Services in {location}</title>
    <meta name="description" content="{name} provides professional {industry.lower()} services in {location}. Trusted by 500+ families. 98% satisfaction rate. Contact us today!">
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "{name}",
        "description": "Professional {industry.lower()} services in {location}",
        "address": {{ "@type": "PostalAddress", "addressLocality": "{location}" }},
        "aggregateRating": {{ "@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "127" }}
    }}
    </script>
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {{
                "@type": "Question",
                "name": "What services does {name} offer?",
                "acceptedAnswer": {{ "@type": "Answer", "text": "{name} provides comprehensive {industry.lower()} services in {location}, including consultations, treatments, and ongoing support." }}
            }},
            {{
                "@type": "Question", 
                "name": "How can I schedule an appointment?",
                "acceptedAnswer": {{ "@type": "Answer", "text": "You can schedule an appointment by calling us or using our online booking system. We offer same-day appointments for urgent needs." }}
            }},
            {{
                "@type": "Question",
                "name": "What areas do you serve?",
                "acceptedAnswer": {{ "@type": "Answer", "text": "{name} proudly serves {location} and surrounding communities within a 25-mile radius." }}
            }}
        ]
    }}
    </script>
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{ background: linear-gradient(135deg, #2C3E50, #4A6B7C); color: white; padding: 5rem 2rem; text-align: center; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
        .tagline {{ font-size: 1.3rem; opacity: 0.9; margin-bottom: 1rem; }}
        .quote {{ font-style: italic; font-size: 1.1rem; max-width: 600px; margin: 1rem auto; padding: 1rem; border-left: 4px solid #4ECDC4; background: rgba(255,255,255,0.1); }}
        .cta {{ display: inline-block; background: #4ECDC4; color: white; padding: 1rem 2.5rem; border-radius: 50px; text-decoration: none; font-weight: 600; margin-top: 1.5rem; }}
        section {{ padding: 4rem 2rem; }}
        section:nth-child(even) {{ background: #f8f9fa; }}
        h2 {{ font-size: 2rem; margin-bottom: 1.5rem; color: #2C3E50; text-align: center; }}
        .stats {{ display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; margin: 2rem 0; }}
        .stat {{ text-align: center; padding: 1.5rem; }}
        .stat-num {{ font-size: 3rem; font-weight: 700; color: #4ECDC4; }}
        .stat-label {{ color: #666; margin-top: 0.5rem; }}
        .services {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; }}
        .service {{ background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); }}
        .service h3 {{ color: #2C3E50; margin-bottom: 0.75rem; }}
        .faq {{ max-width: 800px; margin: 0 auto; }}
        .faq-item {{ background: white; margin-bottom: 1rem; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .faq-item h3 {{ color: #2C3E50; margin-bottom: 0.5rem; font-size: 1.1rem; }}
        .faq-item p {{ color: #555; }}
        footer {{ background: #2C3E50; color: white; padding: 2rem; text-align: center; }}
        .authority {{ background: rgba(78, 205, 196, 0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0; }}
    </style>
</head>
<body>
    <header>
        <h1>{name} | {industry} in {location}</h1>
        <p class="tagline">Your Trusted Local {industry} Provider</p>
        <p class="quote">"At {name}, we believe every customer deserves exceptional service backed by years of expertise and a genuine commitment to their success."</p>
        <p class="quote">"Our mission is to provide {location} with the highest quality {industry.lower()} services, combining modern techniques with personalized care."</p>
        <a href="#contact" class="cta">Schedule Free Consultation</a>
    </header>
    
    <section>
        <div class="container">
            <h2>Why {location} Trusts {name}</h2>
            <p style="text-align: center; max-width: 700px; margin: 0 auto 2rem;">"{name} has proudly served the {location} community for over 10 years, building lasting relationships with families who trust us for their {industry.lower()} needs."</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-num">10+</div>
                    <div class="stat-label">Years Serving {location}</div>
                </div>
                <div class="stat">
                    <div class="stat-num">500+</div>
                    <div class="stat-label">Happy Customers</div>
                </div>
                <div class="stat">
                    <div class="stat-num">98%</div>
                    <div class="stat-label">Satisfaction Rate</div>
                </div>
                <div class="stat">
                    <div class="stat-num">50+</div>
                    <div class="stat-label">Years Combined Experience</div>
                </div>
            </div>
            
            <div class="authority">
                <p><strong>Research shows</strong> that choosing an experienced local provider leads to better outcomes and higher satisfaction. <strong>Industry experts recommend</strong> working with established businesses that understand local needs. At {name}, our <strong>board-certified specialists</strong> deliver results backed by the latest best practices.</p>
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <h2>Our {industry} Services</h2>
            <div class="services">
                <div class="service">
                    <h3>Consultations</h3>
                    <p>Personalized consultations to understand your unique needs. Our experts provide honest assessments and clear recommendations.</p>
                </div>
                <div class="service">
                    <h3>Core Services</h3>
                    <p>Comprehensive {industry.lower()} solutions using the latest techniques and equipment. Quality guaranteed.</p>
                </div>
                <div class="service">
                    <h3>Ongoing Support</h3>
                    <p>We build lasting relationships with follow-up care and support whenever you need us.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <h2>Frequently Asked Questions</h2>
            <div class="faq">
                <div class="faq-item">
                    <h3>What services does {name} offer?</h3>
                    <p>{name} provides comprehensive {industry.lower()} services in {location}. Our certified team delivers personalized solutions tailored to each customer's unique needs, from initial consultation through ongoing support.</p>
                </div>
                <div class="faq-item">
                    <h3>How can I schedule an appointment with {name}?</h3>
                    <p>Scheduling an appointment is easy. You can call us directly, use our online booking system, or visit us in person. We offer flexible scheduling including same-day appointments for urgent needs.</p>
                </div>
                <div class="faq-item">
                    <h3>What areas does {name} serve?</h3>
                    <p>{name} proudly serves {location} and surrounding communities. For over 10 years, we've been the trusted choice for families throughout the region.</p>
                </div>
                <div class="faq-item">
                    <h3>What makes {name} different from other providers?</h3>
                    <p>Our commitment to quality, customer satisfaction, and expertise sets us apart. With a 98% satisfaction rate and over 500 happy customers, we've earned our reputation as {location}'s premier {industry.lower()} provider.</p>
                </div>
                <div class="faq-item">
                    <h3>Do you offer free consultations?</h3>
                    <p>Yes! {name} offers complimentary initial consultations. We believe in building relationships based on trust, which starts with understanding your needs before any commitment.</p>
                </div>
                <div class="faq-item">
                    <h3>What are your hours of operation?</h3>
                    <p>{name} is open Monday through Friday 8am-6pm and Saturday 9am-3pm. We also offer extended hours by appointment to accommodate busy schedules.</p>
                </div>
                <div class="faq-item">
                    <h3>How long has {name} been in business?</h3>
                    <p>{name} has been serving {location} for over 10 years. Our team has over 50 years of combined experience in the {industry.lower()} industry.</p>
                </div>
                <div class="faq-item">
                    <h3>Do you offer emergency services?</h3>
                    <p>Yes, {name} provides emergency services for urgent needs. Contact us immediately and we'll do our best to accommodate same-day appointments.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section id="contact" style="background: linear-gradient(135deg, #2C3E50, #4A6B7C); color: white;">
        <div class="container" style="text-align: center;">
            <h2 style="color: white;">Ready to Get Started?</h2>
            <p style="font-size: 1.2rem; margin-bottom: 1.5rem;">"At {name}, we're committed to exceeding your expectations. Contact us today and experience the difference."</p>
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Hours:</strong> Mon-Fri 8am-6pm, Sat 9am-3pm</p>
            <a href="#" class="cta" style="background: white; color: #2C3E50;">Contact Us Today</a>
        </div>
    </section>
    
    <footer>
        <p>&copy; 2025 {name}. All rights reserved.</p>
        <p>Proudly serving {location} for over 10 years.</p>
    </footer>
</body>
</html>'''


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    ollama = check_ollama()
    return jsonify({
        'status': 'healthy',
        'mongodb': db_uri is not None,
        'ollama': ollama
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Run SEO/GEO analysis"""
    data = request.json
    
    if not data.get('clientUrl') or not data.get('clientName'):
        return jsonify({'error': 'Missing clientUrl or clientName'}), 400
    
    try:
        # Create project
        project_id = ObjectId()
        project = {
            '_id': project_id,
            'client_name': data['clientName'],
            'client_url': data['clientUrl'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'competitors': [c for c in data.get('competitors', []) if c],
            'status': 'running',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        db.projects.insert_one(project)
        
        # Run analysis
        result = pipeline.run_analysis(
            client_url=data['clientUrl'],
            competitor_urls=[c for c in data.get('competitors', []) if c],
            client_info={
                'name': data['clientName'],
                'location': data.get('location', ''),
                'industry': data.get('industry', '')
            },
            project_id=project_id
        )
        
        # Update project
        db.projects.update_one(
            {'_id': project_id},
            {'$set': {'status': 'complete', 'results': result, 'updated_at': datetime.now()}}
        )
        
        # Generate prompt
        prompt = pipeline.generate_prompt({
            'client_name': data['clientName'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'results': result
        })
        result['generatedPrompt'] = prompt
        
        return jsonify({
            'success': True,
            'project_id': str(project_id),
            'results': result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-website', methods=['POST'])
def generate_website():
    """
    Generate optimized website HTML (single pass).
    
    Request: { project_id, custom_prompt? }
    """
    data = request.json
    project_id = data.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'Missing project_id'}), 400
    
    try:
        # Get project
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get prompt
        base_prompt = pipeline.generate_prompt(project)
        final_prompt = data.get('custom_prompt') or base_prompt
        
        # Check Ollama
        ollama = check_ollama()
        
        html = ''
        method = ''
        error = None
        score = {'overall': 0, 'seo': 0, 'geo': 0}
        
        if ollama['connected'] and ollama['has_qwen']:
            # Try Ollama (2 minute timeout)
            print("\n🚀 Generating with Ollama (2 min timeout)...")
            result = pipeline.generate_website(final_prompt, timeout=120)
            
            if result['success']:
                html = result['html']
                score = result['score']
                method = 'ollama'
                print(f"   ✓ Success! Score: {score}")
            else:
                print(f"   ❌ Failed: {result['error']}")
                print("   📋 Using fallback template...")
                html = generate_fallback_html(project)
                score = pipeline._validate_html(html)
                method = 'fallback'
                error = result['error']
        else:
            # Use fallback
            reason = 'Not connected' if not ollama['connected'] else 'Qwen not installed'
            print(f"\n📋 Using fallback ({reason})...")
            html = generate_fallback_html(project)
            score = pipeline._validate_html(html)
            method = 'fallback'
            error = f'Ollama: {reason}'
        
        # Save to project
        db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': {
                'generated_html': html,
                'generation_prompt': final_prompt,
                'generation_method': method,
                'generation_score': score,
                'updated_at': datetime.now()
            }}
        )
        
        return jsonify({
            'success': True,
            'html': html,
            'method': method,
            'error': error,
            'score': score,
            'prompt': final_prompt,
            'prompt_length': len(final_prompt)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>/prompt', methods=['GET'])
def get_prompt(project_id):
    """Get the prompt for a project"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Not found'}), 404
        
        prompt = pipeline.generate_prompt(project)
        return jsonify({'prompt': prompt, 'length': len(prompt)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>/html', methods=['GET'])
def get_html(project_id):
    """Get generated HTML for a project"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Not found'}), 404
        
        html = project.get('generated_html', '')
        if not html:
            return jsonify({'error': 'No HTML generated yet'}), 404
        
        return html, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/geo-analyze', methods=['POST'])
def geo_analyze():
    """Standalone GEO analysis"""
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    
    try:
        result = pipeline.analyze_geo_only(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all projects"""
    try:
        projects = list(db.projects.find())
        for p in projects:
            p['_id'] = str(p['_id'])
            if 'created_at' in p and hasattr(p['created_at'], 'isoformat'):
                p['created_at'] = p['created_at'].isoformat()
            if 'updated_at' in p and hasattr(p['updated_at'], 'isoformat'):
                p['updated_at'] = p['updated_at'].isoformat()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details"""
    try:
        p = db.projects.find_one({'_id': ObjectId(project_id)})
        if not p:
            return jsonify({'error': 'Not found'}), 404
        
        p['_id'] = str(p['_id'])
        if 'created_at' in p and hasattr(p['created_at'], 'isoformat'):
            p['created_at'] = p['created_at'].isoformat()
        if 'updated_at' in p and hasattr(p['updated_at'], 'isoformat'):
            p['updated_at'] = p['updated_at'].isoformat()
        return jsonify(p)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🌊 ATLANTIC DIGITAL API v3")
    print("="*50)
    print(f"MongoDB: {'✅' if db_uri else '⚠️ Mock'}")
    print(f"Ollama:  {'✅ ' + str(ollama_status['models']) if ollama_status['connected'] else '❌ Not connected'}")
    print("="*50)
    print("\nEndpoints:")
    print("  POST /api/analyze          - SEO/GEO analysis")
    print("  POST /api/generate-website - Generate HTML (single pass)")
    print("  GET  /api/project/<id>/prompt - Get prompt")
    print("  GET  /api/project/<id>/html   - Get generated HTML")
    print("  POST /api/geo-analyze      - Standalone GEO check")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
