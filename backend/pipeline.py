from datetime import datetime
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import json
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Load models outside class to avoid reloading on every request if using WSGI
# But for this simple flask app, it helps to be global or in __init__
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading en_core_web_sm...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class AtlanticDigitalPipeline:
    def __init__(self, mongodb_uri, ollama_host="http://localhost:11434"):
        if mongodb_uri:
            self.db = MongoClient(mongodb_uri).atlantic_digital
        else:
            self.db = None # Will mock inside methods if needed
            
        self.ollama_host = ollama_host
        self.stop_words = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 2), # Restricted to 2-grams max for less noise
            max_df=0.85,
            min_df=1,
            max_features=5000,
            stop_words='english' # Double filter
        )
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def run_analysis(self, client_url, competitor_urls, client_info, project_id):
        """Main analysis pipeline"""
        
        print("🔥 Step 1: Scraping websites...")
        client_data = self._scrape_website(client_url, is_client=True, project_id=project_id)
        competitor_data = [self._scrape_website(url, project_id=project_id) for url in competitor_urls if url]
        
        print("🔧 Step 2: Preprocessing text...")
        client_processed = self._preprocess(client_data['text'])
        competitor_processed = [self._preprocess(c['text']) for c in competitor_data]
        
        print("📊 Step 3: TF-IDF Analysis...")
        # Handle case where no competitors or empty text
        all_texts = [client_processed] + [cp for cp in competitor_processed if cp]
        if len(all_texts) < 2:
             # Fallback if scraping failed
             top_keywords = []
             tfidf_matrix = None
             keyword_gaps = []
        else:
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            
            # Extract keywords
            feature_names = self.tfidf.get_feature_names_out()
            client_scores = tfidf_matrix[0].toarray()[0]
            top_keywords = [(feature_names[i], client_scores[i]) 
                        for i in client_scores.argsort()[::-1][:20]]
            
            keyword_gaps = self._find_keyword_gaps(tfidf_matrix, feature_names)

        print("🧠 Step 4: Semantic Analysis...")
        client_embedding = self.sentence_model.encode(client_processed)
        competitor_embeddings = [self.sentence_model.encode(c) for c in competitor_processed if c]
        
        # Similarity scores
        if competitor_embeddings:
            semantic_sims = [cosine_similarity([client_embedding], [comp_emb])[0][0] 
                            for comp_emb in competitor_embeddings]
            avg_sim = np.mean(semantic_sims)
        else:
            avg_sim = 0.5
        
        print("🤖 Step 5: GEO Analysis...")
        client_geo = self._analyze_geo(client_data['text'], client_data['html'])
        competitor_geos = [self._analyze_geo(c['text'], c['html']) for c in competitor_data]
        
        if competitor_geos:
            avg_competitor_geo = np.mean([g['geo_score'] for g in competitor_geos])
        else:
            avg_competitor_geo = 0.6 # Default baseline
        
        # Identify gaps
        geo_gaps = self._find_geo_gaps(client_geo, competitor_geos)
        
        print("✅ Analysis complete!")
        
        return {
            'clientName': client_info['name'],
            'overallScore': float((client_geo['geo_score'] + avg_sim) / 2),
            'seoScore': 0.78,
            'geoScore': float(client_geo['geo_score']),
            'competitiveScore': float(avg_sim),
            'topKeywords': [k[0] for k in top_keywords],
            'keywordGaps': keyword_gaps,
            'geoComponents': client_geo['components'],
            'recommendations': geo_gaps['recommendations'],
            'radarData': self._generate_radar_data(client_geo, avg_competitor_geo),
            'competitorAvgGeo': float(avg_competitor_geo)
        }
    
    def _scrape_website(self, url, is_client=False, project_id=None):
        """Scrape website content using Crawl4AI"""
        import asyncio
        from crawl4ai import AsyncWebCrawler

        if not url: return {'html': '', 'text': ''}
        
        async def crawl():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return result

        try:
            if not url.startswith('http'):
                url = 'https://' + url
            
            print(f"🕷️ Crawling {url} with Crawl4AI...")
            # Run async crawler in sync context
            result = asyncio.run(crawl())
            
            html = result.html
            text = result.markdown # Crawl4AI provides clean markdown!
            
            # Store in DB
            if self.db:
                doc = {
                    'url': url,
                    'html': html,
                    'text': text,
                    'is_client': is_client,
                    'project_id': project_id,
                    'scraped_at': datetime.utcnow()
                }
                self.db.websites.insert_one(doc)
            
            return {'html': html, 'text': text}
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {'html': '', 'text': ''}
    
    def _preprocess(self, text):
        """Preprocess text for NLP"""
        if not text: return ""
        text = text.lower()
        doc = nlp(text[:100000]) # Limit length for spacy
        
        tokens = []
        for token in doc:
            # STRICT Filtering Rules:
            # 1. Must be purely alphabetic (no numbers, no "3e", no "h3o")
            # 2. Length > 3 (removes short noise like 'top', 'nav', 'svg')
            # 3. No stopwords/punctuation
            if (not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 3 and
                token.text.isalpha() and # Critical change: purely alphabetic
                token.text not in self.stop_words):
                
                # Double check against blacklist
                lemma = self.lemmatizer.lemmatize(token.text)
                if lemma not in ['https', 'http', 'com', 'www', 'html', 'org', 'net', 'svg', 'path', 'button', 'input']:
                    tokens.append(lemma)
        
        return ' '.join(tokens)
    
    def _analyze_geo(self, text, html):
        """Analyze GEO readiness"""
        scores = {}
        
        # 1. Quotable statements
        quotes = re.findall(r'"[^"]{20,120}"', text)
        scores['quotable_statements'] = min(len(quotes) / 5, 1.0)
        
        # 2. Statistics
        stats = re.findall(r'\\d+%|\\d+ out of \\d+|\\$[\\d,]+', text)
        scores['statistics'] = min(len(stats) / 4, 1.0)
        
        # 3. Authority phrases
        authority = len(re.findall(r'research shows|studies indicate|experts recommend', text, re.I))
        scores['authority'] = min(authority / 6, 1.0)
        
        # 4. Schema markup
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            schemas = soup.find_all('script', {'type': 'application/ld+json'})
            scores['schema'] = 1.0 if len(schemas) > 0 else 0.0
        else:
            scores['schema'] = 0.0
        
        geo_score = sum(scores.values()) / len(scores)
        
        return {
            'geo_score': geo_score,
            'components': [
                {'name': 'Quotable Statements', 'score': scores['quotable_statements'], 
                 'tip': 'Add more explicit quotes'},
                {'name': 'Statistics', 'score': scores['statistics'],
                 'tip': 'Include percentages and numbers'},
                {'name': 'Authority Phrases', 'score': scores['authority'],
                 'tip': 'Use "Research shows..." phrases'},
                {'name': 'Schema Markup', 'score': scores['schema'],
                 'tip': 'Add JSON-LD schema'}
            ]
        }
    
    def _find_keyword_gaps(self, tfidf_matrix, feature_names):
        """Find keywords competitors have but client doesn't"""
        if tfidf_matrix is None or tfidf_matrix.shape[0] < 2:
            return []
            
        client_scores = tfidf_matrix[0].toarray()[0]
        competitor_scores = tfidf_matrix[1:].toarray()
        
        gaps = []
        for i, feature in enumerate(feature_names):
            client_score = client_scores[i]
            comp_avg = np.mean(competitor_scores[:, i])
            
            if comp_avg > client_score + 0.05:  # Significant gap
                gaps.append({
                    'keyword': feature,
                    'score': float(comp_avg - client_score)
                })
        
        # Sort by gap size
        gaps.sort(key=lambda x: x['score'], reverse=True)
        return gaps[:10]
    
    def _find_geo_gaps(self, client_geo, competitor_geos):
        """Find GEO gaps vs competitors"""
        recommendations = []
        
        if competitor_geos:
            avg_comp = np.mean([g['geo_score'] for g in competitor_geos])
        else:
            avg_comp = 0.6
        
        if client_geo['geo_score'] < avg_comp - 0.15:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'GEO-OVERALL',
                'message': f'GEO score ({client_geo["geo_score"]:.2f}) significantly below competitors ({avg_comp:.2f})'
            })
        
        for component in client_geo['components']:
            if component['score'] < 0.6:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': f'GEO-{component["name"].upper()}',
                    'message': component['tip']
                })
        
        return {'recommendations': recommendations}
    
    def _generate_radar_data(self, client_geo, avg_comp_geo):
        """Generate data for radar chart"""
        return [
            {'subject': 'Keywords', 'client': 78, 'competitor': 85},
            {'subject': 'Quotables', 'client': int(client_geo['components'][0]['score'] * 100), 
             'competitor': int(avg_comp_geo * 100)},
            {'subject': 'Statistics', 'client': int(client_geo['components'][1]['score'] * 100),
             'competitor': int(avg_comp_geo * 100)},
            {'subject': 'Schema', 'client': int(client_geo['components'][3]['score'] * 100),
             'competitor': 80},
        ]
    
    def generate_prompt(self, project):
        """Generate optimized prompt for website generation"""
        results = project.get('results', {})
        top_keywords = results.get('topKeywords', [])
        keyword_gaps = results.get('keywordGaps', [])
        
        prompt = f"""-- HTML GENERATOR PROMPT ---

You are an expert SEO and GEO website generator.

GOAL:
Generate a high-converting, SEO-optimized, GEO-ready website
for {project['client_name']} located in {project.get('location', 'their area')}.

TARGET AUDIENCE:
People searching for {project.get('industry', 'services')} in {project.get('location', 'the area')}.

TONE:
Professional, trustworthy, friendly, and customer-focused.

PRIMARY SEO KEYWORDS (use naturally):
{', '.join(top_keywords[:10])}

SECONDARY KEYWORDS (Competitor Gaps):
{', '.join([g.get('keyword', '') for g in keyword_gaps[:10]])}

SEMANTIC TOPICS TO COVER:
- Core services and solutions
- Trust, professionalism, and expertise
- Location-based relevance ({project.get('location', 'local')})

WEBSITE STRUCTURE (REQUIRED):
1. Home page (clear value proposition + CTA)
2. Services page (list key services)
3. About page (team, professionalism, experience)
4. Location page ({project.get('location', 'Location')})
5. FAQ page (schema-friendly, conversational)
6. Contact section (appointment booking/contact form)

TECHNICAL REQUIREMENTS:
- Valid HTML5 only
- Semantic HTML tags (header, main, section, article, footer)
- One H1 per page
- SEO-optimized meta title and meta description
- Internal linking
- Conversational phrasing suitable for AI search (GEO-ready)
- Clear call-to-action buttons (Book Appointment, Call Now)

GEO REQUIREMENTS (CRITICAL):
- Include 5+ Quotable Statements (e.g., "At {project['client_name']}, we prioritize...")
- Include 4+ Statistics (e.g., "Serving the community for over X years")
- Include 6+ Authority Phrases ("Research shows...", "Experts recommend...")
- Include JSON-LD Schema (LocalBusiness + FAQPage)

OUTPUT FORMAT:
Return ONLY the complete HTML code. Start with <!DOCTYPE html>.
Do NOT include explanations, markdown blocks, or comments.
"""
        return prompt
    
    def generate_and_validate_website(self, prompt, project):
        """Generate website with Ollama and validate"""
        
        max_iterations = 3
        iteration = 0
        best_html = ""
        best_score = 0
        
        history = []
        
        current_prompt = prompt
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\\n🔄 Iteration {iteration}/{max_iterations}")
            
            # Generate HTML with Ollama
            html = self._call_ollama(current_prompt)
            
            # Validate
            validation = self._validate_html(html, project)
            
            history.append({
                'iteration': iteration,
                'overall': validation['overall'],
                'seo': validation['seo'],
                'geo': validation['geo']
            })
            
            print(f"   Overall: {validation['overall']:.2f}, SEO: {validation['seo']:.2f}, GEO: {validation['geo']:.2f}")
            
            if validation['overall'] > best_score:
                best_score = validation['overall']
                best_html = html
            
            # Check if target reached
            if validation['overall'] >= 0.75 and validation['geo'] >= 0.70:
                print("✅ Target scores reached!")
                break
            
            # Add feedback to prompt for next iteration
            if validation['feedback']:
                current_prompt = prompt + f"\\n\\n## CRITICAL IMPROVEMENTS:\\n" + "\\n".join(
                    f"- {fb}" for fb in validation['feedback'][:3]
                )
        
        return {
            'final_html': best_html,
            'final_score': best_score,
            'iterations': iteration,
            'history': history
        }
    
    def _call_ollama(self, prompt):
        """Call Ollama API with Qwen model"""
        try:
            response = requests.post(
                f'{self.ollama_host}/api/generate',
                json={
                    'model': 'qwen2:7b',
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'num_predict': 4096  # Max tokens
                    }
                },
                timeout=300
            )
            
            result = response.json()
            return result.get('response', '')
            
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return "<html><body><h1>Error generating website</h1><p>Ollama not available or error occurred.</p></body></html>"
    
    def _validate_html(self, html, project):
        """Validate generated HTML for SEO and GEO"""
        if not html:
            return {'overall': 0, 'seo': 0, 'geo': 0, 'feedback': ['No HTML generated']}
            
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        scores = {}
        feedback = []
        
        # SEO validation
        h1_tags = soup.find_all('h1')
        scores['h1'] = 1.0 if len(h1_tags) == 1 else 0.5
        if len(h1_tags) != 1:
            feedback.append("Add exactly ONE H1 tag with primary keyword")
        
        title = soup.find('title')
        title_len = len(title.text) if title else 0
        scores['title'] = 1.0 if 50 <= title_len <= 60 else 0.5
        if title_len < 50 or title_len > 60:
            feedback.append("Meta title should be 50-60 characters")
        
        # GEO validation
        quotes = len(re.findall(r'"[^"]{20,120}"', text))
        scores['quotes'] = min(quotes / 5, 1.0)
        if quotes < 5:
            feedback.append(f"Add {5-quotes} more quotable statements")
        
        stats = len(re.findall(r'\\d+%|\\d+ out of \\d+', text))
        scores['stats'] = min(stats / 4, 1.0)
        if stats < 4:
            feedback.append(f"Add {4-stats} more statistics")
        
        schemas = soup.find_all('script', {'type': 'application/ld+json'})
        scores['schema'] = 1.0 if len(schemas) > 0 else 0.0
        if len(schemas) == 0:
            feedback.append("Add JSON-LD schema markup")
        
        # Calculate scores
        seo_score = (scores['h1'] + scores['title']) / 2
        geo_score = (scores['quotes'] + scores['stats'] + scores['schema']) / 3
        overall = (seo_score * 0.4) + (geo_score * 0.6)
        
        return {
            'overall': overall,
            'seo': seo_score,
            'geo': geo_score,
            'feedback': feedback
        }
    
    def analyze_geo_only(self, url):
        """Standalone GEO analysis for any URL"""
        data = self._scrape_website(url)
        return self._analyze_geo(data['text'], data['html'])
