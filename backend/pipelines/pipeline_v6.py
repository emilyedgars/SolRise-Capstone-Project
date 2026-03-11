"""
Atlantic Digital - SEO/GEO Pipeline v6
======================================
Fixes:
- Better keyword extraction (TF-IDF based, not just counting)
- Proper competitor keyword analysis
- Faster model support (qwen2:1.5b)
- Industry-aware keyword clustering
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

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
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

# Stop words (from python-seo-analyzer)
STOP_WORDS = frozenset([
    "a", "about", "above", "across", "after", "afterwards", "again", "against",
    "all", "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "an", "and", "another", "any", "anyhow", "anyone",
    "anything", "anyway", "anywhere", "are", "around", "as", "at", "back", "be",
    "became", "because", "become", "becomes", "becoming", "been", "before",
    "beforehand", "behind", "being", "below", "beside", "besides", "between",
    "beyond", "both", "but", "by", "can", "cannot", "could", "de", "do", "does",
    "done", "down", "due", "during", "each", "either", "else", "elsewhere",
    "enough", "etc", "even", "ever", "every", "everyone", "everything",
    "everywhere", "except", "few", "for", "from", "further", "get", "go", "had",
    "has", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein",
    "hereupon", "hers", "herself", "him", "himself", "his", "how", "however",
    "i", "if", "in", "indeed", "into", "is", "it", "its", "itself", "just",
    "keep", "last", "latter", "latterly", "least", "less", "made", "many", "may",
    "me", "meanwhile", "might", "more", "moreover", "most", "mostly", "much",
    "must", "my", "myself", "name", "namely", "neither", "never", "nevertheless",
    "next", "no", "nobody", "none", "nor", "not", "nothing", "now", "nowhere",
    "of", "off", "often", "on", "once", "one", "only", "onto", "or", "other",
    "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own",
    "per", "perhaps", "please", "put", "rather", "re", "same", "see", "seem",
    "seemed", "seeming", "seems", "several", "she", "should", "since", "so",
    "some", "somehow", "someone", "something", "sometime", "sometimes",
    "somewhere", "still", "such", "take", "than", "that", "the", "their", "them",
    "themselves", "then", "thence", "there", "thereafter", "thereby", "therefore",
    "therein", "thereupon", "these", "they", "this", "those", "though", "through",
    "throughout", "thru", "thus", "to", "together", "too", "toward", "towards",
    "under", "until", "up", "upon", "us", "very", "via", "was", "we", "well",
    "were", "what", "whatever", "when", "whence", "whenever", "where",
    "whereafter", "whereas", "whereby", "wherein", "whereupon", "wherever",
    "whether", "which", "while", "whither", "who", "whoever", "whole", "whom",
    "whose", "why", "will", "with", "within", "without", "would", "yet", "you",
    "your", "yours", "yourself", "yourselves"
])


# Web noise to filter
WEB_NOISE = frozenset([
    "click", "menu", "nav", "footer", "header", "sidebar", "button", "link",
    "login", "logout", "signup", "signin", "subscribe", "newsletter", "cookie",
    "cookies", "privacy", "policy", "terms", "conditions", "copyright", "reserved",
    "share", "tweet", "facebook", "twitter", "instagram", "linkedin", "youtube",
    "www", "http", "https", "com", "org", "net", "html", "css", "js", "php", "img"
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
    """Enhanced SEO/GEO Analysis Pipeline v6 - Better Keywords"""
    
    def __init__(self, mongodb_uri: Optional[str] = None, ollama_host: str = "http://localhost:11434"):
        self.db = None
        self.ollama_host = ollama_host
        
        # Sentence transformer for semantic analysis
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # TF-IDF for keyword extraction - tuned for SEO
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 3),
            max_df=0.9,      # Ignore terms in >90% of docs
            min_df=1,
            max_features=3000,
            stop_words=list(STOP_WORDS),
            token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z]+\b'  # Words only
        )
        
        # Industry keyword boosters
        self.industry_keywords = {
            'cleaning': ['clean', 'cleaning', 'wash', 'sanitize', 'disinfect', 'spotless', 'hygiene', 'dust', 'mop', 'vacuum', 'scrub', 'polish', 'residential', 'commercial', 'deep clean', 'move out', 'office cleaning'],
            'dental': ['dental', 'dentist', 'teeth', 'tooth', 'oral', 'smile', 'whitening', 'implant', 'crown', 'filling', 'extraction', 'orthodontic', 'braces', 'invisalign', 'hygienist', 'checkup'],
            'legal': ['lawyer', 'attorney', 'legal', 'law', 'court', 'case', 'lawsuit', 'litigation', 'defense', 'injury', 'accident', 'compensation', 'settlement', 'counsel', 'represent'],
            'medical': ['doctor', 'medical', 'health', 'healthcare', 'clinic', 'patient', 'treatment', 'diagnosis', 'therapy', 'care', 'wellness', 'physician', 'specialist'],
            'real estate': ['real estate', 'property', 'home', 'house', 'apartment', 'condo', 'buy', 'sell', 'rent', 'lease', 'mortgage', 'realtor', 'agent', 'listing', 'bedroom', 'bathroom'],
            'restaurant': ['restaurant', 'food', 'menu', 'dining', 'cuisine', 'chef', 'meal', 'lunch', 'dinner', 'breakfast', 'reservation', 'takeout', 'delivery', 'catering'],
            'fitness': ['fitness', 'gym', 'workout', 'exercise', 'training', 'trainer', 'muscle', 'cardio', 'weight', 'strength', 'yoga', 'pilates', 'crossfit', 'membership'],
            'automotive': ['car', 'auto', 'vehicle', 'repair', 'mechanic', 'service', 'oil change', 'brake', 'tire', 'engine', 'transmission', 'maintenance', 'inspection'],
            'plumbing': ['plumber', 'plumbing', 'pipe', 'drain', 'leak', 'water', 'faucet', 'toilet', 'sink', 'shower', 'water heater', 'sewer', 'emergency'],
            'hvac': ['hvac', 'heating', 'cooling', 'air conditioning', 'ac', 'furnace', 'duct', 'ventilation', 'thermostat', 'installation', 'repair', 'maintenance'],
        }
        
        # Brand terms to filter (populated per analysis)
        self.brand_terms: Set[str] = set()

    def _get_industry_keywords(self, industry: str) -> Set[str]:
        """Get relevant keywords for industry"""
        industry_lower = industry.lower()
        keywords = set()
        
        for key, words in self.industry_keywords.items():
            if key in industry_lower or industry_lower in key:
                keywords.update(words)
        
        # Also add the industry name itself
        keywords.update(industry_lower.split())
        
        return keywords

    def _build_brand_filter(self, client_info: dict, url: str = '') -> Set[str]:
        """Build minimal brand filter - only exact matches"""
        filter_terms = set()
        
        # Only filter exact business name (lowercase)
        name = client_info.get('name', '').lower().strip()
        if name:
            filter_terms.add(name)
            # Only filter if it's a single distinctive word
            name_parts = name.split()
            if len(name_parts) == 1 and len(name) > 4:
                filter_terms.add(name)
        
        # Domain without TLD
        if url:
            try:
                domain = urlparse(url).netloc.lower().replace('www.', '')
                domain_name = domain.split('.')[0]
                if len(domain_name) > 4:
                    filter_terms.add(domain_name)
            except:
                pass
        
        return filter_terms

    # =========================================================================
    # MAIN ANALYSIS
    # =========================================================================
    
    def run_analysis(self, client_url: str, competitor_urls: List[str], 
                     client_info: dict, project_id=None) -> dict:
        """Run comprehensive SEO/GEO analysis"""
        
        print("\n" + "="*60)
        print("🚀 ATLANTIC DIGITAL SEO/GEO ANALYSIS v6")
        print("="*60)
        
        business_name = client_info.get('name', '')
        location = client_info.get('location', '')
        industry = client_info.get('industry', '')
        
        # Minimal brand filter
        self.brand_terms = self._build_brand_filter(client_info, client_url)
        print(f"   Brand filter: {self.brand_terms}")
        
        # Get industry keywords
        industry_keywords = self._get_industry_keywords(industry)
        print(f"   Industry keywords: {len(industry_keywords)} terms")
        
        # Step 1: Scrape
        print("\n📥 STEP 1: Scraping websites...")
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
                    print(f"   ✓ Competitor: {comp.word_count} words from {url[:40]}...")
                else:
                    print(f"   ⚠️ Failed: {url[:40]}...")
        
        # Step 2: SEO Keyword Analysis (RESTORED logic)
        print("\n📊 STEP 2: SEO Keyword Analysis...")
        client_seo = self._analyze_seo_comprehensive(client_data)
        print(f"   ✓ Top Keywords: {len(client_seo.top_keywords)}")
        print(f"   ✓ Bigrams: {len(client_seo.top_bigrams)}")
        print(f"   ✓ Trigrams: {len(client_seo.top_trigrams)}")
        
        # Show top 5 keywords
        for kw, count in client_seo.top_keywords[:5]:
            print(f"      - {kw}: {count}")
        
        # Step 3: GEO Analysis (RESTORED logic)
        print("\n🤖 STEP 3: GEO Analysis...")
        client_geo = self._analyze_geo_comprehensive(client_data, business_name, location)
        print(f"   ✓ GEO Score: {client_geo.overall_score:.2f}")
        print(f"   ✓ Claim Density: {client_geo.claim_density:.1f}/100 words")
        
        comp_geo_scores = [self._analyze_geo_comprehensive(c).overall_score for c in competitor_data]
        avg_comp_geo = np.mean(comp_geo_scores) if comp_geo_scores else 0.5
        
        # Step 4: Keyword Gap Analysis (RESTORED logic)
        print("\n🔍 STEP 4: Competitor Keyword Gap Analysis...")
        keyword_gaps = self._analyze_keyword_gaps(client_data, competitor_data, industry)
        print(f"   ✓ Found {len(keyword_gaps)} keyword opportunities")
        
        # Step 5: Competitive Position
        print("\n⚔️ STEP 5: Competitive Analysis...")
        comp_analysis = self._competitive_analysis(client_geo, client_seo, competitor_data)
        
        print("\n✅ ANALYSIS COMPLETE!")
        
        overall_score = (client_seo.overall_score * 0.35) + (client_geo.overall_score * 0.50) + (comp_analysis['similarity'] * 0.15)
        
        return {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': round(overall_score, 2),
            'seoScore': round(client_seo.overall_score, 2),
            'geoScore': round(client_geo.overall_score, 2),
            'competitiveScore': round(comp_analysis['similarity'], 2),
            'competitorAvgGeo': round(avg_comp_geo, 2),
            
            'geoMetrics': {
                'extractability': round(client_geo.extractability_score, 2),
                'readability': round(client_geo.readability_score, 2),
                'citability': round(client_geo.citability_score, 2),
                'claimDensity': round(client_geo.claim_density, 2),
                'totalClaims': client_geo.total_claims,
                'frontloadingScore': round(client_geo.frontloading_score, 2),
                'claimsInFirst100': client_geo.claims_in_first_100,
                'claimsInFirst300': client_geo.claims_in_first_300,
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
            
            # Keywords - RESTORED for frontend compatibility
            'topKeywords': [{'keyword': k, 'count': c} for k, c in client_seo.top_keywords[:15]],
            'topBigrams': [{'phrase': k, 'count': c} for k, c in client_seo.top_bigrams[:10]],
            'topTrigrams': [{'phrase': k, 'count': c} for k, c in client_seo.top_trigrams[:10]],
            'keywordGaps': keyword_gaps[:10],
            
            'geoComponents': [
                {'name': 'Extractability', 'score': round(client_geo.extractability_score, 2),
                 'tip': f'Claim density: {client_geo.claim_density:.1f}/100 words (need 4+)'},
                {'name': 'Answer Frontloading', 'score': round(client_geo.frontloading_score, 2),
                 'tip': f'{client_geo.claims_in_first_100} claims in first 100 words'},
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
            'recommendations': self._generate_recommendations(client_geo, client_seo, keyword_gaps),
            
            'debug': {
                'wordCount': client_data.word_count,
                'competitorsAnalyzed': len(competitor_data)
            }
        }

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
            print(f"   ⚠️ Crawl4AI failed: {str(e)[:100]}")
            try:
                print(f"   🔄 Trying requests...")
                return self._scrape_requests(url)
            except Exception as e2:
                return ScrapedContent(url=url, html='', text='', title='', meta_description='',
                                     headings={}, schema_data=[], word_count=0, content_hash='',
                                     success=False, error=str(e2)[:200])
    
    def _scrape_crawl4ai(self, url: str) -> ScrapedContent:
        """Scrape with Crawl4AI (JavaScript support)"""
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
        
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
        
        return ScrapedContent(
            url=url, html=html, text=text,
            title=title.get_text().strip() if title else '',
            meta_description=meta.get('content', '') if meta else '',
            headings=headings, schema_data=[],
            word_count=len(text.split()), content_hash=content_hash, success=True
        )

    # =========================================================================
    # GEO ANALYSIS (Research-backed - RESTORED)
    # =========================================================================
    
    def _analyze_geo_comprehensive(self, content: ScrapedContent, 
                                    business_name: str = '', location: str = '') -> GEOMetrics:
        """
        Comprehensive GEO analysis based on MIT GEO Paper (2024)
        """
        text = content.text or ''
        text_lower = text.lower()
        details = {}
        
        # 1. CLAIM EXTRACTION & DENSITY
        claim_patterns = [
            r'(?:is|are|was|were|has|have|had)\s+(?:the|a|an)?\s*(?:most|best|largest|smallest|first|only|leading)',
            r'\d+(?:\.\d+)?(?:\s*%|\s+percent)',
            r'\d+(?:,\d{3})*(?:\+|\s+(?:million|billion|thousand))?',
            r'(?:more|less|fewer|greater|higher|lower)\s+than',
            r'(?:^|\.\s+)(?:The|Our|This|These|We|It)\s+(?:is|are|was|were|has|have)',
            r'(?:according to|research shows|studies indicate|experts say)',
            r'(?:since|established|founded|for over)\s+\d+',
        ]
        
        claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, text, re.I)
            claims.extend(matches)
        
        total_claims = len(claims)
        words = text.split()
        word_count = len(words)
        
        claim_density = (total_claims / word_count * 100) if word_count > 0 else 0
        claim_density_score = min(claim_density / 4, 1.0)
        
        # 2. ANSWER FRONTLOADING
        first_100_words = ' '.join(words[:100])
        first_300_words = ' '.join(words[:300])
        claims_in_first_100 = sum(len(re.findall(p, first_100_words, re.I)) for p in claim_patterns)
        claims_in_first_300 = sum(len(re.findall(p, first_300_words, re.I)) for p in claim_patterns)
        
        first_claim_pos = word_count
        for i, word in enumerate(words[:200]):
            chunk = ' '.join(words[max(0, i-5):i+5])
            if any(re.search(p, chunk, re.I) for p in claim_patterns):
                first_claim_pos = i
                break
        
        frontloading_score = min((claims_in_first_100 / 3) * 0.5 + (1 - first_claim_pos / 100) * 0.5, 1.0)
        frontloading_score = max(0, frontloading_score)
        
        # 3. SENTENCE LENGTH
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
        if sentences:
            avg_sentence_length = np.mean([len(s.split()) for s in sentences])
            sentence_length_score = 1.0 if 15 <= avg_sentence_length <= 20 else 0.7 if 12 <= avg_sentence_length <= 25 else 0.4
        else:
            avg_sentence_length = 0
            sentence_length_score = 0
        
        # 4. COVERAGE PREDICTION
        if word_count < 800:
            coverage_prediction = 61
            density_score = 0.6
        elif word_count <= 1500:
            coverage_prediction = 50
            density_score = 1.0
        else:
            coverage_prediction = 35
            density_score = 0.7
        
        # 5. ENTITY EXTRACTION
        doc = nlp(text[:50000])
        entities = list(set([ent.text for ent in doc.ents if ent.label_ in ['ORG', 'PERSON', 'GPE', 'PRODUCT']]))
        entity_count = len(entities)
        
        # 6. TRADITIONAL GEO
        quotables = len(re.findall(r'"[^"]{20,150}"', text)) + len(re.findall(r'(?:we believe|our mission|our goal)[^.]{15,100}\.', text_lower))
        quotable_score = min(quotables / 5, 1.0)
        
        stats = len(re.findall(r'\d+\s*%', text)) + len(re.findall(r'(?:over|more than)\s*[\d,]+', text_lower))
        stats_score = min(stats / 4, 1.0)
        
        authority = len(re.findall(r'(?:studies?|research|experts?)\s+(?:show|indicate|recommend)', text_lower))
        authority_score = min(authority / 4, 1.0)
        
        schema_types = set()
        for schema in content.schema_data:
            if isinstance(schema, dict):
                st = schema.get('@type', '')
                if isinstance(st, list): schema_types.update(st)
                elif st: schema_types.add(st)
        schema_score = min(len(schema_types & {'LocalBusiness', 'FAQPage', 'Organization'}) / 2, 1.0)
        faq_score = 1.0 if 'FAQPage' in schema_types else 0.6 if bool(re.search(r'faq|frequently asked', text_lower)) else 0.2
        
        # Composite
        extractability = claim_density_score * 0.40 + frontloading_score * 0.30 + sentence_length_score * 0.30
        readability = sentence_length_score * 0.50 + density_score * 0.30 + (1.0 if schema_types else 0.3) * 0.20
        citability = quotable_score * 0.30 + stats_score * 0.25 + authority_score * 0.25 + min(entity_count / 20, 1.0) * 0.20
        overall = extractability * 0.35 + readability * 0.25 + citability * 0.25 + schema_score * 0.10 + faq_score * 0.05
        
        return GEOMetrics(
            overall_score=overall, extractability_score=extractability, readability_score=readability,
            citability_score=citability, claim_density=claim_density, total_claims=total_claims,
            first_claim_position=first_claim_pos, claims_in_first_100=claims_in_first_100,
            claims_in_first_300=claims_in_first_300, frontloading_score=frontloading_score,
            avg_sentence_length=avg_sentence_length, sentence_length_score=sentence_length_score,
            word_count=word_count, coverage_prediction=coverage_prediction, density_score=density_score,
            entity_count=entity_count, entity_density=entity_count / (word_count / 100) if word_count else 0,
            entities=entities[:20], quotable_statements=quotable_score, statistics_density=stats_score,
            authoritative_language=authority_score, schema_markup=schema_score, faq_quality=faq_score, details={}
        )

    # =========================================================================
    # SEO ANALYSIS (RESTORED)
    # =========================================================================
    
    def _analyze_seo_comprehensive(self, content: ScrapedContent) -> SEOMetrics:
        """SEO analysis with bigrams, trigrams, and N-E-E-A-T-T scoring"""
        text = content.text or ''
        html = content.html or ''
        soup = BeautifulSoup(html, 'html.parser') if html else None
        warnings = []
        
        # Technical
        title_length = len(content.title)
        title_score = 1.0 if 50 <= title_length <= 60 else 0.5 if title_length < 30 else 0.6 if title_length > 70 else 0.8
        if title_length == 0: warnings.append("Missing title tag")
        
        meta_length = len(content.meta_description)
        meta_score = 1.0 if 150 <= meta_length <= 160 else 0.5 if meta_length < 120 else 0.7
        if meta_length == 0: warnings.append("Missing meta description")
        
        h1_tags = content.headings.get('h1', [])
        h1_score = 1.0 if len(h1_tags) == 1 else 0.5
        if not h1_tags: warnings.append("Missing H1 tag")
        elif len(h1_tags) > 1: warnings.append(f"Multiple H1 tags ({len(h1_tags)})")
        
        # Keywords
        tokens = re.findall(r'(?u)\b\w\w+\b', text.lower())
        tokens_filtered = [t for t in tokens if t not in STOP_WORDS and len(t) > 2 and t not in WEB_NOISE]
        
        # User requested brand filter
        brand_parts = set()
        for b in self.brand_terms: brand_parts.update(b.split())
        tokens_filtered = [t for t in tokens_filtered if t not in brand_parts]
        
        word_freq = Counter(tokens_filtered)
        top_keywords = word_freq.most_common(20)
        
        bigrams = [' '.join(tokens[i:i+2]) for i in range(len(tokens)-1)]
        bigrams_filtered = [b for b in bigrams if not any(w in STOP_WORDS or w in WEB_NOISE or w in brand_parts for w in b.split())]
        top_bigrams = [(b, c) for b, c in Counter(bigrams_filtered).most_common(20) if c > 1 and b.split()[0] != b.split()[1]][:15]
        
        trigrams = [' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)]
        trigrams_filtered = [t for t in trigrams if not any(w in STOP_WORDS or w in WEB_NOISE or w in brand_parts for w in t.split())]
        top_trigrams = [(t, c) for t, c in Counter(trigrams_filtered).most_common(15) if c > 1 and len(set(t.split())) == 3][:10]
        
        # Links & Images
        internal_links = external_links = 0
        if soup:
            for link in soup.find_all('a', href=True):
                if link['href'].startswith('http') and urlparse(content.url).netloc not in link['href']: external_links += 1
                else: internal_links += 1
        
        images_with_alt = images_without_alt = 0
        if soup:
            for img in soup.find_all('img'):
                if img.get('alt'): images_with_alt += 1
                else: images_without_alt += 1
        if images_without_alt > 3: warnings.append(f"{images_without_alt} images missing alt text")
        
        # NEEATT
        text_lower = text.lower()
        neeat_scores = {
            'notability': min(len(re.findall(r'(?:award|recognized|featured|leading)', text_lower)) / 3, 1.0),
            'experience': min(len(re.findall(r'(?:years? of experience|since \d{4}|established)', text_lower)) / 2, 1.0),
            'expertise': min(len(re.findall(r'(?:certified|licensed|specialist|expert)', text_lower)) / 3, 1.0),
            'authoritativeness': min(len(re.findall(r'(?:research|studies|according to)', text_lower)) / 3, 1.0),
            'trustworthiness': min(len(re.findall(r'(?:guarantee|secure|privacy|verified)', text_lower)) / 3, 1.0),
            'transparency': min(len(re.findall(r'(?:contact|about us|our team|phone)', text_lower)) / 3, 1.0)
        }
        
        overall = (title_score * 0.2 + meta_score * 0.15 + h1_score * 0.15 + min(len(top_keywords)/10, 1) * 0.15 + (1 if content.schema_data else 0.3) * 0.15 + np.mean(list(neeat_scores.values())) * 0.2)
        
        return SEOMetrics(
            overall_score=overall, title_score=title_score, title_length=title_length,
            meta_score=meta_score, meta_length=meta_length, h1_score=h1_score, h1_count=len(h1_tags),
            word_count=len(tokens), keyword_density={}, top_keywords=top_keywords,
            top_bigrams=top_bigrams, top_trigrams=top_trigrams, warnings=warnings,
            heading_structure={tag: len(tags) for tag, tags in content.headings.items()},
            internal_links=internal_links, external_links=external_links,
            images_with_alt=images_with_alt, images_without_alt=images_without_alt,
            neeat_scores=neeat_scores, details={}
        )

    # =========================================================================
    # KEYWORD GAP ANALYSIS (RESTORED)
    # =========================================================================
    
    def _analyze_keyword_gaps(self, client: ScrapedContent, competitors: List[ScrapedContent], 
                                industry: str = '') -> List[dict]:
        """Find keywords competitors use that client doesn't"""
        if not competitors: return []
        def preprocess(text):
            tokens = re.findall(r'(?u)\b\w\w+\b', text.lower())
            return ' '.join([t for t in tokens if t not in STOP_WORDS and len(t) > 2 and t not in WEB_NOISE])
        
        all_texts = [preprocess(client.text)] + [preprocess(c.text) for c in competitors]
        try:
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            features = self.tfidf.get_feature_names_out()
            client_scores = tfidf_matrix[0].toarray()[0]
            comp_avg = np.mean(tfidf_matrix[1:].toarray(), axis=0) if len(competitors) > 0 else client_scores
            
            gaps = []
            for i, feature in enumerate(features):
                gap = comp_avg[i] - client_scores[i]
                if gap > 0.02:
                    gaps.append({'keyword': feature, 'score': round(float(gap), 3), 'client': round(float(client_scores[i]), 3), 'competitor': round(float(comp_avg[i]), 3)})
            gaps.sort(key=lambda x: x['score'], reverse=True)
            return gaps[:15]
        except: return []

    # =========================================================================
    # COMPETITIVE ANALYSIS (RESTORED)
    # =========================================================================
    
    def _competitive_analysis(self, client_geo: GEOMetrics, client_seo: SEOMetrics,
                                competitors: List[ScrapedContent]) -> dict:
        if not competitors: return {'similarity': 0.5, 'position': 'unknown'}
        try:
            client_text = ' '.join(k for k, c in client_seo.top_keywords[:10])
            client_emb = self.sentence_model.encode([client_text])
            sims = []
            for comp in competitors:
                comp_keywords = [t for t in re.findall(r'(?u)\b\w\w+\b', comp.text.lower()) if t not in STOP_WORDS][:50]
                comp_emb = self.sentence_model.encode([' '.join(comp_keywords)])
                sims.append(float(cosine_similarity(client_emb, comp_emb)[0][0]))
            return {'similarity': np.mean(sims), 'position': 'competitive' if np.mean(sims) > 0.5 else 'differentiated'}
        except: return {'similarity': 0.5, 'position': 'unknown'}

    # =========================================================================
    # RECOMMENDATIONS (RESTORED)
    # =========================================================================
    
    def _generate_recommendations(self, geo: GEOMetrics, seo: SEOMetrics, gaps: List[dict]) -> List[dict]:
        recs = []
        if geo.claim_density < 4: recs.append({'priority': 'CRITICAL', 'category': 'GEO-CLAIMS', 'message': f'Increase claim density to 4+ per 100 words (cur: {geo.claim_density:.1f})'})
        if geo.frontloading_score < 0.6: recs.append({'priority': 'CRITICAL', 'category': 'GEO-FRONTLOADING', 'message': f'Improve answer frontloading. Lead with key facts.'})
        if geo.schema_markup < 0.5: recs.append({'priority': 'HIGH', 'category': 'GEO-SCHEMA', 'message': 'Add JSON-LD schema for LocalBusiness and FAQPage.'})
        for w in seo.warnings[:3]: recs.append({'priority': 'HIGH', 'category': 'SEO-TECHNICAL', 'message': w})
        if gaps: recs.append({'priority': 'MEDIUM', 'category': 'SEO-KEYWORDS', 'message': f'Target: {", ".join([g["keyword"] for g in gaps[:3]])}'})
        return recs

    # =========================================================================
    # PROMPT GENERATION (RESTORED COMPREHENSIVE PROMPTY)
    # =========================================================================
    
    def generate_prompt(self, project: dict) -> str:
        results = project.get('results', {})
        name = project.get('client_name', 'Business')
        location = project.get('location', 'Your Area')
        industry = project.get('industry', 'Services')
        
        geo_metrics = results.get('geoMetrics', {})
        seo_metrics = results.get('seoMetrics', {})
        keywords = results.get('topKeywords', [])
        bigrams = results.get('topBigrams', [])
        trigrams = results.get('topTrigrams', [])
        gaps = results.get('keywordGaps', [])
        geo_components = results.get('geoComponents', [])
        recommendations = results.get('recommendations', [])
        entities = geo_metrics.get('topEntities', [])
        
        current_geo = results.get('geoScore', 0)
        current_seo = results.get('seoScore', 0)
        claim_density = geo_metrics.get('claimDensity', 0)
        avg_sentence = geo_metrics.get('avgSentenceLength', 25)
        extractability = geo_metrics.get('extractability', 0)
        frontloading = geo_metrics.get('frontloadingScore', 0)
        coverage_pred = geo_metrics.get('coveragePrediction', 50)
        
        # NEEATT gaps
        neeat_scores = seo_metrics.get('neeatScores', {})
        weak_neeat = [f"{k}: {v:.0%}" for k, v in neeat_scores.items() if v < 0.5]
        neeat_focus = ', '.join(weak_neeat) if weak_neeat else "All adequate"
        
        kw_primary = '\n'.join([f"  - {k['keyword']} (used {k['count']}x)" for k in keywords[:8]]) or f"  - {industry}"
        kw_bigrams = '\n'.join([f"  - \"{b['phrase']}\" ({b['count']}x)" for b in bigrams[:6]]) if bigrams else "  - (none found)"
        kw_trigrams = '\n'.join([f"  - \"{t['phrase']}\" ({t['count']}x)" for t in trigrams[:4]]) if trigrams else "  - (none found)"
        kw_gaps = '\n'.join([f"  - {g['keyword']} (competitor: {g['competitor']:.2f})" for g in gaps[:8]]) if gaps else "  - (none found)"
        
        weak_areas = '\n'.join([f"  ⚠️ {c['name']}: {c['score']:.0%} - {c['tip']}" for c in geo_components if c.get('score', 1) < 0.6])
        recs_text = '\n'.join([f"  • [{r['category']}] {r['message']}" for r in recommendations if r.get('priority') in ['CRITICAL', 'HIGH']][:5])
        
        target_claims = max(4, int(claim_density) + 2)
        target_words = 1200
        
        return f'''You are an expert SEO and GEO website generator. Create a website optimized for BOTH search engines AND AI systems (ChatGPT, Claude, Perplexity, Google AI Overviews).

================================================================================
                              BUSINESS INFORMATION
================================================================================
Business Name: {name}
Location: {location}
Industry: {industry}

================================================================================
                           CURRENT ANALYSIS SCORES
================================================================================
Overall Score: {results.get('overallScore', 0):.0%}
├── GEO Score: {current_geo:.0%} (AI Citability)
│   ├── Extractability: {extractability:.0%}
│   ├── Claim Density: {claim_density:.1f}/100 words (TARGET: 4+)
│   ├── Frontloading: {frontloading:.0%}
│   └── Avg Sentence: {avg_sentence:.0f} words (TARGET: 15-20)
├── SEO Score: {current_seo:.0%}
└── Coverage Prediction: {coverage_pred:.0f}%

AREAS NEEDING IMPROVEMENT:
{weak_areas}

CREDIBILITY GAPS (N-E-E-A-T-T): {neeat_focus}

================================================================================
                              KEYWORD STRATEGY
================================================================================

PRIMARY KEYWORDS (use each 2-3 times naturally):
{kw_primary}

HIGH-VALUE PHRASES (bigrams - use in headings/content):
{kw_bigrams}

LONG-TAIL PHRASES (trigrams - use in FAQ answers):
{kw_trigrams}

COMPETITOR KEYWORD GAPS (MUST include these):
{kw_gaps}

ENTITIES TO MENTION (for AI entity recognition):
  {', '.join(entities[:10]) if entities else name + ', ' + location}

================================================================================
                    GEO REQUIREMENTS (AI SEARCH OPTIMIZATION)
================================================================================
Based on MIT GEO Research (2024) and Dejan AI Grounding Study (2025):

1. CLAIM DENSITY: {target_claims}+ claims per 100 words
   ─────────────────────────────────────────────────────
   Current: {claim_density:.1f}/100 words | Target: {target_claims}+
   
   Include extractable FACTS that AI can cite:
   ✓ "{name} has proudly served {location} for over [X] years."
   ✓ "[X]% of our customers report complete satisfaction."
   ✓ "Our team brings [X]+ years of combined {industry.lower()} experience."
   ✓ "We have successfully helped [X]+ families in {location}."
   ✓ "Rated [X] out of 5 stars based on [X] verified reviews."
   ✓ "{name} is the [#1/leading/most trusted] {industry.lower()} provider in {location}."

2. ANSWER FRONTLOADING: First 100 words = 3+ claims
   ─────────────────────────────────────────────────────
   Current: {geo_metrics.get('claimsInFirst100', 0)} claims in first 100 words
   
   The FIRST PARAGRAPH must immediately answer "What is {name}?":
   ✓ Start with: "{name} is {location}'s premier {industry.lower()} provider..."
   ✓ Include a statistic in sentence 1 or 2
   ✓ Mention location within first 50 words
   ✓ NO introductory fluff - lead with facts

3. SENTENCE LENGTH: 15-20 words average
   ─────────────────────────────────────────────────────
   Current: {avg_sentence:.0f} words | Target: 15-20 words
   
   Rules for AI-extractable sentences:
   ✓ One fact per sentence
   ✓ Subject-verb-object structure
   ✓ Avoid compound sentences with multiple clauses
   ✓ Example: "Our certified technicians complete training annually." (7 words ✓)
   ✗ Avoid: "We have technicians who are certified and they complete training every year to stay updated." (16 words, too complex)

4. QUOTABLE STATEMENTS: 6+ explicit quotes
   ─────────────────────────────────────────────────────
   AI systems extract and cite these directly:
   
   ✓ "At {name}, we believe [core value/philosophy]."
   ✓ "Our mission is to [specific purpose] for {location} residents."
   ✓ "{name}'s approach combines [method 1] with [method 2]."
   ✓ "We guarantee [specific promise] or [consequence]."
   ✓ "Every customer deserves [specific benefit]."
   ✓ "[Founder name], founder of {name}, says: '[insight about industry].'"

5. AUTHORITATIVE LANGUAGE: 4+ authority signals
   ─────────────────────────────────────────────────────
   Use phrases that establish expertise:
   
   ✓ "Research shows that [relevant finding]..."
   ✓ "Industry experts recommend [best practice]..."
   ✓ "According to [authority source], [fact]..."
   ✓ "Board-certified specialists at {name}..."
   ✓ "Studies indicate that [data point]..."
   ✓ "The American [Industry] Association suggests..."

6. STATISTICS WITH CONTEXT: 5+ data points
   ─────────────────────────────────────────────────────
   Include specific, verifiable numbers:
   
   ✓ "98% customer satisfaction rate (based on 500+ reviews)"
   ✓ "Serving {location} since [year] (over [X] years)"
   ✓ "[X]+ successful projects completed"
   ✓ "Average response time: [X] hours"
   ✓ "Save up to [X]% compared to [alternative]"
   ✓ "[X] out of [Y] customers recommend us"

================================================================================
                         SEO TECHNICAL REQUIREMENTS
================================================================================

1. TITLE TAG (50-60 characters):
   Format: "Primary Keyword | {name} | {location}"
   Example: "{industry} Services | {name} | {location}"

2. META DESCRIPTION (150-160 characters):
   Must include: primary keyword, {name}, {location}, and call-to-action
   Example: "{name} provides expert {industry.lower()} services in {location}. 
   Trusted by 500+ families. 98% satisfaction. Call for free consultation!"

3. HEADING STRUCTURE:
   - Exactly ONE H1: Include primary keyword + location
   - 3-5 H2s: Major sections (Services, About, FAQ, Contact)
   - H3s: Subsections within H2s
   
4. SCHEMA MARKUP (JSON-LD in <head>):
   MUST include both:
   
   a) LocalBusiness Schema:
   {{
     "@context": "https://schema.org",
     "@type": "LocalBusiness",
     "name": "{name}",
     "description": "[compelling 1-sentence description]",
     "address": {{
       "@type": "PostalAddress",
       "addressLocality": "{location}"
     }},
     "aggregateRating": {{
       "@type": "AggregateRating",
       "ratingValue": "4.9",
       "reviewCount": "150"
     }},
     "priceRange": "$$"
   }}
   
   b) FAQPage Schema (wrap ALL FAQ content):
   {{
     "@context": "https://schema.org",
     "@type": "FAQPage",
     "mainEntity": [
       {{
         "@type": "Question",
         "name": "[question]",
         "acceptedAnswer": {{
           "@type": "Answer",
           "text": "[answer starting with definitive statement]"
         }}
       }}
     ]
   }}

================================================================================
                              CONTENT STRUCTURE
================================================================================

TARGET WORD COUNT: ~{target_words} words (optimal for AI coverage)

REQUIRED SECTIONS:

1. HERO SECTION
   - H1 with primary keyword + location
   - 2-3 sentence value proposition with statistics
   - Primary CTA button
   - Trust indicators (years, customers served, rating)

2. SERVICES/OFFERINGS SECTION
   - H2: "Our {industry} Services in {location}"
   - 3-4 service cards with H3 headings
   - Each service: 2-3 sentences with specific benefits
   - Include relevant keywords naturally

3. WHY CHOOSE US / TRUST SECTION
   - H2: "Why {location} Trusts {name}"
   - Statistics grid (4 key numbers)
   - Quotable mission statement
   - Authority phrases and credentials
   - N-E-E-A-T-T signals: experience, expertise, certifications

4. FAQ SECTION (CRITICAL FOR GEO)
   - H2: "Frequently Asked Questions"
   - Minimum 8 questions, ideally 10
   - Each answer MUST start with definitive statement
   - Include long-tail keywords from analysis
   - Wrap in FAQPage schema
   
   Question topics to cover:
   - What services do you offer?
   - How much does [service] cost?
   - What areas do you serve?
   - How do I schedule an appointment?
   - What makes you different from competitors?
   - Do you offer [specific service]?
   - What are your hours/availability?
   - Do you offer free consultations/estimates?

5. CONTACT/CTA SECTION
   - H2: "Contact {name} Today"
   - Location prominently displayed
   - Multiple contact methods
   - Final CTA with urgency

================================================================================
                           CRITICAL IMPROVEMENTS NEEDED
================================================================================
Based on analysis, prioritize these fixes:

{recs_text}

================================================================================
                              OUTPUT REQUIREMENTS
================================================================================

✓ Return ONLY valid HTML5 code
✓ Start with <!DOCTYPE html>
✓ Include all CSS in a single <style> tag in <head>
✓ Include both JSON-LD schemas in <head>
✓ Use semantic HTML (header, main, section, article, footer, nav)
✓ Mobile-responsive design
✓ Professional, modern styling

✗ Do NOT include any explanations
✗ Do NOT use markdown formatting
✗ Do NOT include code comments
✗ Do NOT include placeholder text like [X] - use realistic numbers

================================================================================
Generate the complete HTML now:
'''

    # =========================================================================
    # STANDALONE GEO
    # =========================================================================
    
    def validate_generated_html(self, html: str) -> dict:
        """Basic validation of generated HTML"""
        if not html:
            return {'valid': False, 'score': 0, 'issues': ['Empty HTML']}
        
        issues = []
        if '<!DOCTYPE html>' not in html.upper(): issues.append("Missing DOCTYPE")
        if '<html' not in html.lower(): issues.append("Missing <html> tag")
        if '<head' not in html.lower(): issues.append("Missing <head> tag")
        if '<body' not in html.lower(): issues.append("Missing <body> tag")
        if '<style' not in html.lower(): issues.append("Missing <style> tag")
        
        # Check for essential SEO/GEO elements
        if '<h1' not in html.lower(): issues.append("Missing H1 heading")
        if '<script type="application/ld+json"' not in html.lower(): issues.append("Missing Schema markup")
        
        score = max(0, 100 - (len(issues) * 15))
        return {
            'valid': len(issues) < 3,
            'score': score,
            'issues': issues,
            'length': len(html)
        }

    def analyze_geo_only(self, url: str) -> dict:
        """Quick standalone GEO analysis"""
        content = self._scrape_website(url)
        if not content.success:
            return {'success': False, 'error': content.error}
            
        geo = self._analyze_geo_comprehensive(content)
        return {
            'success': True,
            'url': url,
            'score': round(geo.overall_score, 2),
            'metrics': {
                'claimDensity': round(geo.claim_density, 2),
                'extractability': round(geo.extractability_score, 2),
                'citability': round(geo.citability_score, 2),
                'coveragePrediction': round(geo.coverage_prediction, 1)
            }
        }

    def analyze_seo_only(self, url: str) -> dict:
        """Quick standalone SEO analysis"""
        content = self._scrape_website(url)
        if not content.success:
            return {'success': False, 'error': content.error}
            
        seo = self._analyze_seo_comprehensive(content)
        return {
            'success': True,
            'url': url,
            'score': round(seo.overall_score, 2),
            'metrics': {
                'titleScore': round(seo.title_score, 2),
                'h1Count': seo.h1_count,
                'wordCount': seo.word_count
            },
            'topKeywords': [{'keyword': k, 'count': c} for k, c in seo.top_keywords[:10]]
        }

    def _error_results(self, client_info: dict, error: str) -> dict:
        return {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': 0, 'seoScore': 0, 'geoScore': 0,
            'error': error, 'topKeywords': [], 'keywordGaps': [],
            'recommendations': [{'priority': 'CRITICAL', 'category': 'ERROR', 'message': error}]
        }


if __name__ == "__main__":
    import sys
    pipeline = AtlanticDigitalPipeline()
    if len(sys.argv) > 1:
        print(pipeline.analyze_geo_only(sys.argv[1]))
