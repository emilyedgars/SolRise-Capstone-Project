"""
SolRise - Flask API v7
===============================
- PDF Report Generation
- Fixed GEO analyzer
- Faster model (qwen2:1.5b)
- Dynamic validation
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime
from bson import ObjectId
import requests
import os

from pipelines.pipeline_v8 import SolRisePipeline

app = Flask(__name__)
CORS(app)

# Config
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2:1.5b')

# Database
db = None
using_mongodb = False

try:
    from pymongo import MongoClient
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    client.server_info()
    db = client.solrise
    using_mongodb = True
    print("✅ MongoDB connected")
except:
    class InMemoryDB:
        def __init__(self):
            self.data = {}
        def insert_one(self, doc):
            doc['_id'] = ObjectId()
            self.data[str(doc['_id'])] = doc.copy()
            return type('R', (), {'inserted_id': doc['_id']})()
        def find_one(self, q):
            return self.data.get(str(q.get('_id'))) if '_id' in q else None
        def find(self, q=None):
            return list(self.data.values())
        def update_one(self, q, u):
            doc = self.find_one(q)
            if doc and '$set' in u:
                doc.update(u['$set'])
                self.data[str(doc['_id'])] = doc
        def delete_one(self, q):
            doc = self.find_one(q)
            if doc:
                del self.data[str(doc['_id'])]
                return type('R', (), {'deleted_count': 1})()
            return type('R', (), {'deleted_count': 0})()
        def count_documents(self, q=None):
            return len(self.data)
    
    class DB:
        def __init__(self):
            self.projects = InMemoryDB()
    db = DB()
    print("⚠️ Using in-memory database")

# Pipeline
pipeline = SolRisePipeline(ollama_host=OLLAMA_HOST)

def check_ollama():
    try:
        r = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=3)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            has_model = any(OLLAMA_MODEL.split(':')[0] in m for m in models)
            return {'connected': True, 'models': models, 'selected': OLLAMA_MODEL, 'available': has_model}
    except:
        pass
    return {'connected': False, 'models': [], 'selected': OLLAMA_MODEL, 'available': False}

def serialize(doc):
    if not doc:
        return None
    result = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, dict):
            result[k] = serialize(v)
        elif isinstance(v, list):
            result[k] = [serialize(i) if isinstance(i, dict) else i for i in v]
        else:
            result[k] = v
    return result


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'database': 'mongodb' if using_mongodb else 'in-memory', 'ollama': check_ollama()})


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data or not data.get('clientUrl') or not data.get('clientName'):
        return jsonify({'error': 'Missing clientUrl or clientName'}), 400
    
    try:
        project = {
            'client_name': data['clientName'],
            'client_url': data['clientUrl'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'competitors': [c.strip() for c in data.get('competitors', []) if c and c.strip()],
            'created_at': datetime.utcnow()
        }
        
        result = db.projects.insert_one(project)
        project_id = result.inserted_id
        
        # Prepare client info for v6 pipeline
        client_info = {
            'name': data['clientName'], 
            'location': data.get('location', ''), 
            'industry': data.get('industry', '')
        }
        
        # v6 run_analysis signature: (client_url, competitor_urls, client_info, project_id)
        # It returns a dict directly, not an object we need to process differently
        results = pipeline.run_analysis(
            client_url=data['clientUrl'],
            competitor_urls=project['competitors'],
            client_info=client_info,
            project_id=str(project_id)
        )
        
        project_with_results = {**project, '_id': project_id, 'results': results}
        
        # Check if v6 has generate_prompt, otherwise fallback or skip
        if hasattr(pipeline, 'generate_prompt'):
            results['generatedPrompt'] = pipeline.generate_prompt(project_with_results)
        else:
            results['generatedPrompt'] = "Prompt generation not supported in v6 pipeline."
        
        db.projects.update_one({'_id': project_id}, {'$set': {'results': results, 'updated_at': datetime.utcnow()}})
        
        return jsonify({'success': True, 'project_id': str(project_id), 'results': results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-website', methods=['POST'])
def generate_website():
    data = request.json
    project_id = data.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'Missing project_id'}), 400
    
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if hasattr(pipeline, 'generate_prompt'):
            prompt = data.get('custom_prompt') or pipeline.generate_prompt(project)
        else:
            prompt = data.get('custom_prompt') or f"Generate a website for {project.get('client_name')}"
        
        ollama = check_ollama()
        if not ollama['connected']:
            return jsonify({'error': 'Ollama not running'}), 503
        if not ollama['available']:
            return jsonify({'error': f'Run: ollama pull {OLLAMA_MODEL}'}), 503
        
        import time
        start = time.time()
        
        response = requests.post(
            f'{OLLAMA_HOST}/api/generate',
            json={'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.7, 'num_predict': 6000}},
            timeout=120
        )
        response.raise_for_status()
        
        html = response.json().get('response', '')
        if '```html' in html:
            html = html.split('```html')[1].split('```')[0]
        elif '```' in html:
            parts = html.split('```')
            html = parts[1] if len(parts) > 1 else html
        html = html.strip()
        
        duration = time.time() - start
        
        # v6 might not have validate_and_improve
        if hasattr(pipeline, 'validate_and_improve'):
            validation = pipeline.validate_and_improve(html)
        else:
            validation = {'score': 0, 'issues': [], 'suggestions': []}

        
        db.projects.update_one({'_id': ObjectId(project_id)}, {'$set': {'generated_html': html, 'generation_time': duration, 'validation': validation}})
        
        return jsonify({'success': True, 'html': html, 'model': OLLAMA_MODEL, 'generation_time': round(duration, 1), 'validation': validation})
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout'}), 504
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/geo-analyze', methods=['POST'])
def geo_analyze():
    """GEO Analysis - FIXED"""
    data = request.json
    if not data or not data.get('url'):
        return jsonify({'error': 'Missing url'}), 400
    
    try:
        # v6 might not have analyze_geo_only
        if hasattr(pipeline, 'analyze_geo_only'):
            result = pipeline.analyze_geo_only(data['url'])
            return jsonify(result)
        else:
            return jsonify({'error': 'Quick GEO analysis not supported in v6 pipeline', 'success': False}), 501
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/report/<project_id>')
def get_report(project_id):
    """Download HTML Report"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Not found'}), 404
        
        # v6 might not have generate_report
        if hasattr(pipeline, 'generate_report'):
            report = pipeline.generate_report(project)
            return Response(report, mimetype='text/html', headers={'Content-Disposition': f'attachment; filename=report-{project_id}.html'})
        else:
            return jsonify({'error': 'Report generation not supported in v6 pipeline'}), 501
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/<project_id>/json')
def get_report_json(project_id):
    """Report as JSON"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Not found'}), 404
        
        results = project.get('results', {})
        return jsonify({
            'clientName': project.get('client_name'),
            'scores': {'overall': results.get('overallScore'), 'seo': results.get('seoScore'), 'geo': results.get('geoScore')},
            'htmlImprovements': results.get('htmlImprovements', []),
            'keywords': results.get('topKeywords', []),
            'recommendations': results.get('recommendations', [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects')
def list_projects():
    return jsonify([serialize(p) for p in db.projects.find()])


@app.route('/api/project/<pid>')
def get_project(pid):
    try:
        p = db.projects.find_one({'_id': ObjectId(pid)})
        return jsonify(serialize(p)) if p else (jsonify({'error': 'Not found'}), 404)
    except:
        return jsonify({'error': 'Invalid ID'}), 400


@app.route('/api/project/<pid>', methods=['DELETE'])
def delete_project(pid):
    try:
        r = db.projects.delete_one({'_id': ObjectId(pid)})
        return jsonify({'success': True}) if r.deleted_count else (jsonify({'error': 'Not found'}), 404)
    except:
        return jsonify({'error': 'Invalid ID'}), 400


@app.route('/api/metrics/<project_id>')
def get_metrics(project_id):
    """Get NLP model metrics for a project"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        if not project:
            return jsonify({'error': 'Not found'}), 404
        
        results = project.get('results', {})
        metrics = results.get('nlpMetrics', {})
        
        if not metrics:
            return jsonify({'error': 'No metrics available for this project'}), 404
        
        return jsonify({
            'project_id': project_id,
            'clientName': project.get('client_name'),
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/project/<pid>/html')
def get_html(pid):
    try:
        p = db.projects.find_one({'_id': ObjectId(pid)})
        if p and p.get('generated_html'):
            return Response(p['generated_html'], mimetype='text/html')
        return jsonify({'error': 'No HTML'}), 404
    except:
        return jsonify({'error': 'Invalid ID'}), 400


@app.route('/api/validate', methods=['POST'])
def validate_html():
    """Validate HTML with dynamic checks"""
    html = request.json.get('html', '')
    if not html:
        return jsonify({'error': 'Missing html'}), 400
        
    # v6 fallback
    if hasattr(pipeline, 'validate_and_improve'):
        return jsonify(pipeline.validate_and_improve(html, request.json.get('targets')))
    else:
        return jsonify({'error': 'HTML validation not supported in v6 pipeline', 'score': 0, 'issues': []})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌊 SOLRISE API v7")
    print("="*60)
    
    ollama = check_ollama()
    print(f"\nDatabase: {'MongoDB ✅' if using_mongodb else 'In-Memory ⚠️'}")
    print(f"Ollama: {'✅ ' + str(ollama['models']) if ollama['connected'] else '❌ Not running'}")
    print(f"Model: {OLLAMA_MODEL} {'✅' if ollama.get('available') else '❌'}")
    
    print(f"\n📡 Endpoints:")
    print(f"   POST /api/analyze           - SEO/GEO analysis")
    print(f"   POST /api/generate-website  - Generate HTML")
    print(f"   POST /api/geo-analyze       - Quick GEO check")
    print(f"   GET  /api/report/<id>       - Download report")
    print(f"   POST /api/validate          - Validate HTML")
    
    print(f"\n🌐 http://localhost:5001\n")
    app.run(debug=True, port=5001, host='0.0.0.0')
