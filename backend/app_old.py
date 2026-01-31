"""
Atlantic Digital - Flask API
============================
Run with: python app.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from bson import ObjectId
import requests
import os

from pipeline_v4 import AtlanticDigitalPipeline

app = Flask(__name__)
CORS(app)

# Config
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2:7b')

# Simple mock DB
class MockDB:
    def __init__(self):
        self.data = {}
    def insert_one(self, doc):
        doc['_id'] = ObjectId()
        self.data[str(doc['_id'])] = doc
        return type('R', (), {'inserted_id': doc['_id']})()
    def find_one(self, q):
        return self.data.get(str(q.get('_id')))
    def find(self, q=None):
        return list(self.data.values())
    def update_one(self, q, u):
        doc = self.find_one(q)
        if doc and '$set' in u:
            doc.update(u['$set'])

class DB:
    def __init__(self):
        self.projects = MockDB()

# Database
try:
    from pymongo import MongoClient
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.atlantic_digital
    print("✅ MongoDB connected")
except:
    db = DB()
    print("⚠️ Using in-memory database")

# Pipeline
pipeline = AtlanticDigitalPipeline(ollama_host=OLLAMA_HOST)

# Check Ollama
def check_ollama():
    try:
        r = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=3)
        models = [m['name'] for m in r.json().get('models', [])]
        return {'connected': True, 'models': models}
    except:
        return {'connected': False, 'models': []}

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'ollama': check_ollama()})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data.get('clientUrl') or not data.get('clientName'):
        return jsonify({'error': 'Missing clientUrl or clientName'}), 400
    
    try:
        project_id = ObjectId()
        project = {
            '_id': project_id,
            'client_name': data['clientName'],
            'client_url': data['clientUrl'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'competitors': [c for c in data.get('competitors', []) if c],
            'created_at': datetime.now()
        }
        db.projects.insert_one(project)
        
        results = pipeline.run_analysis(
            client_url=data['clientUrl'],
            competitor_urls=project['competitors'],
            client_info={'name': data['clientName'], 'location': data.get('location', ''), 'industry': data.get('industry', '')}
        )
        
        prompt = pipeline.generate_prompt({**project, 'results': results})
        results['generatedPrompt'] = prompt
        
        db.projects.update_one({'_id': project_id}, {'$set': {'results': results}})
        
        return jsonify({'success': True, 'project_id': str(project_id), 'results': results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-website', methods=['POST'])
def generate():
    data = request.json
    project_id = data.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'Missing project_id'}), 400
    
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        prompt = data.get('custom_prompt') or pipeline.generate_prompt(project)
        
        # Try Ollama
        ollama = check_ollama()
        if ollama['connected']:
            print(f"🤖 Generating with Ollama ({OLLAMA_MODEL})...")
            try:
                # Log the prompt length and start time
                import time
                start_time = time.time()
                
                payload = {
                    'model': OLLAMA_MODEL, 
                    'prompt': prompt, 
                    'stream': False,
                    'options': {'temperature': 0.7, 'num_predict': 8000}
                }
                
                r = requests.post(f'{OLLAMA_HOST}/api/generate', json=payload, timeout=240)
                r.raise_for_status()
                
                response_json = r.json()
                html = response_json.get('response', '')
                
                # Sanitize HTML from markdown blocks if present
                if '```' in html:
                    if '```html' in html:
                        html = html.split('```html')[1].split('```')[0]
                    else:
                        html = html.split('```')[1].split('```')[0]
                
                html = html.strip()
                method = 'ollama'
                
                duration = time.time() - start_time
                print(f"✅ Generation complete in {duration:.1f}s")
                
            except Exception as e:
                print(f"❌ Ollama failed: {e}")
                html = f"<html><body style='font-family: sans-serif; padding: 2rem;'><h1>Generation failed</h1><p>Error: {str(e)}</p></body></html>"
                method = 'error'
        else:
            print("⚠️ Ollama not connected")
            html = "<html><body style='font-family: sans-serif; padding: 2rem;'><h1>Ollama not connected</h1><p>Start Ollama with: <code>ollama serve</code></p></body></html>"
            method = 'fallback'
        
        db.projects.update_one({'_id': ObjectId(project_id)}, {'$set': {'generated_html': html}})
        
        return jsonify({'success': True, 'html': html, 'method': method, 'prompt_length': len(prompt)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/geo-analyze', methods=['POST'])
def geo_analyze():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'Missing url'}), 400
    try:
        return jsonify(pipeline.analyze_geo_only(url))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects')
def list_projects():
    projects = db.projects.find()
    for p in projects:
        p['_id'] = str(p['_id'])
    return jsonify(projects)

@app.route('/api/project/<pid>')
def get_project(pid):
    p = db.projects.find_one({'_id': ObjectId(pid)})
    if not p:
        return jsonify({'error': 'Not found'}), 404
    p['_id'] = str(p['_id'])
    return jsonify(p)

@app.route('/api/project/<pid>/prompt')
def get_prompt(pid):
    p = db.projects.find_one({'_id': ObjectId(pid)})
    if not p:
        return jsonify({'error': 'Not found'}), 404
    prompt = pipeline.generate_prompt(p)
    return jsonify({'prompt': prompt, 'length': len(prompt)})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🌊 ATLANTIC DIGITAL API")
    print("="*50)
    ollama = check_ollama()
    print(f"Ollama: {'✅ ' + str(ollama['models']) if ollama['connected'] else '❌ Not running'}")
    print("="*50)
    print("Endpoints:")
    print("  POST /api/analyze          - Run SEO/GEO analysis")
    print("  POST /api/generate-website - Generate HTML")
    print("  POST /api/geo-analyze      - Quick GEO check")
    print("  GET  /api/projects         - List projects")
    print("="*50 + "\n")
    app.run(debug=True, port=5001, host='0.0.0.0')
