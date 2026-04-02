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
        
        print(f"\n🤖 Generating website for project: {project_id}")
        print(f"   Prompt length: {len(prompt)} chars")
        
        # Check Ollama
        ollama = check_ollama()
        
        if not ollama['connected']:
            return jsonify({
                'success': False,
                'error': 'Ollama not connected. Start with: ollama serve',
                'html': '',
                'method': 'error'
            }), 503
        
        if not ollama['model_available']:
            return jsonify({
                'success': False,
                'error': f"Model {OLLAMA_MODEL} not found. Install with: ollama pull {OLLAMA_MODEL}",
                'html': '',
                'method': 'error'
            }), 503
        
        # Generate with Ollama
        import time
        start_time = time.time()
        
        try:
            response = requests.post(
                f'{OLLAMA_HOST}/api/generate',
                json={
                    'model': OLLAMA_MODEL,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'num_predict': 6000  # Reduced for faster generation
                    }
                },
                timeout=120  # 2 minute timeout (1.5b is fast)
            )
            response.raise_for_status()
            
            html = response.json().get('response', '')
            
            # Clean markdown code blocks
            if '```html' in html:
                html = html.split('```html')[1].split('```')[0]
            elif '```' in html:
                parts = html.split('```')
                if len(parts) >= 2:
                    html = parts[1]
            
            html = html.strip()
            
            # Validate HTML
            if not html or len(html) < 100:
                return jsonify({
                    'success': False,
                    'error': 'Generated HTML too short or empty',
                    'html': html,
                    'method': 'error'
                }), 500
            
            duration = time.time() - start_time
            print(f"   ✅ Generated {len(html)} chars in {duration:.1f}s")
            
            # Validate the generated HTML
            validation = pipeline.validate_generated_html(html)
            
            # Save to database
            db.projects.update_one(
                {'_id': ObjectId(project_id)},
                {'$set': {
                    'generated_html': html,
                    'generation_method': 'ollama',
                    'generation_model': OLLAMA_MODEL,
                    'generation_time': duration,
                    'generation_validation': validation,
                    'updated_at': datetime.utcnow()
                }}
            )
            
            return jsonify({
                'success': True,
                'html': html,
                'method': 'ollama',
                'model': OLLAMA_MODEL,
                'generation_time': round(duration, 1),
                'prompt_length': len(prompt),
                'html_length': len(html),
                'validation': validation
            })
            
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': 'Ollama timeout - generation took too long',
                'html': '',
                'method': 'error'
            }), 504
        
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'Ollama request failed: {str(e)}',
                'html': '',
                'method': 'error'
            }), 502
            
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
