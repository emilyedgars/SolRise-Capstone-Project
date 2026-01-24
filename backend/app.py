from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import json

# Import your analysis pipeline
from pipeline import AtlanticDigitalPipeline

app = Flask(__name__)
CORS(app)  # Allow React frontend to connect

# Mock DB for Demo Mode (when MongoDB is not installed)
class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {}
    
    def insert_one(self, doc):
        if '_id' not in doc:
            doc['_id'] = ObjectId()
        self.data[str(doc['_id'])] = doc
        print(f"📝 [MockDB] Inserted into {self.name}: {doc['_id']}")
        return doc
    
    def find_one(self, query):
        if '_id' in query and isinstance(query['_id'], ObjectId):
            return self.data.get(str(query['_id']))
        # Simple fallback for other queries (not perfect but works for this app)
        for item in self.data.values():
            match = True
            for k, v in query.items():
                if k == '_id': continue
                if item.get(k) != v:
                    match = False
                    break
            if match: return item
        return None

    def find(self, query=None):
        class Cursor:
            def __init__(self, data): self.data = data
            def sort(self, key, direction): return self.data # Ignore sort in mock
            def __iter__(self): return iter(self.data)
            def __list__(self): return self.data
        
        if not query:
            return Cursor(list(self.data.values()))
        return Cursor([x for x in self.data.values()]) # Return all for simplicity in demo

    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc:
            if '$set' in update:
                doc.update(update['$set'])
            print(f"🔄 [MockDB] Updated {self.name}: {doc.get('_id')}")

class MockDatabase:
    def __init__(self):
        self.projects = MockCollection('projects')
        self.websites = MockCollection('websites')
        print("⚠️  Running in DEMO MODE (No MongoDB detected). Data will be lost on restart.")

# MongoDB connection with Fallback
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.server_info() # Trigger connection check
    db = client.atlantic_digital
    pipeline_db_uri = 'mongodb://localhost:27017/'
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection failed ({str(e)})")
    db = MockDatabase()
    pipeline_db_uri = None # Signal pipeline to use mock or skip

# Initialize pipeline
pipeline = AtlanticDigitalPipeline(
    mongodb_uri=pipeline_db_uri,
    ollama_host='http://localhost:11434'
)

# ========================================
# API ENDPOINTS
# ========================================

@app.route('/api/analyze', methods=['POST'])
def run_analysis():
    """
    Endpoint: Start new SEO/GEO analysis
    Request body: {
        clientUrl, clientName, location, industry,
        competitors: [url1, url2, url3]
    }
    """
    data = request.json
    
    try:
        # Validate input
        if not data.get('clientUrl') or not data.get('clientName'):
            return jsonify({'error': 'Missing required fields'}), 400
        
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
            'created_at': datetime.now(), # Using local time for simplicity or use timezone aware
            'updated_at': datetime.now()
        }
        db.projects.insert_one(project)
        
        # Run analysis in background (for production, use Celery/Redis)
        # For now, we'll run synchronously
        client_info = {
            'name': data['clientName'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'target_audience': data.get('targetAudience', 'general public'),
            'services': data.get('services', [])
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
        
        # Generate prompt immediately for display
        prompt_project_mock = {
            'client_name': data['clientName'],
            'location': data.get('location', ''),
            'industry': data.get('industry', ''),
            'results': result
        }
        generated_prompt = pipeline.generate_prompt(prompt_project_mock)
        result['generatedPrompt'] = generated_prompt

        return jsonify({
            'success': True,
            'project_id': str(project_id),
            'results': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    projects = list(db.projects.find().sort('created_at', -1))
    
    # Convert ObjectId to string for JSON serialization
    for project in projects:
        project['_id'] = str(project['_id'])
        project['created_at'] = project['created_at'].isoformat()
        project['updated_at'] = project['updated_at'].isoformat()
    
    return jsonify(projects)


@app.route('/api/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get specific project details"""
    try:
        project = db.projects.find_one({'_id': ObjectId(project_id)})
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        project['_id'] = str(project['_id'])
        project['created_at'] = project['created_at'].isoformat()
        project['updated_at'] = project['updated_at'].isoformat()
        
        return jsonify(project)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-website', methods=['POST'])
def generate_website():
    """
    Generate optimized website HTML
    Request: {
        project_id: string,
        custom_prompt?: string  # Optional: employee can edit prompt
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
    
        # Generate optimized prompt
        base_prompt = pipeline.generate_prompt(project)
        
        # Allow employee to customize prompt
        final_prompt = data.get('custom_prompt', base_prompt)
        
        # Generate website using Ollama/Qwen
        html_result = pipeline.generate_and_validate_website(
            prompt=final_prompt,
            project=project
        )
        
        # Save generated website
        db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': {
                'generated_html': html_result['final_html'],
                'generation_prompt': final_prompt,
                'generation_score': html_result['final_score'],
                'generation_iterations': html_result['iterations'],
                'updated_at': datetime.now()
            }}
        )
        
        return jsonify({
            'success': True,
            'html': html_result['final_html'],
            'score': html_result['final_score'],
            'iterations': html_result['iterations'],
            'base_prompt': base_prompt  # Send back for editing
        })
        
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
            # Return generated HTML
            html = project.get('generated_html', '<p>No HTML generated yet</p>')
            return html, 200, {'Content-Type': 'text/html'}
        
        else:
            # Return JSON
            project['_id'] = str(project['_id'])
            project['created_at'] = project['created_at'].isoformat()
            project['updated_at'] = project['updated_at'].isoformat()
            
            return jsonify(project), 200, {
                'Content-Disposition': f'attachment; filename=project_{project_id}.json'
            }
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
