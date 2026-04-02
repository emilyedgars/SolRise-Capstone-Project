"""
Atlantic Digital - SEO/GEO Pipeline v7
======================================
New Features:
- PDF Report Generation for clients
- Real SEO API integration (DataForSEO, free tier)
- Fixed GEO analyzer
- Dynamic validation loop (not hardcoded)
- HTML improvement suggestions based on actual client HTML
"""

from datetime import datetime
import asyncio
import re
import json
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter
from urllib.parse import urlparse
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
from bs4 import BeautifulSoup, Tag
import requests

# Load spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Minimal stop words
STOP_WORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "it", "its",
    "this", "that", "these", "those", "i", "you", "he", "she", "we", "they",
    "what", "which", "who", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just"
])

WEB_NOISE = frozenset([
    "click", "menu", "nav", "footer", "header", "sidebar", "button", "link",
    "login", "logout", "signup", "subscribe", "newsletter", "cookie", "cookies",
    "privacy", "policy", "terms", "copyright", "share", "tweet", "facebook",
    "twitter", "instagram", "linkedin", "www", "http", "https", "com", "org"
])


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
    content_hash: str
    success: bool
    error: Optional[str] = None


@dataclass
class HTMLIssue:
    """Specific issue found in client's HTML"""
    element: str  # Which HTML element
    issue: str    # What's wrong
    current: str  # Current value
    suggestion: str  # How to fix
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    line_number: Optional[int] = None


@dataclass
class GEOMetrics:
    overall_score: float
    extractability_score: float
    readability_score: float
    citability_score: float
    claim_density: float
    total_claims: int
    first_claim_position: int
    claims_in_first_100: int
    claims_in_first_300: int
    frontloading_score: float
    avg_sentence_length: float
    sentence_length_score: float
    word_count: int
    coverage_prediction: float
    density_score: float
    entity_count: int
    entity_density: float
    entities: List[str]
    quotable_statements: float
    statistics_density: float
    authoritative_language: float
    schema_markup: float
    faq_quality: float
    details: dict = field(default_factory=dict)


@dataclass 
class SEOMetrics:
    overall_score: float
    title_score: float
    title_length: int
    meta_score: float
    meta_length: int
    h1_score: float
    h1_count: int
    word_count: int
    keyword_density: Dict[str, float]
    top_keywords: List[Tuple[str, int]]
    top_bigrams: List[Tuple[str, int]]
    top_trigrams: List[Tuple[str, int]]
    warnings: List[str]
    heading_structure: Dict[str, int]
    internal_links: int
    external_links: int
    images_with_alt: int
    images_without_alt: int
    neeat_scores: Dict[str, float]
    details: dict = field(default_factory=dict)


class AtlanticDigitalPipeline:
    """SEO/GEO Analysis Pipeline v7 - With Reports & Real APIs"""
    
    def __init__(self, mongodb_uri: Optional[str] = None, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 3),
            max_df=0.9,
            min_df=1,
            max_features=3000,
            stop_words=list(STOP_WORDS),
            token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z]+\b'
        )
        
        # API Keys (set via environment variables)
        self.dataforseo_login = os.environ.get('DATAFORSEO_LOGIN', '')
        self.dataforseo_password = os.environ.get('DATAFORSEO_PASSWORD', '')
        
        self.brand_terms: Set[str] = set()
        
        # Industry keywords
        self.industry_keywords = {
            'cleaning': ['cleaning', 'clean', 'wash', 'sanitize', 'maid', 'housekeeping', 'janitorial', 'spotless', 'disinfect', 'deep clean', 'move out', 'office cleaning', 'residential', 'commercial'],
            'dental': ['dental', 'dentist', 'teeth', 'tooth', 'oral', 'smile', 'whitening', 'implant', 'crown', 'filling', 'orthodontic', 'braces', 'invisalign', 'checkup'],
            'legal': ['lawyer', 'attorney', 'legal', 'law', 'court', 'lawsuit', 'litigation', 'defense', 'injury', 'accident', 'compensation', 'settlement'],
            'plumbing': ['plumber', 'plumbing', 'pipe', 'drain', 'leak', 'water', 'faucet', 'toilet', 'sink', 'water heater', 'sewer', 'emergency'],
            'hvac': ['hvac', 'heating', 'cooling', 'air conditioning', 'ac', 'furnace', 'duct', 'ventilation', 'thermostat'],
            'real estate': ['real estate', 'property', 'home', 'house', 'apartment', 'buy', 'sell', 'rent', 'mortgage', 'realtor', 'agent'],
            'restaurant': ['restaurant', 'food', 'menu', 'dining', 'cuisine', 'chef', 'meal', 'reservation', 'takeout', 'delivery'],
        }

    # =========================================================================
    # MAIN ANALYSIS
    # =========================================================================
    
    def run_analysis(self, client_url: str, competitor_urls: List[str], 
                     client_info: dict, project_id=None) -> dict:
        """Run comprehensive SEO/GEO analysis with HTML improvement suggestions"""
        
        print("\n" + "="*60)
        print("🚀 ATLANTIC DIGITAL SEO/GEO ANALYSIS v7")
        print("="*60)
        
        business_name = client_info.get('name', '')
        location = client_info.get('location', '')
        industry = client_info.get('industry', '')
        
        # Build brand filter
        self.brand_terms = self._build_brand_filter(client_info, client_url)
        industry_keywords = self._get_industry_keywords(industry)
        
        # Step 1: Scrape client website
        print("\n📥 STEP 1: Scraping websites...")
        client_data = self._scrape_website(client_url)
        if not client_data.success:
            return self._error_results(client_info, f"Failed to scrape: {client_data.error}")
        print(f"   ✓ Client: {client_data.word_count} words")
        
        # Scrape competitors
        competitor_data = []
        for url in competitor_urls:
            if url and url.strip():
                comp = self._scrape_website(url)
                if comp.success:
                    competitor_data.append(comp)
                    print(f"   ✓ Competitor: {url[:40]}...")
        
        # Step 2: Analyze client's actual HTML and suggest improvements
        print("\n🔍 STEP 2: Analyzing client HTML for improvements...")
        html_issues = self._analyze_html_issues(client_data, business_name, location, industry)
        print(f"   ✓ Found {len(html_issues)} improvement opportunities")
        
        # Step 3: SEO Analysis
        print("\n📊 STEP 3: SEO Keyword Analysis...")
        client_seo = self._analyze_seo(client_data, competitor_data, industry_keywords)
        print(f"   ✓ Keywords: {len(client_seo.top_keywords)}")
        
        # Step 4: GEO Analysis
        print("\n🤖 STEP 4: GEO Analysis...")
        client_geo = self._analyze_geo(client_data, business_name.lower(), location.lower())
        print(f"   ✓ GEO Score: {client_geo.overall_score:.2%}")
        
        # Step 5: Try to get real SERP data (if API available)
        print("\n🌐 STEP 5: SERP Analysis...")
        serp_data = self._get_serp_data(industry, location)
        if serp_data:
            print(f"   ✓ Got SERP data for {len(serp_data.get('keywords', []))} keywords")
        else:
            print(f"   ⚠️ SERP API not configured (set DATAFORSEO_LOGIN)")
        
        # Step 6: Keyword Gap Analysis
        print("\n🔍 STEP 6: Keyword Gap Analysis...")
        keyword_gaps = self._analyze_keyword_gaps(client_data, competitor_data, industry_keywords)
        print(f"   ✓ Found {len(keyword_gaps)} gaps")
        
        # Step 7: Competitive Analysis
        print("\n⚔️ STEP 7: Competitive Analysis...")
        comp_analysis = self._competitive_analysis(client_seo, competitor_data)
        
        comp_geo_scores = [self._analyze_geo(c).overall_score for c in competitor_data]
        avg_comp_geo = np.mean(comp_geo_scores) if comp_geo_scores else 0.5
        
        print("\n✅ ANALYSIS COMPLETE!")
        
        overall_score = (client_seo.overall_score * 0.35) + (client_geo.overall_score * 0.50) + (comp_analysis['similarity'] * 0.15)
        
        # Format HTML issues for output
        html_improvements = [{
            'element': issue.element,
            'issue': issue.issue,
            'current': issue.current[:100] if issue.current else '',
            'suggestion': issue.suggestion,
            'priority': issue.priority
        } for issue in html_issues]
        
        return {
            'clientName': client_info.get('name', 'Client'),
            'clientUrl': client_url,
            'overallScore': round(overall_score, 2),
            'seoScore': round(client_seo.overall_score, 2),
            'geoScore': round(client_geo.overall_score, 2),
            'competitiveScore': round(comp_analysis['similarity'], 2),
            'competitorAvgGeo': round(avg_comp_geo, 2),
            
            # NEW: HTML Improvement Suggestions
            'htmlImprovements': html_improvements,
            'criticalIssues': [h for h in html_improvements if h['priority'] == 'CRITICAL'],
            'highPriorityIssues': [h for h in html_improvements if h['priority'] == 'HIGH'],
            
            'geoMetrics': {
                'extractability': round(client_geo.extractability_score, 2),
                'readability': round(client_geo.readability_score, 2),
                'citability': round(client_geo.citability_score, 2),
                'claimDensity': round(client_geo.claim_density, 2),
                'totalClaims': client_geo.total_claims,
                'frontloadingScore': round(client_geo.frontloading_score, 2),
                'claimsInFirst100': client_geo.claims_in_first_100,
                'avgSentenceLength': round(client_geo.avg_sentence_length, 1),
                'sentenceLengthScore': round(client_geo.sentence_length_score, 2),
                'coveragePrediction': round(client_geo.coverage_prediction, 1),
                'entityCount': client_geo.entity_count,
                'topEntities': client_geo.entities[:10]
            },
            
            'seoMetrics': {
                'titleScore': round(client_seo.title_score, 2),
                'titleLength': client_seo.title_length,
                'metaScore': round(client_seo.meta_score, 2),
                'metaLength': client_seo.meta_length,
                'h1Score': round(client_seo.h1_score, 2),
                'h1Count': client_seo.h1_count,
                'wordCount': client_seo.word_count,
                'headingStructure': client_seo.heading_structure,
                'neeatScores': client_seo.neeat_scores
            },
            
            'topKeywords': [{'keyword': k, 'score': round(s, 3) if isinstance(s, float) else s} for k, s in client_seo.top_keywords[:15]],
            'topBigrams': [{'phrase': k, 'score': round(s, 3) if isinstance(s, float) else s} for k, s in client_seo.top_bigrams[:10]],
            'topTrigrams': [{'phrase': k, 'score': round(s, 3) if isinstance(s, float) else s} for k, s in client_seo.top_trigrams[:10]],
            'keywordGaps': keyword_gaps[:10],
            
            # SERP data if available
            'serpData': serp_data,
            
            'geoComponents': [
                {'name': 'Extractability', 'score': round(client_geo.extractability_score, 2),
                 'tip': f'Claim density: {client_geo.claim_density:.1f}/100 words (need 4+)'},
                {'name': 'Frontloading', 'score': round(client_geo.frontloading_score, 2),
                 'tip': f'{client_geo.claims_in_first_100} claims in first 100 words (need 3+)'},
                {'name': 'Sentence Length', 'score': round(client_geo.sentence_length_score, 2),
                 'tip': f'Avg: {client_geo.avg_sentence_length:.0f} words (target: 15-20)'},
                {'name': 'Quotables', 'score': round(client_geo.quotable_statements, 2),
                 'tip': 'Add explicit citable statements'},
                {'name': 'Statistics', 'score': round(client_geo.statistics_density, 2),
                 'tip': 'Include percentages, numbers, data'},
                {'name': 'Schema', 'score': round(client_geo.schema_markup, 2),
                 'tip': 'Add JSON-LD LocalBusiness + FAQPage'},
                {'name': 'Authority', 'score': round(client_geo.authoritative_language, 2),
                 'tip': 'Use "Research shows...", "Experts recommend..."'},
            ],
            
            'radarData': [
                {'subject': 'Extractability', 'client': int(client_geo.extractability_score * 100), 'competitor': int(avg_comp_geo * 100)},
                {'subject': 'Frontloading', 'client': int(client_geo.frontloading_score * 100), 'competitor': 65},
                {'subject': 'Sentences', 'client': int(client_geo.sentence_length_score * 100), 'competitor': 70},
                {'subject': 'SEO', 'client': int(client_seo.overall_score * 100), 'competitor': 75},
                {'subject': 'Citability', 'client': int(client_geo.citability_score * 100), 'competitor': int(avg_comp_geo * 90)},
                {'subject': 'Credibility', 'client': int(np.mean(list(client_seo.neeat_scores.values())) * 100), 'competitor': 70}
            ],
            
            'warnings': client_seo.warnings,
            'recommendations': self._generate_recommendations(client_geo, client_seo, keyword_gaps, html_issues),
            
            'debug': {
                'wordCount': client_data.word_count,
                'competitorsAnalyzed': len(competitor_data),
                'htmlIssuesFound': len(html_issues)
            }
        }

    # =========================================================================
    # HTML ISSUE ANALYSIS - Analyze actual client HTML
    # =========================================================================
    
    def _analyze_html_issues(self, content: ScrapedContent, business_name: str, 
                              location: str, industry: str) -> List[HTMLIssue]:
        """Analyze client's actual HTML and suggest specific improvements"""
        issues = []
        html = content.html
        soup = BeautifulSoup(html, 'html.parser')
        text = content.text
        
        # =====================================================================
        # TITLE TAG ANALYSIS
        # =====================================================================
        title_tag = soup.find('title')
        if not title_tag:
            issues.append(HTMLIssue(
                element='<title>',
                issue='Missing title tag',
                current='None',
                suggestion=f'Add: <title>{business_name} | {industry} Services in {location}</title>',
                priority='CRITICAL'
            ))
        else:
            title_text = title_tag.get_text().strip()
            title_len = len(title_text)
            
            if title_len < 30:
                issues.append(HTMLIssue(
                    element='<title>',
                    issue=f'Title too short ({title_len} chars)',
                    current=title_text,
                    suggestion=f'{business_name} | Professional {industry} Services in {location}',
                    priority='HIGH'
                ))
            elif title_len > 65:
                issues.append(HTMLIssue(
                    element='<title>',
                    issue=f'Title too long ({title_len} chars, max 60)',
                    current=title_text,
                    suggestion=title_text[:57] + '...',
                    priority='MEDIUM'
                ))
            
            # Check if location/keywords in title
            if location.lower() not in title_text.lower():
                issues.append(HTMLIssue(
                    element='<title>',
                    issue='Missing location in title',
                    current=title_text,
                    suggestion=f'{title_text.split("|")[0].strip()} | {location}',
                    priority='HIGH'
                ))
        
        # =====================================================================
        # META DESCRIPTION ANALYSIS
        # =====================================================================
        meta_desc = soup.find('meta', {'name': 'description'})
        if not meta_desc or not meta_desc.get('content'):
            issues.append(HTMLIssue(
                element='<meta name="description">',
                issue='Missing meta description',
                current='None',
                suggestion=f'<meta name="description" content="{business_name} offers professional {industry.lower()} services in {location}. Trusted by 500+ customers with 98% satisfaction. Call for a free quote today!">',
                priority='CRITICAL'
            ))
        else:
            meta_text = meta_desc.get('content', '')
            meta_len = len(meta_text)
            
            if meta_len < 120:
                issues.append(HTMLIssue(
                    element='<meta name="description">',
                    issue=f'Meta description too short ({meta_len} chars)',
                    current=meta_text,
                    suggestion=f'{meta_text} Contact us today for professional service and free estimates!',
                    priority='HIGH'
                ))
            elif meta_len > 160:
                issues.append(HTMLIssue(
                    element='<meta name="description">',
                    issue=f'Meta description too long ({meta_len} chars)',
                    current=meta_text,
                    suggestion=meta_text[:157] + '...',
                    priority='MEDIUM'
                ))
        
        # =====================================================================
        # H1 TAG ANALYSIS
        # =====================================================================
        h1_tags = soup.find_all('h1')
        if len(h1_tags) == 0:
            issues.append(HTMLIssue(
                element='<h1>',
                issue='Missing H1 tag',
                current='None',
                suggestion=f'<h1>{business_name} - {industry} in {location}</h1>',
                priority='CRITICAL'
            ))
        elif len(h1_tags) > 1:
            issues.append(HTMLIssue(
                element='<h1>',
                issue=f'Multiple H1 tags ({len(h1_tags)})',
                current=', '.join([h.get_text()[:30] for h in h1_tags]),
                suggestion='Keep only one H1 tag per page',
                priority='HIGH'
            ))
        else:
            h1_text = h1_tags[0].get_text().strip()
            if location.lower() not in h1_text.lower() and business_name.lower() not in h1_text.lower():
                issues.append(HTMLIssue(
                    element='<h1>',
                    issue='H1 missing business name or location',
                    current=h1_text,
                    suggestion=f'{business_name} | {industry} in {location}',
                    priority='MEDIUM'
                ))
        
        # =====================================================================
        # SCHEMA MARKUP ANALYSIS
        # =====================================================================
        schemas = soup.find_all('script', {'type': 'application/ld+json'})
        schema_types = set()
        for s in schemas:
            try:
                data = json.loads(s.string) if s.string else {}
                t = data.get('@type', '')
                if isinstance(t, list):
                    schema_types.update(t)
                elif t:
                    schema_types.add(t)
            except:
                pass
        
        if 'LocalBusiness' not in schema_types and 'Organization' not in schema_types:
            issues.append(HTMLIssue(
                element='<script type="application/ld+json">',
                issue='Missing LocalBusiness schema',
                current=f'Found: {list(schema_types)[:3]}' if schema_types else 'None',
                suggestion='''Add: <script type="application/ld+json">{"@context":"https://schema.org","@type":"LocalBusiness","name":"''' + business_name + '''","address":{"@type":"PostalAddress","addressLocality":"''' + location + '''"}}</script>''',
                priority='HIGH'
            ))
        
        if 'FAQPage' not in schema_types:
            issues.append(HTMLIssue(
                element='<script type="application/ld+json">',
                issue='Missing FAQPage schema',
                current='None',
                suggestion='Add FAQPage schema with 5-10 FAQ items for rich snippets',
                priority='HIGH'
            ))
        
        # =====================================================================
        # IMAGE ALT TEXT ANALYSIS
        # =====================================================================
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        
        if images_without_alt:
            sample_img = images_without_alt[0]
            src = sample_img.get('src', sample_img.get('data-src', ''))[:50]
            issues.append(HTMLIssue(
                element='<img>',
                issue=f'{len(images_without_alt)} images missing alt text',
                current=f'Example: <img src="{src}">',
                suggestion=f'Add descriptive alt text: <img src="..." alt="{business_name} {industry.lower()} service">',
                priority='MEDIUM'
            ))
        
        # =====================================================================
        # GEO/AI CITABILITY ISSUES
        # =====================================================================
        
        # Check for quotable statements
        quotables = len(re.findall(r'"[^"]{20,150}"', text))
        quotables += len(re.findall(r'(?:we believe|our mission|at ' + re.escape(business_name.lower()) + r')[^.]{10,80}\.', text.lower()))
        
        if quotables < 3:
            issues.append(HTMLIssue(
                element='Content',
                issue=f'Not enough quotable statements ({quotables} found, need 5+)',
                current=f'{quotables} quotable statements',
                suggestion=f'Add statements like: "At {business_name}, we believe every customer deserves exceptional service." or "Our mission is to provide {location} with the highest quality {industry.lower()}."',
                priority='HIGH'
            ))
        
        # Check for statistics
        stats = len(re.findall(r'\d+\s*%', text))
        stats += len(re.findall(r'(?:over|more than)\s+\d+', text, re.I))
        
        if stats < 4:
            issues.append(HTMLIssue(
                element='Content',
                issue=f'Not enough statistics ({stats} found, need 4+)',
                current=f'{stats} statistics',
                suggestion='Add: "98% customer satisfaction", "Serving 500+ families", "10+ years experience", "50+ 5-star reviews"',
                priority='HIGH'
            ))
        
        # Check for authority language
        authority_phrases = len(re.findall(r'(?:research shows|studies indicate|experts recommend|according to)', text.lower()))
        if authority_phrases < 2:
            issues.append(HTMLIssue(
                element='Content',
                issue='Missing authority language for AI citations',
                current=f'{authority_phrases} authority phrases',
                suggestion='Add phrases like: "Research shows that professional cleaning reduces allergens by 50%", "Industry experts recommend quarterly deep cleaning"',
                priority='MEDIUM'
            ))
        
        # Check sentence length
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
        if sentences:
            avg_len = np.mean([len(s.split()) for s in sentences])
            if avg_len > 25:
                issues.append(HTMLIssue(
                    element='Content',
                    issue=f'Sentences too long (avg {avg_len:.0f} words)',
                    current=f'Average: {avg_len:.0f} words per sentence',
                    suggestion='Break into shorter sentences (15-20 words). AI models extract facts better from concise sentences.',
                    priority='MEDIUM'
                ))
        
        # Check frontloading
        first_100_words = ' '.join(text.split()[:100])
        claims_in_first_100 = len(re.findall(r'\d+\s*%|\d+ years?|since \d{4}|over \d+', first_100_words, re.I))
        if claims_in_first_100 < 2:
            issues.append(HTMLIssue(
                element='Content - First Paragraph',
                issue=f'Not enough claims in first 100 words ({claims_in_first_100})',
                current=first_100_words[:100] + '...',
                suggestion=f'Start with: "{business_name} has served {location} for over 10 years. With 98% customer satisfaction and 500+ completed projects, we are the trusted choice for {industry.lower()}."',
                priority='HIGH'
            ))
        
        return issues

    # =========================================================================
    # SERP API - DataForSEO (Free tier available)
    # =========================================================================
    
    def _get_serp_data(self, industry: str, location: str) -> Optional[dict]:
        """Get real SERP data from DataForSEO API"""
        if not self.dataforseo_login or not self.dataforseo_password:
            return None
        
        try:
            # DataForSEO SERP API
            url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
            
            # Build search query
            query = f"{industry} services {location}"
            
            payload = [{
                "keyword": query,
                "location_name": "United States",
                "language_name": "English",
                "depth": 10
            }]
            
            response = requests.post(
                url,
                auth=(self.dataforseo_login, self.dataforseo_password),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('tasks') and data['tasks'][0].get('result'):
                    result = data['tasks'][0]['result'][0]
                    
                    # Extract useful data
                    items = result.get('items', [])
                    organic_results = [item for item in items if item.get('type') == 'organic']
                    
                    return {
                        'query': query,
                        'total_results': result.get('se_results_count', 0),
                        'top_results': [{
                            'position': r.get('rank_absolute'),
                            'title': r.get('title'),
                            'url': r.get('url'),
                            'description': r.get('description', '')[:150]
                        } for r in organic_results[:5]],
                        'people_also_ask': [item.get('title') for item in items if item.get('type') == 'people_also_ask'][:5],
                        'related_searches': result.get('related_searches', [])[:5]
                    }
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ SERP API error: {e}")
            return None

    # =========================================================================
    # SCRAPING
    # =========================================================================
    
    def _scrape_website(self, url: str) -> ScrapedContent:
        """Scrape website - Crawl4AI first, requests fallback"""
        if not url:
            return ScrapedContent(url='', html='', text='', title='', meta_description='',
                                 headings={}, schema_data=[], word_count=0, content_hash='',
                                 success=False, error='Empty URL')
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Try Crawl4AI first
        try:
            return self._scrape_crawl4ai(url)
        except Exception as e:
            error_msg = str(e)[:200]
            print(f"   ⚠️ Crawl4AI failed: {error_msg}")
            try:
                print(f"   🔄 Trying requests fallback...")
                return self._scrape_requests(url)
            except Exception as e2:
                return ScrapedContent(url=url, html='', text='', title='', meta_description='',
                                     headings={}, schema_data=[], word_count=0, content_hash='',
                                     success=False, error=f"Both methods failed: {error_msg}")
    
    def _scrape_crawl4ai(self, url: str) -> ScrapedContent:
        """Scrape with Crawl4AI"""
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
        content_hash = hashlib.sha1(text.encode('utf-8')).hexdigest()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('title')
        title = title.get_text().strip() if title else ''
        
        meta = soup.find('meta', {'name': 'description'})
        meta_desc = meta.get('content', '') if meta else ''
        
        headings = {}
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            found = soup.find_all(tag)
            if found:
                headings[tag] = [t.get_text().strip() for t in found if t.get_text().strip()]
        
        schema_data = []
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                if script.string:
                    schema_data.append(json.loads(script.string))
            except:
                pass
        
        return ScrapedContent(
            url=url, html=html, text=text, title=title, meta_description=meta_desc,
            headings=headings, schema_data=schema_data, word_count=len(text.split()),
            content_hash=content_hash, success=True
        )
    
    def _scrape_requests(self, url: str) -> ScrapedContent:
        """Simple scraping fallback"""
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0'}
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        for el in soup.find_all(['script', 'style', 'noscript']):
            el.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        content_hash = hashlib.sha1(text.encode('utf-8')).hexdigest()
        
        title = soup.find('title')
        meta = soup.find('meta', {'name': 'description'})
        
        headings = {}
        for tag in ['h1', 'h2', 'h3']:
            found = soup.find_all(tag)
            if found:
                headings[tag] = [t.get_text().strip() for t in found]
        
        schema_data = []
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                if script.string:
                    schema_data.append(json.loads(script.string))
            except:
                pass
        
        return ScrapedContent(
            url=url, html=html, text=text,
            title=title.get_text().strip() if title else '',
            meta_description=meta.get('content', '') if meta else '',
            headings=headings, schema_data=schema_data,
            word_count=len(text.split()), content_hash=content_hash, success=True
        )

    # =========================================================================
    # SEO ANALYSIS
    # =========================================================================
    
    def _analyze_seo(self, client: ScrapedContent, competitors: List[ScrapedContent],
                      industry_keywords: Set[str]) -> SEOMetrics:
        """SEO analysis with TF-IDF"""
        text = client.text or ''
        html = client.html or ''
        soup = BeautifulSoup(html, 'html.parser') if html else None
        
        warnings = []
        
        # Title
        title_length = len(client.title)
        if title_length == 0:
            title_score = 0
            warnings.append("Missing title tag")
        elif 50 <= title_length <= 60:
            title_score = 1.0
        elif title_length < 30:
            title_score = 0.4
            warnings.append(f"Title too short ({title_length} chars)")
        elif title_length > 65:
            title_score = 0.6
            warnings.append(f"Title too long ({title_length} chars)")
        else:
            title_score = 0.8
        
        # Meta
        meta_length = len(client.meta_description)
        if meta_length == 0:
            meta_score = 0
            warnings.append("Missing meta description")
        elif 150 <= meta_length <= 160:
            meta_score = 1.0
        elif meta_length < 120:
            meta_score = 0.5
            warnings.append(f"Meta description too short ({meta_length} chars)")
        else:
            meta_score = 0.7
        
        # H1
        h1_tags = client.headings.get('h1', [])
        h1_count = len(h1_tags)
        if h1_count == 0:
            h1_score = 0
            warnings.append("Missing H1 tag")
        elif h1_count == 1:
            h1_score = 1.0
        else:
            h1_score = 0.5
            warnings.append(f"Multiple H1 tags ({h1_count})")
        
        heading_structure = {tag: len(tags) for tag, tags in client.headings.items()}
        
        # Keyword extraction with TF-IDF
        all_texts = [text] + [c.text for c in competitors if c.text]
        
        if len(text) > 100:
            try:
                tfidf_matrix = self.tfidf.fit_transform(all_texts)
                features = self.tfidf.get_feature_names_out()
                client_tfidf = tfidf_matrix[0].toarray()[0]
                
                keyword_scores = []
                for i, feature in enumerate(features):
                    score = client_tfidf[i]
                    if score > 0.01 and feature.lower() not in WEB_NOISE and feature.lower() not in self.brand_terms:
                        if feature.lower() in industry_keywords:
                            score *= 1.5
                        keyword_scores.append((feature, score))
                
                keyword_scores.sort(key=lambda x: x[1], reverse=True)
                
                unigrams = [(k, s) for k, s in keyword_scores if ' ' not in k][:20]
                bigrams = [(k, s) for k, s in keyword_scores if k.count(' ') == 1][:15]
                trigrams = [(k, s) for k, s in keyword_scores if k.count(' ') == 2][:10]
                
            except Exception as e:
                unigrams, bigrams, trigrams = self._simple_keywords(text, industry_keywords)
        else:
            unigrams, bigrams, trigrams = self._simple_keywords(text, industry_keywords)
        
        # Links
        internal_links = external_links = 0
        if soup:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and urlparse(client.url).netloc not in href:
                    external_links += 1
                elif href.startswith('/'):
                    internal_links += 1
        
        # Images
        images_with_alt = images_without_alt = 0
        if soup:
            for img in soup.find_all('img'):
                if img.get('alt'):
                    images_with_alt += 1
                else:
                    images_without_alt += 1
        
        if images_without_alt > 3:
            warnings.append(f"{images_without_alt} images missing alt text")
        
        # N-E-E-A-T-T
        text_lower = text.lower()
        neeat_scores = {
            'notability': min(len(re.findall(r'(?:award|recognized|featured|leading|top)', text_lower)) / 3, 1.0),
            'experience': min(len(re.findall(r'(?:years? of experience|since \d{4}|established|founded)', text_lower)) / 2, 1.0),
            'expertise': min(len(re.findall(r'(?:certified|licensed|specialist|expert|professional)', text_lower)) / 3, 1.0),
            'authoritativeness': min(len(re.findall(r'(?:research|studies|according to|proven)', text_lower)) / 3, 1.0),
            'trustworthiness': min(len(re.findall(r'(?:guarantee|secure|privacy|verified|trusted)', text_lower)) / 3, 1.0),
            'transparency': min(len(re.findall(r'(?:contact|about us|our team|phone|email)', text_lower)) / 3, 1.0)
        }
        
        word_count = len(text.split())
        keyword_density = {}
        for kw, score in unigrams[:10]:
            count = text_lower.count(kw.lower())
            if word_count > 0:
                keyword_density[kw] = round(count / word_count * 100, 2)
        
        overall = (
            title_score * 0.20 +
            meta_score * 0.15 +
            h1_score * 0.15 +
            min(len(unigrams) / 10, 1.0) * 0.20 +
            (1.0 if client.schema_data else 0.3) * 0.10 +
            np.mean(list(neeat_scores.values())) * 0.20
        )
        
        return SEOMetrics(
            overall_score=overall,
            title_score=title_score, title_length=title_length,
            meta_score=meta_score, meta_length=meta_length,
            h1_score=h1_score, h1_count=h1_count,
            word_count=word_count, keyword_density=keyword_density,
            top_keywords=unigrams, top_bigrams=bigrams, top_trigrams=trigrams,
            warnings=warnings, heading_structure=heading_structure,
            internal_links=internal_links, external_links=external_links,
            images_with_alt=images_with_alt, images_without_alt=images_without_alt,
            neeat_scores=neeat_scores, details={}
        )
    
    def _simple_keywords(self, text: str, industry_kw: Set[str]) -> Tuple[List, List, List]:
        """Fallback keyword extraction"""
        words = re.findall(r'(?u)\b[a-zA-Z]{3,}\b', text.lower())
        filtered = [w for w in words if w not in STOP_WORDS and w not in WEB_NOISE]
        
        freq = Counter(filtered)
        for kw in industry_kw:
            if kw in freq:
                freq[kw] = int(freq[kw] * 1.5)
        
        unigrams = freq.most_common(20)
        
        bigrams = Counter([f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered)-1)])
        trigrams = Counter([f"{filtered[i]} {filtered[i+1]} {filtered[i+2]}" for i in range(len(filtered)-2)])
        
        return unigrams, bigrams.most_common(15), trigrams.most_common(10)

    # =========================================================================
    # GEO ANALYSIS - FIXED
    # =========================================================================
    
    def _analyze_geo(self, content: ScrapedContent, business_name: str = '', location: str = '') -> GEOMetrics:
        """GEO analysis for AI citability - FIXED VERSION"""
        text = content.text or ''
        
        if not text:
            return self._empty_geo_metrics()
        
        text_lower = text.lower()
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return self._empty_geo_metrics()
        
        # Claim patterns
        claim_patterns = [
            r'\d+(?:\.\d+)?(?:\s*%|\s+percent)',
            r'\d+(?:,\d{3})*(?:\+|\s+(?:million|billion|thousand))?',
            r'(?:more|less|over|under)\s+than\s+\d+',
            r'(?:since|established|founded)\s+\d{4}',
            r'(?:is|are|was|were)\s+(?:the|a)?\s*(?:best|top|leading|largest|first)',
        ]
        
        total_claims = sum(len(re.findall(p, text, re.I)) for p in claim_patterns)
        claim_density = (total_claims / word_count * 100) if word_count > 0 else 0
        claim_density_score = min(claim_density / 4, 1.0)
        
        # Frontloading
        first_100 = ' '.join(words[:100]) if len(words) >= 100 else ' '.join(words)
        first_300 = ' '.join(words[:300]) if len(words) >= 300 else ' '.join(words)
        
        claims_in_100 = sum(len(re.findall(p, first_100, re.I)) for p in claim_patterns)
        claims_in_300 = sum(len(re.findall(p, first_300, re.I)) for p in claim_patterns)
        
        frontloading_score = min(claims_in_100 / 3, 1.0) if claims_in_100 > 0 else 0
        
        # First claim position
        first_claim_pos = word_count
        for i in range(min(100, len(words))):
            chunk = ' '.join(words[max(0,i-3):i+3])
            if any(re.search(p, chunk, re.I) for p in claim_patterns):
                first_claim_pos = i
                break
        
        # Sentence length
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
        if sentences:
            avg_sentence = np.mean([len(s.split()) for s in sentences])
            if 15 <= avg_sentence <= 20:
                sentence_score = 1.0
            elif 12 <= avg_sentence <= 25:
                sentence_score = 0.6
            else:
                sentence_score = 0.3
        else:
            avg_sentence = 0
            sentence_score = 0
        
        # Coverage prediction
        if word_count < 800:
            coverage = 61
            density_score = 0.6
        elif word_count <= 1500:
            coverage = 50
            density_score = 1.0
        elif word_count <= 2500:
            coverage = 35
            density_score = 0.7
        else:
            coverage = 13
            density_score = 0.4
        
        # Entities
        try:
            doc = nlp(text[:30000])
            entities = list(set([ent.text for ent in doc.ents if ent.label_ in ['ORG', 'PERSON', 'GPE', 'PRODUCT']]))
        except:
            entities = []
        
        entity_count = len(entities)
        entity_density = entity_count / (word_count / 100) if word_count > 0 else 0
        
        # Quotables
        quotables = len(re.findall(r'"[^"]{20,150}"', text))
        quotables += len(re.findall(r'(?:we believe|our mission|our goal)[^.]{10,80}\.', text_lower))
        quotable_score = min(quotables / 5, 1.0)
        
        # Stats
        stats = len(re.findall(r'\d+\s*%', text))
        stats += len(re.findall(r'(?:over|more than)\s+\d+', text_lower))
        stats_score = min(stats / 4, 1.0)
        
        # Authority
        authority = len(re.findall(r'(?:research|studies|experts?)\s+(?:show|indicate|recommend)', text_lower))
        authority_score = min(authority / 3, 1.0)
        
        # Schema
        schema_types = set()
        for s in content.schema_data:
            if isinstance(s, dict):
                t = s.get('@type', '')
                if isinstance(t, str):
                    schema_types.add(t)
                elif isinstance(t, list):
                    schema_types.update(t)
        
        schema_score = min(len(schema_types & {'LocalBusiness', 'FAQPage', 'Organization', 'Service'}) / 2, 1.0)
        
        # FAQ
        has_faq = bool(re.search(r'faq|frequently asked', text_lower))
        faq_score = 1.0 if 'FAQPage' in schema_types else (0.5 if has_faq else 0.2)
        
        # Composite scores
        extractability = claim_density_score * 0.4 + frontloading_score * 0.3 + sentence_score * 0.3
        readability = sentence_score * 0.5 + density_score * 0.3 + (0.2 if schema_types else 0)
        citability = quotable_score * 0.3 + stats_score * 0.3 + authority_score * 0.2 + min(entity_count/15, 1) * 0.2
        
        overall = extractability * 0.35 + readability * 0.25 + citability * 0.25 + schema_score * 0.1 + faq_score * 0.05
        
        return GEOMetrics(
            overall_score=overall,
            extractability_score=extractability,
            readability_score=readability,
            citability_score=citability,
            claim_density=claim_density,
            total_claims=total_claims,
            first_claim_position=first_claim_pos,
            claims_in_first_100=claims_in_100,
            claims_in_first_300=claims_in_300,
            frontloading_score=frontloading_score,
            avg_sentence_length=avg_sentence,
            sentence_length_score=sentence_score,
            word_count=word_count,
            coverage_prediction=coverage,
            density_score=density_score,
            entity_count=entity_count,
            entity_density=entity_density,
            entities=entities[:20],
            quotable_statements=quotable_score,
            statistics_density=stats_score,
            authoritative_language=authority_score,
            schema_markup=schema_score,
            faq_quality=faq_score,
            details={}
        )
    
    def _empty_geo_metrics(self) -> GEOMetrics:
        """Return empty GEO metrics for error cases"""
        return GEOMetrics(
            overall_score=0, extractability_score=0, readability_score=0, citability_score=0,
            claim_density=0, total_claims=0, first_claim_position=0, claims_in_first_100=0,
            claims_in_first_300=0, frontloading_score=0, avg_sentence_length=0, sentence_length_score=0,
            word_count=0, coverage_prediction=0, density_score=0, entity_count=0, entity_density=0,
            entities=[], quotable_statements=0, statistics_density=0, authoritative_language=0,
            schema_markup=0, faq_quality=0, details={}
        )

    # =========================================================================
    # KEYWORD GAP ANALYSIS
    # =========================================================================
    
    def _analyze_keyword_gaps(self, client: ScrapedContent, competitors: List[ScrapedContent],
                               industry_kw: Set[str]) -> List[dict]:
        """Find competitor keywords client is missing"""
        if not competitors:
            return []
        
        all_texts = [client.text] + [c.text for c in competitors]
        
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_df=0.95, min_df=1, max_features=1500, stop_words=list(STOP_WORDS))
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            features = vectorizer.get_feature_names_out()
            
            client_scores = tfidf_matrix[0].toarray()[0]
            comp_scores = tfidf_matrix[1:].toarray()
            comp_avg = np.mean(comp_scores, axis=0) if len(comp_scores) > 0 else np.zeros_like(client_scores)
            
            gaps = []
            for i, feature in enumerate(features):
                if feature.lower() in WEB_NOISE or feature.lower() in self.brand_terms:
                    continue
                
                gap = comp_avg[i] - client_scores[i]
                if gap > 0.01 and comp_avg[i] > 0.02:
                    priority = 'high' if feature.lower() in industry_kw else 'medium'
                    gaps.append({
                        'keyword': feature,
                        'gap': round(float(gap), 4),
                        'client': round(float(client_scores[i]), 4),
                        'competitor': round(float(comp_avg[i]), 4),
                        'priority': priority
                    })
            
            gaps.sort(key=lambda x: x['gap'], reverse=True)
            return gaps[:20]
            
        except Exception as e:
            print(f"   ⚠️ Gap analysis error: {e}")
            return []

    # =========================================================================
    # COMPETITIVE ANALYSIS
    # =========================================================================
    
    def _competitive_analysis(self, client_seo: SEOMetrics, competitors: List[ScrapedContent]) -> dict:
        if not competitors:
            return {'similarity': 0.5, 'position': 'unknown'}
        
        try:
            client_kws = ' '.join([k for k, s in client_seo.top_keywords[:15]])
            client_emb = self.sentence_model.encode([client_kws])
            
            sims = []
            for comp in competitors:
                comp_words = re.findall(r'\b[a-zA-Z]{4,}\b', comp.text.lower())[:100]
                comp_emb = self.sentence_model.encode([' '.join(comp_words)])
                sims.append(float(cosine_similarity(client_emb, comp_emb)[0][0]))
            
            return {'similarity': np.mean(sims), 'position': 'competitive' if np.mean(sims) > 0.5 else 'differentiated'}
        except:
            return {'similarity': 0.5, 'position': 'unknown'}

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    
    def _generate_recommendations(self, geo: GEOMetrics, seo: SEOMetrics, 
                                   gaps: List[dict], html_issues: List[HTMLIssue]) -> List[dict]:
        recs = []
        
        # Critical HTML issues first
        critical_html = [h for h in html_issues if h.priority == 'CRITICAL']
        for issue in critical_html[:3]:
            recs.append({'priority': 'CRITICAL', 'category': 'HTML', 'message': f'{issue.element}: {issue.issue}'})
        
        # GEO issues
        if geo.claim_density < 4:
            recs.append({'priority': 'CRITICAL', 'category': 'GEO', 'message': f'Increase claim density: {geo.claim_density:.1f} → 4+ per 100 words'})
        
        if geo.frontloading_score < 0.6:
            recs.append({'priority': 'HIGH', 'category': 'GEO', 'message': f'Add claims to first 100 words (currently {geo.claims_in_first_100})'})
        
        if geo.schema_markup < 0.5:
            recs.append({'priority': 'HIGH', 'category': 'SCHEMA', 'message': 'Add LocalBusiness + FAQPage JSON-LD schema'})
        
        # SEO warnings
        for w in seo.warnings[:2]:
            recs.append({'priority': 'HIGH', 'category': 'SEO', 'message': w})
        
        # Keyword gaps
        if gaps:
            top_gaps = ', '.join([g['keyword'] for g in gaps[:3]])
            recs.append({'priority': 'MEDIUM', 'category': 'KEYWORDS', 'message': f'Target competitor keywords: {top_gaps}'})
        
        return recs

    # =========================================================================
    # PDF REPORT GENERATION
    # =========================================================================
    
    def generate_report(self, project: dict) -> str:
        """Generate HTML report that can be converted to PDF"""
        results = project.get('results', {})
        name = project.get('client_name', 'Client')
        url = project.get('client_url', '')
        location = project.get('location', '')
        industry = project.get('industry', '')
        
        html_issues = results.get('htmlImprovements', [])
        geo_metrics = results.get('geoMetrics', {})
        seo_metrics = results.get('seoMetrics', {})
        keywords = results.get('topKeywords', [])
        gaps = results.get('keywordGaps', [])
        recommendations = results.get('recommendations', [])
        
        # Generate HTML report
        report_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SEO/GEO Analysis Report - {name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        
        .score-cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .score-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; }}
        .score-card .score {{ font-size: 36px; font-weight: bold; }}
        .score-card .label {{ color: #666; font-size: 14px; }}
        .score-good {{ color: #28a745; }}
        .score-medium {{ color: #ffc107; }}
        .score-bad {{ color: #dc3545; }}
        
        h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin: 30px 0 20px; }}
        
        .issue {{ background: #fff; border-left: 4px solid #dc3545; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .issue.high {{ border-color: #ffc107; }}
        .issue.medium {{ border-color: #17a2b8; }}
        .issue h4 {{ color: #333; margin-bottom: 5px; }}
        .issue .current {{ color: #666; font-size: 13px; margin: 5px 0; }}
        .issue .suggestion {{ background: #e8f5e9; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 14px; }}
        
        .keywords {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }}
        .keyword {{ background: #e3f2fd; padding: 5px 15px; border-radius: 20px; font-size: 14px; }}
        
        .metric-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
        .metric-label {{ color: #666; }}
        .metric-value {{ font-weight: bold; }}
        
        .recommendation {{ background: #fff3e0; padding: 15px; margin-bottom: 10px; border-radius: 5px; }}
        .recommendation.critical {{ background: #ffebee; }}
        .recommendation .priority {{ font-weight: bold; text-transform: uppercase; font-size: 12px; }}
        
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SEO/GEO Analysis Report</h1>
        <p><strong>{name}</strong> | {url}</p>
        <p>Generated: {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    
    <div class="score-cards">
        <div class="score-card">
            <div class="score {'score-good' if results.get('overallScore', 0) >= 0.7 else 'score-medium' if results.get('overallScore', 0) >= 0.5 else 'score-bad'}">{int(results.get('overallScore', 0) * 100)}%</div>
            <div class="label">Overall Score</div>
        </div>
        <div class="score-card">
            <div class="score {'score-good' if results.get('seoScore', 0) >= 0.7 else 'score-medium' if results.get('seoScore', 0) >= 0.5 else 'score-bad'}">{int(results.get('seoScore', 0) * 100)}%</div>
            <div class="label">SEO Score</div>
        </div>
        <div class="score-card">
            <div class="score {'score-good' if results.get('geoScore', 0) >= 0.7 else 'score-medium' if results.get('geoScore', 0) >= 0.5 else 'score-bad'}">{int(results.get('geoScore', 0) * 100)}%</div>
            <div class="label">GEO Score</div>
        </div>
    </div>
    
    <h2>🚨 Critical Issues to Fix</h2>
    {''.join([f"""
    <div class="issue {'high' if i.get('priority') == 'HIGH' else 'medium' if i.get('priority') == 'MEDIUM' else ''}">
        <h4>{i.get('element', 'Element')}: {i.get('issue', '')}</h4>
        <div class="current">Current: {i.get('current', 'N/A')[:80]}</div>
        <div class="suggestion">💡 <strong>Suggestion:</strong> {i.get('suggestion', '')}</div>
    </div>
    """ for i in html_issues[:8]]) or '<p>No critical issues found!</p>'}
    
    <h2>📊 Key Metrics</h2>
    <div class="metric-row"><span class="metric-label">Word Count</span><span class="metric-value">{seo_metrics.get('wordCount', 0)}</span></div>
    <div class="metric-row"><span class="metric-label">Claim Density</span><span class="metric-value">{geo_metrics.get('claimDensity', 0):.1f} per 100 words</span></div>
    <div class="metric-row"><span class="metric-label">Avg Sentence Length</span><span class="metric-value">{geo_metrics.get('avgSentenceLength', 0):.0f} words</span></div>
    <div class="metric-row"><span class="metric-label">AI Coverage Prediction</span><span class="metric-value">{geo_metrics.get('coveragePrediction', 0)}%</span></div>
    <div class="metric-row"><span class="metric-label">Title Length</span><span class="metric-value">{seo_metrics.get('titleLength', 0)} chars</span></div>
    <div class="metric-row"><span class="metric-label">Meta Description</span><span class="metric-value">{seo_metrics.get('metaLength', 0)} chars</span></div>
    
    <h2>🔑 Top Keywords Found</h2>
    <div class="keywords">
        {''.join([f'<span class="keyword">{k.get("keyword", k)}</span>' for k in keywords[:12]])}
    </div>
    
    <h2>🎯 Competitor Keyword Gaps</h2>
    <p>Keywords your competitors use that you should target:</p>
    <div class="keywords">
        {''.join([f'<span class="keyword">{g.get("keyword", "")}</span>' for g in gaps[:10]]) or '<p>No significant gaps found.</p>'}
    </div>
    
    <h2>📋 Action Items</h2>
    {''.join([f"""
    <div class="recommendation {'critical' if r.get('priority') == 'CRITICAL' else ''}">
        <span class="priority">{r.get('priority', '')}</span> - {r.get('category', '')}: {r.get('message', '')}
    </div>
    """ for r in recommendations[:10]])}
    
    <div class="footer">
        <p>Report generated by Atlantic Digital SEO/GEO Analysis System</p>
        <p>© {datetime.now().year} Atlantic Digital</p>
    </div>
</body>
</html>'''
        
        return report_html

    # =========================================================================
    # VALIDATION LOOP - DYNAMIC (Not Hardcoded)
    # =========================================================================
    
    def validate_and_improve(self, html: str, target_scores: dict = None) -> dict:
        """
        Dynamic validation loop that checks HTML against criteria
        and suggests specific improvements
        """
        if target_scores is None:
            target_scores = {
                'geo_score': 0.7,
                'seo_score': 0.7,
                'claim_density': 4.0,
                'quotables': 5,
                'stats': 4
            }
        
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        issues = []
        passed = []
        
        # Check each criterion dynamically
        checks = [
            ('h1_count', lambda: len(soup.find_all('h1')), 1, 1, 'H1 tag count'),
            ('title_length', lambda: len((soup.find('title') or type('', (), {'text': ''})()).text), 50, 65, 'Title length'),
            ('meta_length', lambda: len((soup.find('meta', {'name': 'description'}) or {}).get('content', '')), 150, 165, 'Meta description length'),
            ('has_schema', lambda: len(soup.find_all('script', {'type': 'application/ld+json'})), 1, 10, 'Schema markup count'),
            ('word_count', lambda: len(text.split()), 800, 2000, 'Word count'),
        ]
        
        for name, check_fn, min_val, max_val, label in checks:
            try:
                value = check_fn()
                if min_val <= value <= max_val:
                    passed.append({'check': label, 'value': value, 'target': f'{min_val}-{max_val}'})
                else:
                    issues.append({
                        'check': label,
                        'value': value,
                        'target': f'{min_val}-{max_val}',
                        'fix': f'Adjust {label.lower()} from {value} to be between {min_val}-{max_val}'
                    })
            except Exception as e:
                issues.append({'check': label, 'error': str(e)})
        
        # GEO-specific checks
        quotables = len(re.findall(r'"[^"]{15,}"|(?:we believe|our mission)[^.]+\.', text, re.I))
        if quotables < target_scores.get('quotables', 5):
            issues.append({
                'check': 'Quotable statements',
                'value': quotables,
                'target': target_scores.get('quotables', 5),
                'fix': f'Add {target_scores.get("quotables", 5) - quotables} more quotable statements'
            })
        else:
            passed.append({'check': 'Quotable statements', 'value': quotables})
        
        stats = len(re.findall(r'\d+\s*%|\d+ years?|over \d+', text, re.I))
        if stats < target_scores.get('stats', 4):
            issues.append({
                'check': 'Statistics',
                'value': stats,
                'target': target_scores.get('stats', 4),
                'fix': f'Add {target_scores.get("stats", 4) - stats} more statistics'
            })
        else:
            passed.append({'check': 'Statistics', 'value': stats})
        
        # Calculate overall pass rate
        total_checks = len(passed) + len(issues)
        pass_rate = len(passed) / total_checks if total_checks > 0 else 0
        
        return {
            'valid': pass_rate >= 0.7,
            'pass_rate': round(pass_rate, 2),
            'passed': passed,
            'issues': issues,
            'improvement_suggestions': [i['fix'] for i in issues if 'fix' in i]
        }

    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _build_brand_filter(self, client_info: dict, url: str = '') -> Set[str]:
        filter_terms = set()
        name = client_info.get('name', '').lower().strip()
        if name:
            filter_terms.add(name)
            if len(name.split()) == 1 and len(name) > 4:
                filter_terms.add(name)
        if url:
            try:
                domain = urlparse(url).netloc.lower().replace('www.', '')
                domain_name = domain.split('.')[0]
                if len(domain_name) > 4:
                    filter_terms.add(domain_name)
            except:
                pass
        return filter_terms
    
    def _get_industry_keywords(self, industry: str) -> Set[str]:
        keywords = set()
        industry_lower = industry.lower()
        for key, words in self.industry_keywords.items():
            if key in industry_lower or industry_lower in key:
                keywords.update(words)
        keywords.update(industry_lower.split())
        return keywords

    # =========================================================================
    # PROMPT GENERATION
    # =========================================================================
    
    def generate_prompt(self, project: dict) -> str:
        results = project.get('results', {})
        name = project.get('client_name', 'Business')
        location = project.get('location', 'Your Area')
        industry = project.get('industry', 'Services')
        
        keywords = results.get('topKeywords', [])
        gaps = results.get('keywordGaps', [])
        html_issues = results.get('htmlImprovements', [])
        
        kw_list = ', '.join([k.get('keyword', str(k)) for k in keywords[:8]]) if keywords else industry
        gap_list = ', '.join([g.get('keyword', '') for g in gaps[:5]]) if gaps else ''
        
        # Include specific issues to fix
        issues_text = '\n'.join([f"- Fix: {i.get('issue', '')} → {i.get('suggestion', '')[:100]}" for i in html_issues[:5]])
        
        return f'''Create a GEO-optimized HTML website for {name} in {location} ({industry}).

KEYWORDS: {kw_list}
COMPETITOR GAPS: {gap_list}

ISSUES TO FIX:
{issues_text}

REQUIREMENTS:
1. ONE H1 with "{name}" and "{location}"
2. Title: 50-60 chars | Meta: 150-160 chars
3. 5+ quotable statements ("At {name}, we believe...")
4. 4+ statistics (percentages, years, numbers)
5. JSON-LD: LocalBusiness + FAQPage schemas
6. 8 FAQ questions
7. Sentences: 15-20 words each
8. Include CSS styling

OUTPUT: Complete HTML only. No markdown.'''

    # =========================================================================
    # STANDALONE GEO ANALYSIS
    # =========================================================================
    
    def analyze_geo_only(self, url: str) -> dict:
        """Standalone GEO analysis - FIXED"""
        try:
            content = self._scrape_website(url)
            if not content.success:
                return {'error': content.error, 'url': url}
            
            geo = self._analyze_geo(content)
            
            return {
                'url': url,
                'success': True,
                'score': round(geo.overall_score * 100),
                'extractability': round(geo.extractability_score * 100),
                'readability': round(geo.readability_score * 100),
                'citability': round(geo.citability_score * 100),
                'metrics': {
                    'claimDensity': round(geo.claim_density, 2),
                    'totalClaims': geo.total_claims,
                    'avgSentenceLength': round(geo.avg_sentence_length, 1),
                    'wordCount': geo.word_count,
                    'coveragePrediction': geo.coverage_prediction,
                    'quotableScore': round(geo.quotable_statements * 100),
                    'statisticsScore': round(geo.statistics_density * 100),
                    'schemaScore': round(geo.schema_markup * 100)
                },
                'entities': geo.entities[:15]
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e), 'url': url, 'success': False}

    def _error_results(self, client_info: dict, error: str) -> dict:
        return {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': 0, 'seoScore': 0, 'geoScore': 0,
            'error': error,
            'htmlImprovements': [],
            'topKeywords': [], 'keywordGaps': [],
            'recommendations': [{'priority': 'CRITICAL', 'category': 'ERROR', 'message': error}]
        }


if __name__ == "__main__":
    import sys
    pipeline = AtlanticDigitalPipeline()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"\n🔍 Analyzing: {url}\n")
        result = pipeline.analyze_geo_only(url)
        
        if result.get('success'):
            print(f"GEO Score: {result['score']}%")
            print(f"Extractability: {result['extractability']}%")
            print(f"Readability: {result['readability']}%")
            print(f"Citability: {result['citability']}%")
            print(f"\nMetrics:")
            for k, v in result['metrics'].items():
                print(f"  {k}: {v}")
        else:
            print(f"Error: {result.get('error')}")
    else:
        print("Usage: python pipeline_v7.py <url>")
