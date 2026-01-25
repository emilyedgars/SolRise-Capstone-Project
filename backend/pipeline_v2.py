"""
Atlantic Digital - SEO/GEO Pipeline v3
======================================
- Fixed GEO validation regex
- Single-pass generation (no iterations)
- Optimized prompt for GEO
- Faster timeouts
"""

from datetime import datetime
import asyncio
import re
import json
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
from bs4 import BeautifulSoup
import requests

# Load spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


@dataclass
class ScrapedContent:
    url: str
    html: str
    text: str
    title: str
    meta_description: str
    headings: Dict[str, List[str]]
    schema_data: List[dict]
    word_count: int
    success: bool
    error: Optional[str] = None


@dataclass 
class GEOScore:
    overall_score: float
    quotable_statements: float
    statistics_density: float
    authoritative_language: float
    definitive_openers: float
    schema_markup: float
    entity_clarity: float
    faq_quality: float
    details: dict = field(default_factory=dict)


class AtlanticDigitalPipeline:
    
    def __init__(self, mongodb_uri: Optional[str] = None, ollama_host: str = "http://localhost:11434"):
        # Database
        self.db = None
        if mongodb_uri:
            try:
                from pymongo import MongoClient
                self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
                self.client.server_info()
                self.db = self.client.atlantic_digital
                print("✅ Connected to MongoDB")
            except Exception as e:
                print(f"⚠️ MongoDB unavailable: {e}")
        
        self.ollama_host = ollama_host
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 3),
            max_df=0.85,
            min_df=1,
            max_features=5000,
            stop_words='english',
            token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z]+\b'
        )
        
        self.noise_words = {
            'https', 'http', 'www', 'com', 'org', 'html', 'css', 'svg', 'png',
            'button', 'click', 'menu', 'nav', 'footer', 'header', 'sidebar',
            'cookie', 'privacy', 'policy', 'terms', 'subscribe', 'newsletter'
        }

    # =========================================================================
    # MAIN ANALYSIS
    # =========================================================================
    
    def run_analysis(self, client_url: str, competitor_urls: List[str], 
                     client_info: dict, project_id=None) -> dict:
        """Run complete SEO/GEO analysis"""
        
        print("\n" + "="*60)
        print("🚀 ATLANTIC DIGITAL SEO/GEO ANALYSIS")
        print("="*60)
        
        business_name = client_info.get('name', '').lower()
        location = client_info.get('location', '').lower()
        industry = client_info.get('industry', '').lower()
        
        # Step 1: Scrape
        print("\n📥 STEP 1: Scraping...")
        client_data = self._scrape_website(client_url)
        if not client_data.success:
            return self._error_results(client_info, client_data.error)
        print(f"   ✓ Client: {client_data.word_count} words")
        
        competitor_data = []
        for url in competitor_urls:
            if url and url.strip():
                comp = self._scrape_website(url)
                if comp.success:
                    competitor_data.append(comp)
                    print(f"   ✓ Competitor: {comp.word_count} words")
        
        # Step 2: Preprocess
        print("\n🔧 STEP 2: Preprocessing...")
        client_processed = self._preprocess(client_data.text)
        competitor_processed = [self._preprocess(c.text) for c in competitor_data]
        
        # Step 3: TF-IDF
        print("\n📊 STEP 3: TF-IDF Keywords...")
        all_texts = [client_processed] + [cp for cp in competitor_processed if cp]
        
        if len(all_texts) >= 2 and all(len(t) > 50 for t in all_texts):
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            feature_names = self.tfidf.get_feature_names_out()
            
            client_scores = tfidf_matrix[0].toarray()[0]
            top_idx = client_scores.argsort()[::-1][:20]
            top_keywords = [(feature_names[i], float(client_scores[i])) for i in top_idx if client_scores[i] > 0]
            
            keyword_gaps = self._find_keyword_gaps(tfidf_matrix, feature_names)
            print(f"   ✓ {len(top_keywords)} keywords, {len(keyword_gaps)} gaps")
        else:
            top_keywords = []
            keyword_gaps = []
        
        # Step 4: Semantic
        print("\n🧠 STEP 4: Semantic Analysis...")
        try:
            client_emb = self._get_embedding(client_processed)
            if competitor_processed:
                comp_embs = [self._get_embedding(cp) for cp in competitor_processed if cp]
                sims = [float(cosine_similarity([client_emb], [ce])[0][0]) for ce in comp_embs]
                avg_sim = np.mean(sims)
            else:
                avg_sim = 0.5
            print(f"   ✓ Similarity: {avg_sim:.2f}")
        except:
            avg_sim = 0.5
        
        # Step 5: GEO Analysis
        print("\n🤖 STEP 5: GEO Analysis...")
        client_geo = self._analyze_geo(client_data, business_name, location)
        print(f"   ✓ GEO Score: {client_geo.overall_score:.2f}")
        
        comp_geo_scores = [self._analyze_geo(c).overall_score for c in competitor_data]
        avg_comp_geo = np.mean(comp_geo_scores) if comp_geo_scores else 0.6
        
        # Step 6: Structure
        print("\n📝 STEP 6: Structure Analysis...")
        structure = self._analyze_structure(client_data)
        
        # Compile results
        print("\n✅ COMPLETE!")
        
        seo_score = self._calc_seo_score(structure, top_keywords)
        overall = (seo_score * 0.4) + (client_geo.overall_score * 0.5) + (avg_sim * 0.1)
        
        return {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': round(overall, 2),
            'seoScore': round(seo_score, 2),
            'geoScore': round(client_geo.overall_score, 2),
            'competitiveScore': round(avg_sim, 2),
            'competitorAvgGeo': round(avg_comp_geo, 2),
            'topKeywords': [{'keyword': k[0], 'score': round(k[1], 3)} for k in top_keywords[:15]],
            'keywordGaps': keyword_gaps[:10],
            'geoComponents': [
                {'name': 'Quotable Statements', 'score': round(client_geo.quotable_statements, 2),
                 'tip': 'Add statements like "At [Business], we believe..."'},
                {'name': 'Statistics', 'score': round(client_geo.statistics_density, 2),
                 'tip': 'Include percentages, years, customer counts'},
                {'name': 'Authority', 'score': round(client_geo.authoritative_language, 2),
                 'tip': 'Use "Research shows...", "Experts recommend..."'},
                {'name': 'Definitive Openers', 'score': round(client_geo.definitive_openers, 2),
                 'tip': 'Start paragraphs with facts, not questions'},
                {'name': 'Schema Markup', 'score': round(client_geo.schema_markup, 2),
                 'tip': 'Add JSON-LD LocalBusiness + FAQPage'},
                {'name': 'Entity Clarity', 'score': round(client_geo.entity_clarity, 2),
                 'tip': 'Mention business name 8+ times'},
                {'name': 'FAQ Quality', 'score': round(client_geo.faq_quality, 2),
                 'tip': 'Add 8-10 FAQs with clear answers'}
            ],
            'radarData': [
                {'subject': 'Keywords', 'client': int(min(len(top_keywords)/15, 1) * 100), 'competitor': 75},
                {'subject': 'Quotables', 'client': int(client_geo.quotable_statements * 100), 'competitor': int(avg_comp_geo * 100)},
                {'subject': 'Statistics', 'client': int(client_geo.statistics_density * 100), 'competitor': 70},
                {'subject': 'Schema', 'client': int(client_geo.schema_markup * 100), 'competitor': 70},
                {'subject': 'Authority', 'client': int(client_geo.authoritative_language * 100), 'competitor': 65},
                {'subject': 'Structure', 'client': int(seo_score * 100), 'competitor': 80}
            ],
            'recommendations': self._generate_recommendations(client_geo, keyword_gaps, structure),
            'debug': {'word_count': client_data.word_count, 'competitors': len(competitor_data)}
        }

    # =========================================================================
    # SCRAPING
    # =========================================================================
    
    def _scrape_website(self, url: str) -> ScrapedContent:
        if not url:
            return ScrapedContent(url='', html='', text='', title='', meta_description='',
                                 headings={}, schema_data=[], word_count=0, success=False, error='Empty URL')
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        try:
            return self._scrape_crawl4ai(url)
        except Exception as e:
            print(f"   ⚠️ Crawl4AI failed: {e}, trying requests...")
            try:
                return self._scrape_requests(url)
            except Exception as e2:
                return ScrapedContent(url=url, html='', text='', title='', meta_description='',
                                     headings={}, schema_data=[], word_count=0, success=False, error=str(e2))
    
    def _scrape_crawl4ai(self, url: str) -> ScrapedContent:
        from crawl4ai import AsyncWebCrawler
        
        async def crawl():
            async with AsyncWebCrawler(verbose=False) as crawler:
                return await crawler.arun(url=url)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(crawl())
        
        html = result.html or ''
        text = result.markdown or ''
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('title')
        title = title.get_text().strip() if title else ''
        
        meta = soup.find('meta', {'name': 'description'})
        meta_desc = meta.get('content', '') if meta else ''
        
        headings = {
            'h1': [h.get_text().strip() for h in soup.find_all('h1')],
            'h2': [h.get_text().strip() for h in soup.find_all('h2')],
            'h3': [h.get_text().strip() for h in soup.find_all('h3')]
        }
        
        schema_data = []
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                schema_data.append(json.loads(script.string))
            except:
                pass
        
        return ScrapedContent(url=url, html=html, text=text, title=title, meta_description=meta_desc,
                             headings=headings, schema_data=schema_data, word_count=len(text.split()), success=True)
    
    def _scrape_requests(self, url: str) -> ScrapedContent:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for el in soup.find_all(['script', 'style', 'nav', 'footer']):
            el.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        title = soup.find('title')
        meta = soup.find('meta', {'name': 'description'})
        
        return ScrapedContent(
            url=url, html=response.text, text=text,
            title=title.get_text().strip() if title else '',
            meta_description=meta.get('content', '') if meta else '',
            headings={'h1': [h.get_text().strip() for h in soup.find_all('h1')],
                     'h2': [h.get_text().strip() for h in soup.find_all('h2')],
                     'h3': [h.get_text().strip() for h in soup.find_all('h3')]},
            schema_data=[],
            word_count=len(text.split()),
            success=True
        )

    # =========================================================================
    # TEXT PROCESSING
    # =========================================================================
    
    def _preprocess(self, text: str) -> str:
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        doc = nlp(text[:100000])
        tokens = [t.lemma_ for t in doc 
                  if not t.is_stop and not t.is_punct and len(t.text) > 2 
                  and t.text.isalpha() and t.text not in self.noise_words]
        
        return ' '.join(tokens)
    
    def _get_embedding(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(384)
        words = text.split()
        chunks = [' '.join(words[i:i+500]) for i in range(0, len(words), 500)]
        if not chunks:
            return np.zeros(384)
        return np.mean(self.sentence_model.encode(chunks), axis=0)

    # =========================================================================
    # KEYWORD ANALYSIS
    # =========================================================================
    
    def _find_keyword_gaps(self, tfidf_matrix, feature_names) -> List[dict]:
        if tfidf_matrix is None or tfidf_matrix.shape[0] < 2:
            return []
        
        client_scores = tfidf_matrix[0].toarray()[0]
        comp_scores = tfidf_matrix[1:].toarray()
        
        gaps = []
        for i, feature in enumerate(feature_names):
            client = client_scores[i]
            comp_avg = np.mean(comp_scores[:, i])
            gap = comp_avg - client
            
            if gap > 0.02:
                gaps.append({
                    'keyword': feature,
                    'score': round(float(gap), 3),
                    'client': round(float(client), 3),
                    'competitor': round(float(comp_avg), 3)
                })
        
        gaps.sort(key=lambda x: x['score'], reverse=True)
        return gaps[:15]

    # =========================================================================
    # GEO ANALYSIS - FIXED REGEX!
    # =========================================================================
    
    def _analyze_geo(self, content: ScrapedContent, business_name: str = '', location: str = '') -> GEOScore:
        text = content.text or ''
        text_lower = text.lower()
        details = {}
        
        # 1. QUOTABLE STATEMENTS (25%) - FIXED REGEX
        quotable_patterns = [
            r'"[^"]{20,150}"',  # Regular quotes
            r'"[^"]{20,150}"',  # Smart quotes  
            r'(?:we believe|our mission|our goal|our approach)[^.]{15,100}\.',
        ]
        if business_name:
            quotable_patterns.append(rf'(?:at {re.escape(business_name)})[^.]+\.')
        
        quotables = []
        for pattern in quotable_patterns:
            quotables.extend(re.findall(pattern, text_lower, re.IGNORECASE))
        
        quotable_score = min(len(quotables) / 5, 1.0)
        details['quotables_found'] = len(quotables)
        
        # 2. STATISTICS (20%) - FIXED REGEX
        stat_patterns = [
            r'\d+\s*%',  # Percentages like "95%"
            r'\d+\s*(?:years?|months?)\s*(?:of)?\s*(?:experience|serving)',  # Years experience
            r'(?:over|more than|nearly)\s*[\d,]+\s*(?:customers?|clients?|patients?|families?)',
            r'\d+\s*out of\s*\d+',  # "9 out of 10"
            r'(?:since|established|founded)\s*(?:in\s*)?\d{4}',  # Since 2010
            r'\d+\+?\s*(?:locations?|offices?|stores?)',  # 5+ locations
            r'[\d,]+\s*(?:sq\.?\s*ft|square feet)',  # Square footage
            r'\$[\d,]+',  # Dollar amounts
        ]
        
        stats = []
        for pattern in stat_patterns:
            stats.extend(re.findall(pattern, text_lower, re.IGNORECASE))
        
        stats_score = min(len(stats) / 4, 1.0)
        details['stats_found'] = len(stats)
        details['stats_examples'] = stats[:5]
        
        # 3. AUTHORITATIVE LANGUAGE (15%) - FIXED REGEX
        authority_patterns = [
            r'(?:studies?|research)\s+(?:show|indicate|suggest|demonstrate|prove)',
            r'(?:according to|based on)\s+(?:research|studies|data|experts?)',
            r'(?:experts?|specialists?|professionals?)\s+(?:recommend|suggest|advise)',
            r'(?:board[- ]?certified|licensed|accredited|certified)',
            r'(?:clinically|scientifically|medically)\s+(?:proven|tested|validated)',
            r'(?:industry[- ]?leading|award[- ]?winning|top[- ]?rated)',
        ]
        
        authority_count = sum(len(re.findall(p, text_lower)) for p in authority_patterns)
        authority_score = min(authority_count / 6, 1.0)
        details['authority_found'] = authority_count
        
        # 4. DEFINITIVE OPENERS (15%)
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 30][:15]
        
        definitive_patterns = [
            r'^(?:The|Our|We|This|Here|Yes|No|At)\s',
            r'^\d',
            r'^[A-Z][a-z]+\s+(?:is|are|was|were|has|have|provide|offer)',
        ]
        
        definitive = sum(1 for p in paragraphs if any(re.match(pat, p) for pat in definitive_patterns))
        definitive_score = definitive / max(len(paragraphs), 1)
        details['definitive_openers'] = definitive
        details['paragraphs_checked'] = len(paragraphs)
        
        # 5. SCHEMA MARKUP (10%)
        schema_types = set()
        for schema in content.schema_data:
            if isinstance(schema, dict):
                st = schema.get('@type', '')
                if isinstance(st, list):
                    schema_types.update(st)
                else:
                    schema_types.add(st)
                if '@graph' in schema:
                    for item in schema['@graph']:
                        if isinstance(item, dict):
                            it = item.get('@type', '')
                            schema_types.add(it) if isinstance(it, str) else schema_types.update(it)
        
        important = {'LocalBusiness', 'Organization', 'FAQPage', 'Service', 'Product', 'Review'}
        found_important = schema_types & important
        schema_score = min(len(found_important) / 2, 1.0)
        details['schema_types'] = list(schema_types)
        
        # 6. ENTITY CLARITY (10%)
        if business_name and len(business_name) > 2:
            name_count = text_lower.count(business_name)
            name_score = min(name_count / 8, 1.0)
        else:
            name_score = 0.5
        
        if location and len(location) > 2:
            loc_count = text_lower.count(location)
            loc_score = min(loc_count / 5, 1.0)
        else:
            loc_score = 0.5
        
        entity_score = (name_score + loc_score) / 2
        details['name_mentions'] = name_count if business_name else 'N/A'
        details['location_mentions'] = loc_count if location else 'N/A'
        
        # 7. FAQ QUALITY (5%)
        has_faq = bool(re.search(r'(?:faq|frequently\s+asked|common\s+questions)', text_lower))
        has_faq_schema = 'FAQPage' in schema_types
        qa_count = len(re.findall(r'(?:^|\n)\s*(?:q:|question:?|what|how|why|when|where|who)\s*[^\n?]+\?', text_lower, re.MULTILINE))
        
        if has_faq_schema:
            faq_score = 1.0
        elif has_faq and qa_count >= 5:
            faq_score = 0.8
        elif has_faq or qa_count >= 3:
            faq_score = 0.5
        else:
            faq_score = 0.2
        
        details['has_faq'] = has_faq
        details['qa_count'] = qa_count
        
        # OVERALL
        overall = (
            quotable_score * 0.25 +
            stats_score * 0.20 +
            authority_score * 0.15 +
            definitive_score * 0.15 +
            schema_score * 0.10 +
            entity_score * 0.10 +
            faq_score * 0.05
        )
        
        return GEOScore(
            overall_score=overall,
            quotable_statements=quotable_score,
            statistics_density=stats_score,
            authoritative_language=authority_score,
            definitive_openers=definitive_score,
            schema_markup=schema_score,
            entity_clarity=entity_score,
            faq_quality=faq_score,
            details=details
        )

    # =========================================================================
    # STRUCTURE ANALYSIS
    # =========================================================================
    
    def _analyze_structure(self, content: ScrapedContent) -> dict:
        return {
            'h1_tags': content.headings.get('h1', []),
            'h2_tags': content.headings.get('h2', []),
            'title': content.title,
            'title_length': len(content.title),
            'meta_description': content.meta_description,
            'meta_length': len(content.meta_description),
            'has_faq': bool(re.search(r'faq', content.text.lower())) if content.text else False,
            'schema_types': [s.get('@type', '') for s in content.schema_data if isinstance(s, dict)]
        }
    
    def _calc_seo_score(self, structure: dict, keywords: List) -> float:
        scores = []
        h1_count = len(structure['h1_tags'])
        scores.append(1.0 if h1_count == 1 else 0.5 if h1_count > 0 else 0.0)
        
        title_len = structure['title_length']
        scores.append(1.0 if 50 <= title_len <= 60 else 0.6 if 40 <= title_len <= 70 else 0.3)
        
        meta_len = structure['meta_length']
        scores.append(1.0 if 150 <= meta_len <= 160 else 0.6 if 120 <= meta_len <= 180 else 0.3)
        
        scores.append(1.0 if structure['schema_types'] else 0.0)
        scores.append(min(len(keywords) / 10, 1.0))
        
        return np.mean(scores)

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    
    def _generate_recommendations(self, geo: GEOScore, gaps: List, structure: dict) -> List[dict]:
        recs = []
        
        if geo.schema_markup < 0.5:
            recs.append({'priority': 'CRITICAL', 'category': 'GEO-SCHEMA',
                        'message': 'Add JSON-LD for LocalBusiness and FAQPage'})
        
        if geo.quotable_statements < 0.6:
            recs.append({'priority': 'CRITICAL', 'category': 'GEO-QUOTES',
                        'message': f'Add quotable statements (found {geo.details.get("quotables_found", 0)}, need 5+)'})
        
        if geo.statistics_density < 0.5:
            recs.append({'priority': 'HIGH', 'category': 'GEO-STATS',
                        'message': 'Add statistics: percentages, years, customer counts'})
        
        if geo.faq_quality < 0.5:
            recs.append({'priority': 'HIGH', 'category': 'GEO-FAQ',
                        'message': 'Add FAQ section with 8-10 questions'})
        
        if geo.authoritative_language < 0.5:
            recs.append({'priority': 'MEDIUM', 'category': 'GEO-AUTHORITY',
                        'message': 'Add phrases like "Research shows...", "Board-certified..."'})
        
        if len(structure['h1_tags']) != 1:
            recs.append({'priority': 'HIGH', 'category': 'SEO-H1',
                        'message': f'Use exactly 1 H1 tag (found {len(structure["h1_tags"])})'})
        
        if gaps:
            top = ', '.join([g['keyword'] for g in gaps[:3]])
            recs.append({'priority': 'HIGH', 'category': 'SEO-KEYWORDS',
                        'message': f'Target keywords: {top}'})
        
        return recs
    
    def _error_results(self, client_info: dict, error: str) -> dict:
        return {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': 0, 'seoScore': 0, 'geoScore': 0, 'competitiveScore': 0,
            'error': error, 'topKeywords': [], 'keywordGaps': [],
            'geoComponents': [], 'radarData': [],
            'recommendations': [{'priority': 'CRITICAL', 'category': 'ERROR', 'message': error}]
        }

    # =========================================================================
    # PROMPT GENERATION - OPTIMIZED FOR GEO
    # =========================================================================
    
    def generate_prompt(self, project: dict) -> str:
        """Generate highly optimized prompt for GEO-ready website"""
        
        results = project.get('results', {})
        name = project.get('client_name', 'Business')
        location = project.get('location', 'Your Area')
        industry = project.get('industry', 'Services')
        
        keywords = results.get('topKeywords', [])
        gaps = results.get('keywordGaps', [])
        
        kw_list = '\n'.join([f"- {k['keyword']}" for k in keywords[:8]]) if keywords else f"- {industry}"
        gap_list = '\n'.join([f"- {g['keyword']}" for g in gaps[:5]]) if gaps else "- (none found)"
        
        return f'''Generate a complete, SEO and GEO optimized HTML website.

BUSINESS INFO:
- Name: {name}
- Location: {location}  
- Industry: {industry}

TARGET KEYWORDS:
{kw_list}

COMPETITOR KEYWORD GAPS (include these):
{gap_list}

CRITICAL GEO REQUIREMENTS (AI search optimization):

1. QUOTABLE STATEMENTS - Include exactly 5 statements like:
   - "At {name}, we believe exceptional service starts with understanding our customers' needs."
   - "Our mission is to provide {location} with the highest quality {industry.lower()} services."
   - "{name} has proudly served the {location} community for over 10 years."

2. STATISTICS - Include exactly 4 statistics:
   - "Trusted by over 500 families in {location}"
   - "98% customer satisfaction rate"
   - "Serving {location} for over 10 years"
   - "Our team has 50+ years combined experience"

3. AUTHORITATIVE PHRASES - Include at least 3:
   - "Research shows that..."
   - "Industry experts recommend..."
   - "Board-certified specialists..."

4. FAQ SECTION - Include 8 FAQs with definitive answers. Example:
   Q: What services does {name} offer?
   A: {name} provides comprehensive {industry.lower()} services including [list services]. Our certified team in {location} delivers personalized solutions.

5. JSON-LD SCHEMA - Include in <head>:
   - LocalBusiness schema with name, address, phone
   - FAQPage schema wrapping all FAQs

STRUCTURE REQUIREMENTS:
- Exactly ONE H1 tag: "{name} | {industry} in {location}"
- Title tag 50-60 characters
- Meta description 150-160 characters with call-to-action
- Semantic HTML: header, main, section, article, footer
- Hero section with value proposition
- Services section
- About/Trust section with stats
- FAQ section (8 questions minimum)
- Contact section with CTA

OUTPUT:
Return ONLY valid HTML5 starting with <!DOCTYPE html>.
Include all CSS in <style> tag.
Include JSON-LD schemas in <script type="application/ld+json"> tags.
NO explanations, NO markdown, NO comments.'''

    # =========================================================================
    # SINGLE-PASS WEBSITE GENERATION
    # =========================================================================
    
    def generate_website(self, prompt: str, timeout: int = 120) -> dict:
        """
        Generate website with single Ollama call (no iterations).
        Returns dict with html, score, and any errors.
        """
        print("\n🚀 Generating website (single pass)...")
        
        try:
            response = requests.post(
                f'{self.ollama_host}/api/generate',
                json={
                    'model': 'qwen2:7b',
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'num_predict': 8000
                    }
                },
                timeout=timeout
            )
            
            if response.status_code != 200:
                return {'success': False, 'html': '', 'error': f'Ollama returned {response.status_code}'}
            
            html = response.json().get('response', '')
            
            # Clean markdown if present
            if '```html' in html:
                html = html.split('```html')[1].split('```')[0]
            elif '```' in html:
                parts = html.split('```')
                if len(parts) >= 2:
                    html = parts[1]
            
            html = html.strip()
            
            if not html:
                return {'success': False, 'html': '', 'error': 'Empty response from Ollama'}
            
            # Validate
            score = self._validate_html(html)
            
            print(f"   ✓ Generated {len(html)} chars")
            print(f"   ✓ Score: Overall={score['overall']:.2f}, SEO={score['seo']:.2f}, GEO={score['geo']:.2f}")
            
            return {
                'success': True,
                'html': html,
                'score': score,
                'error': None
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'html': '', 'error': f'Timeout after {timeout}s'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'html': '', 'error': 'Cannot connect to Ollama'}
        except Exception as e:
            return {'success': False, 'html': '', 'error': str(e)}
    
    def _validate_html(self, html: str) -> dict:
        """Validate generated HTML for SEO and GEO - FIXED REGEX"""
        if not html:
            return {'overall': 0, 'seo': 0, 'geo': 0, 'feedback': ['No HTML']}
        
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        scores = {}
        feedback = []
        
        # SEO
        h1s = soup.find_all('h1')
        scores['h1'] = 1.0 if len(h1s) == 1 else 0.5
        if len(h1s) != 1:
            feedback.append(f'H1 tags: {len(h1s)} (need 1)')
        
        title = soup.find('title')
        tlen = len(title.text) if title else 0
        scores['title'] = 1.0 if 50 <= tlen <= 65 else 0.5
        
        meta = soup.find('meta', {'name': 'description'})
        mlen = len(meta.get('content', '')) if meta else 0
        scores['meta'] = 1.0 if 150 <= mlen <= 165 else 0.5
        
        # GEO - FIXED PATTERNS
        quotes = len(re.findall(r'"[^"]{20,150}"', text))
        quotes += len(re.findall(r'(?:we believe|our mission|at \w+,)[^.]{15,80}\.', text, re.I))
        scores['quotes'] = min(quotes / 5, 1.0)
        if quotes < 5:
            feedback.append(f'Quotables: {quotes} (need 5)')
        
        stats = len(re.findall(r'\d+\s*%', text))
        stats += len(re.findall(r'(?:over|more than)\s*\d+', text, re.I))
        stats += len(re.findall(r'\d+\s*(?:years?|customers?|clients?)', text, re.I))
        scores['stats'] = min(stats / 4, 1.0)
        if stats < 4:
            feedback.append(f'Statistics: {stats} (need 4)')
        
        schemas = soup.find_all('script', {'type': 'application/ld+json'})
        scores['schema'] = 1.0 if schemas else 0.0
        if not schemas:
            feedback.append('Missing JSON-LD schema')
        
        seo = (scores['h1'] + scores['title'] + scores['meta']) / 3
        geo = (scores['quotes'] + scores['stats'] + scores['schema']) / 3
        overall = seo * 0.4 + geo * 0.6
        
        return {
            'overall': round(overall, 2),
            'seo': round(seo, 2),
            'geo': round(geo, 2),
            'details': scores,
            'feedback': feedback
        }

    # Legacy method for backwards compatibility
    def generate_and_validate_website(self, prompt: str, project: dict) -> dict:
        """Legacy method - now just calls single-pass generation"""
        result = self.generate_website(prompt)
        return {
            'final_html': result.get('html', ''),
            'final_score': result.get('score', {}).get('overall', 0),
            'iterations': 1,
            'history': [result.get('score', {})]
        }
    
    def analyze_geo_only(self, url: str) -> dict:
        """Standalone GEO analysis"""
        content = self._scrape_website(url)
        if not content.success:
            return {'error': content.error}
        
        geo = self._analyze_geo(content)
        return {
            'url': url,
            'score': round(geo.overall_score * 100),
            'components': {
                'quotables': round(geo.quotable_statements * 100),
                'statistics': round(geo.statistics_density * 100),
                'authority': round(geo.authoritative_language * 100),
                'openers': round(geo.definitive_openers * 100),
                'schema': round(geo.schema_markup * 100),
                'entity': round(geo.entity_clarity * 100),
                'faq': round(geo.faq_quality * 100)
            },
            'details': geo.details
        }


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    
    pipeline = AtlanticDigitalPipeline()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        
        if '--geo' in sys.argv:
            print(f"\n🤖 GEO Analysis: {url}")
            result = pipeline.analyze_geo_only(url)
            print(f"\nScore: {result.get('score', 'N/A')}%")
            for k, v in result.get('components', {}).items():
                bar = '█' * (v // 10) + '░' * (10 - v // 10)
                print(f"  {k:12s} [{bar}] {v}%")
        else:
            print(f"\n🔍 Full Analysis: {url}")
            results = pipeline.run_analysis(url, sys.argv[2:] if len(sys.argv) > 2 else [],
                                           {'name': 'Test', 'location': 'Test', 'industry': 'Test'})
            print(f"\nOverall: {results['overallScore']}")
            print(f"SEO: {results['seoScore']}")
            print(f"GEO: {results['geoScore']}")
    else:
        print("Usage: python pipeline_v3.py <url> [--geo] [competitor1 competitor2 ...]")
