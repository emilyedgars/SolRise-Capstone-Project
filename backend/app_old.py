"""
Atlantic Digital - Flask API Backend (v2)
==========================================
Improved with:
- Ollama connection checking
- Better error messages
- Fallback HTML generation
- Debug endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import json
import requests
import os

# Import the improved pipeline
from pipeline_v2 import AtlanticDigitalPipeline

app = Flask(__name__)
CORS(app)  # Allow React frontend to connect

# ============================================================================
# CONFIGURATION
# ============================================================================

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')  # Optional: for Claude

# ============================================================================
# MOCK DATABASE (for when MongoDB is not installed)
# ============================================================================

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {}
    
    def insert_one(self, doc):
        if '_id' not in doc:
            doc['_id'] = ObjectId()
        self.data[str(doc['_id'])] = doc
        print(f"📝 [MockDB] Inserted into {self.name}: {doc['_id']}")
        return type('obj', (object,), {'inserted_id': doc['_id']})()
    
    def find_one(self, query):
        if '_id' in query:
            key = str(query['_id']) if isinstance(query['_id'], ObjectId) else query['_id']
            return self.data.get(key)
        for item in self.data.values():
            match = all(item.get(k) == v for k, v in query.items() if k != '_id')
            if match:
                return item
        return None

    def find(self, query=None):
        items = list(self.data.values())
        return MockCursor(items)
    
    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc and '$set' in update:
            doc.update(update['$set'])
            print(f"🔄 [MockDB] Updated {self.name}: {doc.get('_id')}")
        return type('obj', (object,), {'modified_count': 1 if doc else 0})()


class MockCursor:
    def __init__(self, data):
        self.data = data
    
    def sort(self, key, direction=1):
        return self
    
    def limit(self, n):
        self.data = self.data[:n]
        return self
    
    def __iter__(self):
        return iter(self.data)
    
    def __list__(self):
        return self.data


class MockDatabase:
    def __init__(self):
        self.projects = MockCollection('projects')
        self.websites = MockCollection('websites')
        self.generated = MockCollection('generated')
        print("⚠️  Running in DEMO MODE (No MongoDB). Data will be lost on restart.")


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.atlantic_digital
    pipeline_db_uri = MONGODB_URI
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    db = MockDatabase()
    pipeline_db_uri = None


# ============================================================================
# OLLAMA CONNECTION CHECK
# ============================================================================

def check_ollama_status():
    """Check if Ollama is running and has required model"""
    try:
        response = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            has_qwen = any('qwen' in name.lower() for name in model_names)
            return {
                'connected': True,
                'models': model_names,
                'has_qwen': has_qwen,
                'recommended_model': 'qwen2:7b' if not has_qwen else next(
                    (n for n in model_names if 'qwen' in n.lower()), 'qwen2:7b'
                )
            }
    except Exception as e:
        return {
            'connected': False,
            'error': str(e),
            'models': [],
            'has_qwen': False
        }
    return {'connected': False, 'models': [], 'has_qwen': False}


def generate_with_ollama(prompt: str, model: str = 'qwen2:7b') -> dict:
    """Generate content with Ollama, returns dict with html and error info"""
    try:
        print(f"🤖 Calling Ollama ({model})...")
        print(f"   Prompt length: {len(prompt)} chars")
        
        response = requests.post(
            f'{OLLAMA_HOST}/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 8000
                }
            },
            timeout=300  # 5 minute timeout for generation
        )
        
        if response.status_code != 200:
            return {
                'success': False,
                'html': '',
                'error': f'Ollama returned status {response.status_code}: {response.text}'
            }
        
        result = response.json()
        html = result.get('response', '')
        
        # Clean up markdown code blocks if present
        if '```html' in html:
            html = html.split('```html')[1].split('```')[0]
        elif '```' in html:
            parts = html.split('```')
            if len(parts) >= 2:
                html = parts[1]
        
        html = html.strip()
        
        print(f"   ✓ Generated {len(html)} chars")
        
        if not html:
            return {
                'success': False,
                'html': '',
                'error': 'Ollama returned empty response'
            }
        
        return {
            'success': True,
            'html': html,
            'error': None
        }
        
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'html': '',
            'error': 'Ollama request timed out (5 min). Model might be loading.'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'html': '',
            'error': f'Cannot connect to Ollama at {OLLAMA_HOST}. Is it running?'
        }
    except Exception as e:
        return {
            'success': False,
            'html': '',
            'error': f'Ollama error: {str(e)}'
        }


def generate_fallback_html(project: dict) -> str:
    """Generate basic HTML template when Ollama is not available"""
    name = project.get('client_name', 'Business')
    location = project.get('location', 'Your Area')
    industry = project.get('industry', 'Services')
    results = project.get('results', {})
    
    keywords = results.get('topKeywords', [])
    keywords_str = ', '.join([k.get('keyword', k) if isinstance(k, dict) else str(k) 
                              for k in keywords[:5]]) if keywords else industry
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | Expert {industry} in {location}</title>
    <meta name="description" content="{name} provides professional {industry.lower()} services in {location}. Trusted by the community. Contact us today!">
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "{name}",
        "description": "Professional {industry.lower()} services in {location}",
        "address": {{
            "@type": "PostalAddress",
            "addressLocality": "{location}"
        }}
    }}
    </script>
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{ background: linear-gradient(135deg, #2C3E50, #4A6B7C); color: white; padding: 4rem 2rem; text-align: center; }}
        header h1 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
        header p {{ font-size: 1.25rem; opacity: 0.9; max-width: 600px; margin: 0 auto; }}
        .cta-button {{ display: inline-block; background: #4ECDC4; color: white; padding: 1rem 2rem; border-radius: 50px; text-decoration: none; font-weight: 600; margin-top: 2rem; }}
        section {{ padding: 4rem 2rem; }}
        section:nth-child(even) {{ background: #f9f9f9; }}
        h2 {{ font-size: 2rem; margin-bottom: 1.5rem; color: #2C3E50; }}
        .services-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; }}
        .service-card {{ background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }}
        .service-card h3 {{ color: #2C3E50; margin-bottom: 0.5rem; }}
        .stats {{ display: flex; justify-content: center; gap: 4rem; flex-wrap: wrap; margin: 2rem 0; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 3rem; font-weight: 700; color: #4ECDC4; }}
        .stat-label {{ color: #666; }}
        .faq-item {{ margin-bottom: 1.5rem; padding: 1.5rem; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .faq-item h3 {{ color: #2C3E50; margin-bottom: 0.5rem; }}
        footer {{ background: #2C3E50; color: white; padding: 2rem; text-align: center; }}
        .quote {{ font-style: italic; font-size: 1.2rem; border-left: 4px solid #4ECDC4; padding-left: 1rem; margin: 2rem 0; }}
    </style>
</head>
<body>
    <header>
        <h1>{name}</h1>
        <p>Your Trusted {industry} Provider in {location}</p>
        <p class="quote">"At {name}, we believe every customer deserves exceptional service backed by expertise and dedication."</p>
        <a href="#contact" class="cta-button">Contact Us Today</a>
    </header>
    
    <section>
        <div class="container">
            <h2>Why Choose {name}?</h2>
            <p>{name} has been serving {location} with professional {industry.lower()} services. Our team of experts is committed to delivering results that exceed expectations.</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">10+</div>
                    <div class="stat-label">Years Experience</div>
                </div>
                <div class="stat">
                    <div class="stat-number">500+</div>
                    <div class="stat-label">Happy Customers</div>
                </div>
                <div class="stat">
                    <div class="stat-number">98%</div>
                    <div class="stat-label">Satisfaction Rate</div>
                </div>
            </div>
            
            <p>Research shows that choosing an experienced local provider leads to better outcomes. At {name}, we combine years of expertise with the latest technology.</p>
        </div>
    </section>
    
    <section>
        <div class="container">
            <h2>Our Services</h2>
            <div class="services-grid">
                <div class="service-card">
                    <h3>Service One</h3>
                    <p>Professional service tailored to your needs with guaranteed satisfaction.</p>
                </div>
                <div class="service-card">
                    <h3>Service Two</h3>
                    <p>Expert solutions using the latest techniques and equipment.</p>
                </div>
                <div class="service-card">
                    <h3>Service Three</h3>
                    <p>Comprehensive care from our certified specialists.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <h2>Frequently Asked Questions</h2>
            
            <div class="faq-item">
                <h3>What services do you offer?</h3>
                <p>{name} offers comprehensive {industry.lower()} services in {location}. Our certified team provides personalized solutions for every customer.</p>
            </div>
            
            <div class="faq-item">
                <h3>How can I schedule an appointment?</h3>
                <p>You can contact us by phone or through our website to schedule an appointment. We offer flexible scheduling to accommodate your needs.</p>
            </div>
            
            <div class="faq-item">
                <h3>What areas do you serve?</h3>
                <p>{name} proudly serves {location} and surrounding areas. We have been the trusted local provider for over a decade.</p>
            </div>
            
            <div class="faq-item">
                <h3>What makes you different from competitors?</h3>
                <p>Our commitment to quality, customer satisfaction, and expertise sets us apart. We have a 98% customer satisfaction rate and use only the best practices in the industry.</p>
            </div>
        </div>
    </section>
    
    <section id="contact">
        <div class="container" style="text-align: center;">
            <h2>Contact Us</h2>
            <p>Ready to get started? Contact {name} today for a consultation.</p>
            <p style="margin-top: 1rem;"><strong>Location:</strong> {location}</p>
            <a href="#" class="cta-button">Get Started</a>
        </div>
    </section>
    
    <footer>
        <p>&copy; 2025 {name}. All rights reserved. | Serving {location}</p>
    </footer>
</body>
</html>'''


# ============================================================================
# INITIALIZE PIPELINE
# ============================================================================

pipeline = AtlanticDigitalPipeline(
    mongodb_uri=pipeline_db_uri,
    ollama_host=OLLAMA_HOST
)

# Check Ollama status on startup
ollama_status = check_ollama_status()
if ollama_status['connected']:
    print(f"✅ Ollama connected. Models: {ollama_status['models']}")
    if not ollama_status['has_qwen']:
        print(f"⚠️  Qwen model not found. Run: ollama pull qwen2:7b")
else:
    print(f"❌ Ollama not connected: {ollama_status.get('error', 'Unknown error')}")
    print("   Website generation will use fallback templates.")
    print("   To enable AI generation, start Ollama: ollama serve")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with status info"""
    ollama = check_ollama_status()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'mongodb': pipeline_db_uri is not None,
        'ollama': ollama,
        'anthropic_configured': bool(ANTHROPIC_API_KEY)
    })


@app.route('/api/analyze', methods=['POST'])
def run_analysis():
    """
    Run SEO/GEO analysis on client and competitor websites.
    
    Request body:
    {
        "clientUrl": "https://example.com",
        "clientName": "Business Name",
        "location": "City, State",
        "industry": "Industry Type",
        "competitors": ["https://comp1.com", "https://comp2.com"]
    }
    """
    data = request.json
    
    try:
        # Validate input
        if not data.get('clientUrl') or not data.get('clientName'):
            return jsonify({'error': 'Missing required fields: clientUrl and clientName'}), 400
        
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
        client_info = {
            'name': data['clientName'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
        }
        
        result = pipeline.run_analysis(
            client_url=data['clientUrl'],
            competitor_urls=[c for c in data.get('competitors', []) if c],
            client_info=client_info,
            project_id=project_id
        )
        
        # Update project with results
        db.projects.update_one(
            {'_id': project_id},
            {'$set': {
                'status': 'complete',
                'results': result,
                'updated_at': datetime.now()
            }}
        )
        
        # Generate prompt for display
        prompt_data = {
            'client_name': data['clientName'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'results': result
        }
        generated_prompt = pipeline.generate_prompt(prompt_data)
        result['generatedPrompt'] = generated_prompt

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
    Generate optimized website HTML.
    
    Request body:
    {
        "project_id": "...",
        "custom_prompt": "..." (optional),
        "use_fallback": false (optional - force template generation)
    }
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
        
        # Generate prompt
        base_prompt = pipeline.generate_prompt(project)
        final_prompt = data.get('custom_prompt') or base_prompt
        
        # Check if we should use Ollama or fallback
        use_fallback = data.get('use_fallback', False)
        ollama = check_ollama_status()
        
        generation_result = {
            'html': '',
            'method': '',
            'error': None
        }
        
        if not use_fallback and ollama['connected'] and ollama['has_qwen']:
            # Try Ollama first
            print("\n🚀 Generating website with Ollama...")
            result = generate_with_ollama(final_prompt, ollama['recommended_model'])
            
            if result['success']:
                generation_result['html'] = result['html']
                generation_result['method'] = 'ollama'
            else:
                print(f"   ⚠️ Ollama failed: {result['error']}")
                print("   📋 Using fallback template...")
                generation_result['html'] = generate_fallback_html(project)
                generation_result['method'] = 'fallback'
                generation_result['error'] = result['error']
        else:
            # Use fallback
            reason = 'User requested' if use_fallback else \
                    'Not connected' if not ollama['connected'] else \
                    'Qwen model not installed'
            print(f"\n📋 Using fallback template ({reason})...")
            generation_result['html'] = generate_fallback_html(project)
            generation_result['method'] = 'fallback'
            if not use_fallback:
                generation_result['error'] = f'Ollama: {reason}'
        
        # Validate the generated HTML
        validation = validate_generated_html(generation_result['html'], project)
        
        # Save to database
        db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': {
                'generated_html': generation_result['html'],
                'generation_prompt': final_prompt,
                'generation_method': generation_result['method'],
                'generation_score': validation['overall'],
                'updated_at': datetime.now()
            }}
        )
        
        return jsonify({
            'success': True,
            'html': generation_result['html'],
            'method': generation_result['method'],
            'error': generation_result['error'],
            'validation': validation,
            'prompt': final_prompt,
            'prompt_length': len(final_prompt)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-simple', methods=['POST'])
def generate_simple():
    """
    Simple generation endpoint - just takes a prompt and returns HTML.
    Useful for testing.
    
    Request body:
    {
        "prompt": "Generate a website for...",
        "model": "qwen2:7b" (optional)
    }
    """
    data = request.json
    prompt = data.get('prompt')
    model = data.get('model', 'qwen2:7b')
    
    if not prompt:
        return jsonify({'error': 'Missing prompt'}), 400
    
    # Check Ollama
    ollama = check_ollama_status()
    if not ollama['connected']:
        return jsonify({
            'error': f"Ollama not connected. Please run: ollama serve",
            'ollama_status': ollama
        }), 503
    
    if not ollama['has_qwen'] and 'qwen' in model.lower():
        return jsonify({
            'error': f"Qwen model not found. Please run: ollama pull {model}",
            'available_models': ollama['models']
        }), 503
    
    result = generate_with_ollama(prompt, model)
    
    return jsonify({
        'success': result['success'],
        'html': result['html'],
        'error': result['error'],
        'model': model,
        'prompt_length': len(prompt)
    })


@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        projects = list(db.projects.find())
        
        # Convert for JSON
        for project in projects:
            project['_id'] = str(project['_id'])
            if 'created_at' in project:
                project['created_at'] = project['created_at'].isoformat() if hasattr(project['created_at'], 'isoformat') else str(project['created_at'])
            if 'updated_at' in project:
                project['updated_at'] = project['updated_at'].isoformat() if hasattr(project['updated_at'], 'isoformat') else str(project['updated_at'])
        
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get specific project"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        project['_id'] = str(project['_id'])
        if 'created_at' in project:
            project['created_at'] = project['created_at'].isoformat() if hasattr(project['created_at'], 'isoformat') else str(project['created_at'])
        if 'updated_at' in project:
            project['updated_at'] = project['updated_at'].isoformat() if hasattr(project['updated_at'], 'isoformat') else str(project['updated_at'])
        
        return jsonify(project)
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


@app.route('/api/geo-analyze', methods=['POST'])
def geo_analyze():
    """Standalone GEO analysis for any URL"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    
    try:
        result = pipeline.analyze_geo_only(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/<project_id>', methods=['GET'])
def export_project(project_id):
    """Export project as JSON or HTML"""
    export_format = request.args.get('format', 'json')
    
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if export_format == 'html':
            html = project.get('generated_html', '<p>No HTML generated yet</p>')
            return html, 200, {'Content-Type': 'text/html'}
        else:
            project['_id'] = str(project['_id'])
            if 'created_at' in project:
                project['created_at'] = project['created_at'].isoformat() if hasattr(project['created_at'], 'isoformat') else str(project['created_at'])
            if 'updated_at' in project:
                project['updated_at'] = project['updated_at'].isoformat() if hasattr(project['updated_at'], 'isoformat') else str(project['updated_at'])
            
            return jsonify(project), 200, {
                'Content-Disposition': f'attachment; filename=project_{project_id}.json'
            }
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# VALIDATION HELPER
# ============================================================================

def validate_generated_html(html: str, project: dict) -> dict:
    """Validate generated HTML for SEO and GEO requirements"""
    from bs4 import BeautifulSoup
    import re
    
    if not html:
        return {'overall': 0, 'seo': 0, 'geo': 0, 'feedback': ['No HTML generated']}
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    scores = {}
    feedback = []
    
    # SEO checks
    h1_tags = soup.find_all('h1')
    scores['h1'] = 1.0 if len(h1_tags) == 1 else 0.5 if len(h1_tags) > 0 else 0.0
    if len(h1_tags) != 1:
        feedback.append(f"Should have exactly 1 H1 tag (found {len(h1_tags)})")
    
    title = soup.find('title')
    title_len = len(title.text) if title else 0
    scores['title'] = 1.0 if 50 <= title_len <= 65 else 0.6 if 40 <= title_len <= 70 else 0.3
    if not title:
        feedback.append("Missing <title> tag")
    elif title_len < 50 or title_len > 65:
        feedback.append(f"Title should be 50-65 chars (currently {title_len})")
    
    meta_desc = soup.find('meta', {'name': 'description'})
    meta_len = len(meta_desc.get('content', '')) if meta_desc else 0
    scores['meta'] = 1.0 if 150 <= meta_len <= 160 else 0.6 if 120 <= meta_len <= 180 else 0.3
    if not meta_desc:
        feedback.append("Missing meta description")
    
    # GEO checks
    quotes = len(re.findall(r'"[^"]{20,150}"', text))
    scores['quotes'] = min(quotes / 5, 1.0)
    if quotes < 5:
        feedback.append(f"Add {5-quotes} more quotable statements")
    
    stats = len(re.findall(r'\d+%|\d+\+?\s*(?:years?|customers?|clients?)', text, re.I))
    scores['stats'] = min(stats / 4, 1.0)
    if stats < 4:
        feedback.append(f"Add {4-stats} more statistics")
    
    schemas = soup.find_all('script', {'type': 'application/ld+json'})
    scores['schema'] = 1.0 if len(schemas) > 0 else 0.0
    if not schemas:
        feedback.append("Add JSON-LD schema markup")
    
    # Calculate scores
    seo_score = (scores['h1'] + scores['title'] + scores['meta']) / 3
    geo_score = (scores['quotes'] + scores['stats'] + scores['schema']) / 3
    overall = (seo_score * 0.4) + (geo_score * 0.6)
    
    return {
        'overall': round(overall, 2),
        'seo': round(seo_score, 2),
        'geo': round(geo_score, 2),
        'details': scores,
        'feedback': feedback
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌊 ATLANTIC DIGITAL API SERVER")
    print("="*60)
    print(f"MongoDB: {'✅ Connected' if pipeline_db_uri else '⚠️ Using MockDB'}")
    print(f"Ollama:  {'✅ Connected' if ollama_status['connected'] else '❌ Not connected'}")
    if ollama_status['connected']:
        print(f"         Models: {ollama_status['models']}")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /api/analyze          - Run SEO/GEO analysis")
    print("  POST /api/generate-website - Generate optimized website")
    print("  POST /api/generate-simple  - Simple prompt → HTML")
    print("  GET  /api/health           - Health check")
    print("  GET  /api/projects         - List projects")
    print("  GET  /api/project/<id>     - Get project details")
    print("  POST /api/geo-analyze      - Standalone GEO analysis")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
