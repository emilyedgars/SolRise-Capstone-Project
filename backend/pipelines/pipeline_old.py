"""
Atlantic Digital - SEO/GEO Pipeline v4
======================================
Enhanced with techniques from:
- houtini-ai/geo-analyzer (GEO metrics)
- python-seo-analyzer (SEO analysis)

New Features:
- Claim density (4+ per 100 words target)
- Answer frontloading (first 100/300 words analysis)
- Sentence length optimization (15-20 word target)
- Information density scoring
- Bigrams & trigrams extraction
- N-E-E-A-T-T credibility scoring
- Extractability score
"""

from datetime import datetime
import asyncio
import re
import json
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter
from string import punctuation

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
from bs4 import BeautifulSoup
import requests

# Load spaCy with entity recognition
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
    """GEO-specific metrics based on research"""
    # Core scores (0-1)
    overall_score: float
    extractability_score: float
    readability_score: float
    citability_score: float
    
    # Claim analysis
    claim_density: float  # Claims per 100 words (target: 4+)
    total_claims: int
    
    # Answer frontloading
    first_claim_position: int  # Word position of first claim
    claims_in_first_100: int
    claims_in_first_300: int
    frontloading_score: float
    
    # Sentence analysis
    avg_sentence_length: float  # Target: 15-20 words
    sentence_length_score: float
    
    # Information density
    word_count: int
    coverage_prediction: float  # Predicted AI coverage %
    density_score: float
    
    # Entity analysis
    entity_count: int
    entity_density: float
    entities: List[str]
    
    # Traditional GEO
    quotable_statements: float
    statistics_density: float
    authoritative_language: float
    schema_markup: float
    faq_quality: float
    
    details: dict = field(default_factory=dict)


@dataclass
class SEOMetrics:
    """SEO metrics based on python-seo-analyzer"""
    overall_score: float
    
    # Technical SEO
    title_score: float
    title_length: int
    meta_score: float
    meta_length: int
    h1_score: float
    h1_count: int
    
    # Content quality
    word_count: int
    keyword_density: Dict[str, float]
    
    # Keywords (unigrams, bigrams, trigrams)
    top_keywords: List[Tuple[str, int]]
    top_bigrams: List[Tuple[str, int]]
    top_trigrams: List[Tuple[str, int]]
    
    # Issues/Warnings
    warnings: List[str]
    
    # Structure
    heading_structure: Dict[str, int]
    internal_links: int
    external_links: int
    images_with_alt: int
    images_without_alt: int
    
    # Credibility (N-E-E-A-T-T)
    neeat_scores: Dict[str, float]
    
    details: dict = field(default_factory=dict)


class AtlanticDigitalPipeline:
    """
    Enhanced SEO/GEO Analysis Pipeline v4
    
    Incorporates research-backed metrics:
    - MIT GEO Paper (2024): Claim density, sentence length
    - Dejan AI Research (2025): Information density, coverage prediction
    """
    
    def __init__(self, mongodb_uri: Optional[str] = None, ollama_host: str = "http://localhost:11434"):
        self.db = None
        if mongodb_uri:
            try:
                from pymongo import MongoClient
                self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
                self.client.server_info()
                self.db = self.client.atlantic_digital
                print("✅ MongoDB connected")
            except Exception as e:
                print(f"⚠️ MongoDB unavailable: {e}")
        
        self.ollama_host = ollama_host
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 3),
            max_df=0.85,
            min_df=1,
            max_features=5000,
            stop_words='english'
        )

    # =========================================================================
    # MAIN ANALYSIS
    # =========================================================================
    
    def run_analysis(self, client_url: str, competitor_urls: List[str], 
                     client_info: dict, project_id=None) -> dict:
        """Run comprehensive SEO/GEO analysis"""
        
        print("\n" + "="*60)
        print("🚀 ATLANTIC DIGITAL SEO/GEO ANALYSIS v4")
        print("="*60)
        
        business_name = client_info.get('name', '').lower()
        location = client_info.get('location', '').lower()
        industry = client_info.get('industry', '').lower()
        
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
                    print(f"   ✓ Competitor: {comp.word_count} words")
        
        # Step 2: GEO Analysis (Research-backed metrics)
        print("\n🤖 STEP 2: GEO Analysis (AI Citability)...")
        client_geo = self._analyze_geo_comprehensive(client_data, business_name, location)
        print(f"   ✓ Overall GEO: {client_geo.overall_score:.2f}")
        print(f"   ✓ Extractability: {client_geo.extractability_score:.2f}")
        print(f"   ✓ Claim Density: {client_geo.claim_density:.1f}/100 words (target: 4+)")
        print(f"   ✓ Frontloading: {client_geo.frontloading_score:.2f}")
        
        comp_geo_scores = [self._analyze_geo_comprehensive(c).overall_score for c in competitor_data]
        avg_comp_geo = np.mean(comp_geo_scores) if comp_geo_scores else 0.5
        
        # Step 3: SEO Analysis
        print("\n📊 STEP 3: SEO Analysis...")
        client_seo = self._analyze_seo_comprehensive(client_data)
        print(f"   ✓ SEO Score: {client_seo.overall_score:.2f}")
        print(f"   ✓ Keywords: {len(client_seo.top_keywords)}")
        print(f"   ✓ Bigrams: {len(client_seo.top_bigrams)}")
        print(f"   ✓ Warnings: {len(client_seo.warnings)}")
        
        # Step 4: Keyword Gap Analysis
        print("\n🔍 STEP 4: Keyword Gap Analysis...")
        keyword_gaps = self._analyze_keyword_gaps(client_data, competitor_data, industry)
        print(f"   ✓ Found {len(keyword_gaps)} keyword gaps")
        
        # Step 5: Competitive Analysis
        print("\n⚔️ STEP 5: Competitive Analysis...")
        comp_analysis = self._competitive_analysis(client_geo, client_seo, competitor_data)
        
        # Compile results
        print("\n✅ ANALYSIS COMPLETE!")
        
        overall_score = (client_seo.overall_score * 0.35) + (client_geo.overall_score * 0.50) + (comp_analysis['similarity'] * 0.15)
        
        results = {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': round(overall_score, 2),
            'seoScore': round(client_seo.overall_score, 2),
            'geoScore': round(client_geo.overall_score, 2),
            'competitiveScore': round(comp_analysis['similarity'], 2),
            'competitorAvgGeo': round(avg_comp_geo, 2),
            
            # GEO Breakdown (Research-backed)
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
            
            # SEO Breakdown
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
            
            # Keywords
            'topKeywords': [{'keyword': k, 'count': c} for k, c in client_seo.top_keywords[:15]],
            'topBigrams': [{'phrase': k, 'count': c} for k, c in client_seo.top_bigrams[:10]],
            'topTrigrams': [{'phrase': k, 'count': c} for k, c in client_seo.top_trigrams[:10]],
            'keywordGaps': keyword_gaps[:10],
            
            # GEO Components (for UI compatibility)
            'geoComponents': [
                {'name': 'Extractability', 'score': round(client_geo.extractability_score, 2),
                 'tip': f'Claim density: {client_geo.claim_density:.1f}/100 words (need 4+)'},
                {'name': 'Answer Frontloading', 'score': round(client_geo.frontloading_score, 2),
                 'tip': f'{client_geo.claims_in_first_100} claims in first 100 words'},
                {'name': 'Sentence Length', 'score': round(client_geo.sentence_length_score, 2),
                 'tip': f'Avg: {client_geo.avg_sentence_length:.0f} words (target: 15-20)'},
                {'name': 'Quotable Statements', 'score': round(client_geo.quotable_statements, 2),
                 'tip': 'Add explicit citable statements'},
                {'name': 'Statistics', 'score': round(client_geo.statistics_density, 2),
                 'tip': 'Include percentages, numbers, data'},
                {'name': 'Schema Markup', 'score': round(client_geo.schema_markup, 2),
                 'tip': 'Add JSON-LD LocalBusiness + FAQPage'},
                {'name': 'Authority', 'score': round(client_geo.authoritative_language, 2),
                 'tip': 'Use "Research shows...", "Experts recommend..."'},
            ],
            
            # Radar chart
            'radarData': [
                {'subject': 'Extractability', 'client': int(client_geo.extractability_score * 100), 'competitor': int(avg_comp_geo * 100)},
                {'subject': 'Frontloading', 'client': int(client_geo.frontloading_score * 100), 'competitor': 65},
                {'subject': 'Sentence Opt', 'client': int(client_geo.sentence_length_score * 100), 'competitor': 70},
                {'subject': 'SEO Technical', 'client': int(client_seo.overall_score * 100), 'competitor': 75},
                {'subject': 'Citability', 'client': int(client_geo.citability_score * 100), 'competitor': int(avg_comp_geo * 90)},
                {'subject': 'Credibility', 'client': int(np.mean(list(client_seo.neeat_scores.values())) * 100), 'competitor': 70}
            ],
            
            # Warnings & Recommendations
            'warnings': client_seo.warnings,
            'recommendations': self._generate_recommendations(client_geo, client_seo, keyword_gaps),
            
            # Debug
            'debug': {
                'wordCount': client_data.word_count,
                'contentHash': client_data.content_hash,
                'competitorsAnalyzed': len(competitor_data)
            }
        }
        
        return results

    # =========================================================================
    # SCRAPING (with content hash)
    # =========================================================================
    
    def _scrape_website(self, url: str) -> ScrapedContent:
        if not url:
            return ScrapedContent(url='', html='', text='', title='', meta_description='',
                                 headings={}, schema_data=[], word_count=0, content_hash='',
                                 success=False, error='Empty URL')
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        try:
            return self._scrape_crawl4ai(url)
        except Exception as e:
            print(f"   ⚠️ Crawl4AI failed: {e}")
            try:
                return self._scrape_requests(url)
            except Exception as e2:
                return ScrapedContent(url=url, html='', text='', title='', meta_description='',
                                     headings={}, schema_data=[], word_count=0, content_hash='',
                                     success=False, error=str(e2))
    
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
        
        # Content hash for duplicate detection
        content_hash = hashlib.sha1(text.encode('utf-8')).hexdigest()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('title')
        title = title.get_text().strip() if title else ''
        
        meta = soup.find('meta', {'name': 'description'})
        meta_desc = meta.get('content', '') if meta else ''
        
        headings = {}
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            tags = soup.find_all(tag)
            if tags:
                headings[tag] = [t.get_text().strip() for t in tags]
        
        schema_data = []
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                schema_data.append(json.loads(script.string))
            except:
                pass
        
        return ScrapedContent(
            url=url, html=html, text=text, title=title, meta_description=meta_desc,
            headings=headings, schema_data=schema_data, word_count=len(text.split()),
            content_hash=content_hash, success=True
        )
    
    def _scrape_requests(self, url: str) -> ScrapedContent:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        for el in soup.find_all(['script', 'style', 'nav', 'footer']):
            el.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        content_hash = hashlib.sha1(text.encode('utf-8')).hexdigest()
        
        title = soup.find('title')
        meta = soup.find('meta', {'name': 'description'})
        
        headings = {}
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            tags = soup.find_all(tag)
            if tags:
                headings[tag] = [t.get_text().strip() for t in tags]
        
        return ScrapedContent(
            url=url, html=html, text=text,
            title=title.get_text().strip() if title else '',
            meta_description=meta.get('content', '') if meta else '',
            headings=headings, schema_data=[],
            word_count=len(text.split()), content_hash=content_hash, success=True
        )

    # =========================================================================
    # GEO ANALYSIS (Research-backed)
    # =========================================================================
    
    def _analyze_geo_comprehensive(self, content: ScrapedContent, 
                                    business_name: str = '', location: str = '') -> GEOMetrics:
        """
        Comprehensive GEO analysis based on:
        - MIT GEO Paper (2024)
        - Dejan AI Grounding Research (2025)
        """
        text = content.text or ''
        text_lower = text.lower()
        details = {}
        
        # =================================================================
        # 1. CLAIM EXTRACTION & DENSITY
        # =================================================================
        # Target: 4+ claims per 100 words (MIT GEO Paper)
        
        claim_patterns = [
            # Factual statements
            r'(?:is|are|was|were|has|have|had)\s+(?:the|a|an)?\s*(?:most|best|largest|smallest|first|only|leading)',
            # Statistics
            r'\d+(?:\.\d+)?(?:\s*%|\s+percent)',
            r'\d+(?:,\d{3})*(?:\+|\s+(?:million|billion|thousand))?',
            # Comparisons
            r'(?:more|less|fewer|greater|higher|lower)\s+than',
            # Definitive statements
            r'(?:^|\.\s+)(?:The|Our|This|These|We|It)\s+(?:is|are|was|were|has|have)',
            # Expert citations
            r'(?:according to|research shows|studies indicate|experts say)',
            # Time-based facts
            r'(?:since|established|founded|for over)\s+\d+',
        ]
        
        claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            claims.extend(matches)
        
        total_claims = len(claims)
        words = text.split()
        word_count = len(words)
        
        claim_density = (total_claims / word_count * 100) if word_count > 0 else 0
        claim_density_score = min(claim_density / 4, 1.0)  # Target: 4 per 100 words
        
        details['total_claims'] = total_claims
        details['claim_density'] = claim_density
        
        # =================================================================
        # 2. ANSWER FRONTLOADING
        # =================================================================
        # Key info should appear in first 100-300 words
        
        first_100_words = ' '.join(words[:100])
        first_300_words = ' '.join(words[:300])
        
        claims_in_first_100 = sum(len(re.findall(p, first_100_words, re.I)) for p in claim_patterns)
        claims_in_first_300 = sum(len(re.findall(p, first_300_words, re.I)) for p in claim_patterns)
        
        # Find position of first claim
        first_claim_pos = word_count  # Default to end if no claim
        for i, word in enumerate(words):
            chunk = ' '.join(words[max(0, i-5):i+5])
            if any(re.search(p, chunk, re.I) for p in claim_patterns):
                first_claim_pos = i
                break
        
        # Frontloading score: claims in first 100 words + early first claim
        frontloading_score = min(
            (claims_in_first_100 / 3) * 0.5 +  # At least 3 claims in first 100
            (1 - first_claim_pos / 100) * 0.5,  # First claim before word 100
            1.0
        )
        frontloading_score = max(0, frontloading_score)
        
        details['claims_first_100'] = claims_in_first_100
        details['claims_first_300'] = claims_in_first_300
        details['first_claim_pos'] = first_claim_pos
        
        # =================================================================
        # 3. SENTENCE LENGTH ANALYSIS
        # =================================================================
        # Target: 15-20 words per sentence (matches Google's extraction)
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if sentences:
            sentence_lengths = [len(s.split()) for s in sentences]
            avg_sentence_length = np.mean(sentence_lengths)
            
            # Score: optimal at 15-20 words
            if 15 <= avg_sentence_length <= 20:
                sentence_length_score = 1.0
            elif 12 <= avg_sentence_length <= 25:
                sentence_length_score = 0.7
            elif 10 <= avg_sentence_length <= 30:
                sentence_length_score = 0.5
            else:
                sentence_length_score = 0.3
        else:
            avg_sentence_length = 0
            sentence_length_score = 0
        
        details['avg_sentence_length'] = avg_sentence_length
        details['sentence_count'] = len(sentences)
        
        # =================================================================
        # 4. INFORMATION DENSITY / COVERAGE PREDICTION
        # =================================================================
        # Based on Dejan research:
        # - Pages <1K words: ~61% AI coverage
        # - Pages 1-2K words: ~40% coverage (optimal)
        # - Pages 3K+ words: ~13% coverage
        
        if word_count < 800:
            coverage_prediction = 61
            density_score = 0.6
        elif 800 <= word_count <= 1500:
            coverage_prediction = 50
            density_score = 1.0  # Optimal range
        elif 1500 < word_count <= 2500:
            coverage_prediction = 35
            density_score = 0.7
        else:
            coverage_prediction = 13
            density_score = 0.4
        
        details['word_count'] = word_count
        details['coverage_prediction'] = coverage_prediction
        
        # =================================================================
        # 5. ENTITY EXTRACTION
        # =================================================================
        doc = nlp(text[:50000])  # Limit for performance
        
        entities = []
        entity_types = Counter()
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON', 'GPE', 'PRODUCT', 'FAC', 'LOC']:
                entities.append(ent.text)
                entity_types[ent.label_] += 1
        
        entity_count = len(entities)
        entity_density = entity_count / (word_count / 100) if word_count > 0 else 0
        
        details['entity_types'] = dict(entity_types)
        details['entity_density'] = entity_density
        
        # =================================================================
        # 6. TRADITIONAL GEO METRICS
        # =================================================================
        
        # Quotable statements
        quotable_patterns = [
            r'"[^"]{20,150}"',
            r'"[^"]{20,150}"',
            r'(?:we believe|our mission|our goal)[^.]{15,100}\.',
        ]
        quotables = sum(len(re.findall(p, text_lower)) for p in quotable_patterns)
        quotable_score = min(quotables / 5, 1.0)
        
        # Statistics
        stat_patterns = [
            r'\d+\s*%',
            r'(?:over|more than)\s*[\d,]+',
            r'\d+\s*(?:years?|customers?|clients?)',
        ]
        stats = sum(len(re.findall(p, text_lower)) for p in stat_patterns)
        stats_score = min(stats / 4, 1.0)
        
        # Authority phrases
        authority_patterns = [
            r'(?:studies?|research)\s+(?:show|indicate|suggest)',
            r'(?:experts?|specialists?)\s+(?:recommend|advise)',
            r'(?:board[- ]?certified|licensed|accredited)',
        ]
        authority = sum(len(re.findall(p, text_lower)) for p in authority_patterns)
        authority_score = min(authority / 4, 1.0)
        
        # Schema
        schema_types = set()
        for schema in content.schema_data:
            if isinstance(schema, dict):
                st = schema.get('@type', '')
                if isinstance(st, list):
                    schema_types.update(st)
                elif st:
                    schema_types.add(st)
        
        important_schemas = {'LocalBusiness', 'Organization', 'FAQPage', 'Service', 'Product'}
        schema_score = min(len(schema_types & important_schemas) / 2, 1.0)
        
        # FAQ quality
        has_faq = bool(re.search(r'(?:faq|frequently\s+asked)', text_lower))
        faq_schema = 'FAQPage' in schema_types
        faq_score = 1.0 if faq_schema else 0.6 if has_faq else 0.2
        
        # =================================================================
        # CALCULATE COMPOSITE SCORES
        # =================================================================
        
        # Extractability: How easily AI can extract facts
        extractability = (
            claim_density_score * 0.40 +
            frontloading_score * 0.30 +
            sentence_length_score * 0.30
        )
        
        # Readability: Structure quality for AI parsing
        readability = (
            sentence_length_score * 0.50 +
            density_score * 0.30 +
            (1.0 if schema_types else 0.3) * 0.20
        )
        
        # Citability: How quotable and attributable
        citability = (
            quotable_score * 0.30 +
            stats_score * 0.25 +
            authority_score * 0.25 +
            (entity_count / 20 if entity_count < 20 else 1.0) * 0.20
        )
        
        # Overall GEO score
        overall = (
            extractability * 0.35 +
            readability * 0.25 +
            citability * 0.25 +
            schema_score * 0.10 +
            faq_score * 0.05
        )
        
        return GEOMetrics(
            overall_score=overall,
            extractability_score=extractability,
            readability_score=readability,
            citability_score=citability,
            claim_density=claim_density,
            total_claims=total_claims,
            first_claim_position=first_claim_pos,
            claims_in_first_100=claims_in_first_100,
            claims_in_first_300=claims_in_first_300,
            frontloading_score=frontloading_score,
            avg_sentence_length=avg_sentence_length,
            sentence_length_score=sentence_length_score,
            word_count=word_count,
            coverage_prediction=coverage_prediction,
            density_score=density_score,
            entity_count=entity_count,
            entity_density=entity_density,
            entities=list(set(entities))[:20],
            quotable_statements=quotable_score,
            statistics_density=stats_score,
            authoritative_language=authority_score,
            schema_markup=schema_score,
            faq_quality=faq_score,
            details=details
        )

    # =========================================================================
    # SEO ANALYSIS (python-seo-analyzer style)
    # =========================================================================
    
    def _analyze_seo_comprehensive(self, content: ScrapedContent) -> SEOMetrics:
        """SEO analysis with bigrams, trigrams, and N-E-E-A-T-T scoring"""
        
        text = content.text or ''
        html = content.html or ''
        soup = BeautifulSoup(html, 'html.parser') if html else None
        
        warnings = []
        
        # =================================================================
        # TITLE ANALYSIS
        # =================================================================
        title_length = len(content.title)
        if title_length == 0:
            title_score = 0
            warnings.append("Missing title tag")
        elif title_length < 30:
            title_score = 0.5
            warnings.append(f"Title too short ({title_length} chars, need 50-60)")
        elif 50 <= title_length <= 60:
            title_score = 1.0
        elif title_length > 70:
            title_score = 0.6
            warnings.append(f"Title too long ({title_length} chars, max 70)")
        else:
            title_score = 0.8
        
        # =================================================================
        # META DESCRIPTION ANALYSIS
        # =================================================================
        meta_length = len(content.meta_description)
        if meta_length == 0:
            meta_score = 0
            warnings.append("Missing meta description")
        elif meta_length < 120:
            meta_score = 0.5
            warnings.append(f"Meta description too short ({meta_length} chars)")
        elif 150 <= meta_length <= 160:
            meta_score = 1.0
        elif meta_length > 170:
            meta_score = 0.6
            warnings.append(f"Meta description too long ({meta_length} chars)")
        else:
            meta_score = 0.8
        
        # =================================================================
        # H1 ANALYSIS
        # =================================================================
        h1_tags = content.headings.get('h1', [])
        h1_count = len(h1_tags)
        if h1_count == 0:
            h1_score = 0
            warnings.append("Missing H1 tag")
        elif h1_count == 1:
            h1_score = 1.0
        else:
            h1_score = 0.5
            warnings.append(f"Multiple H1 tags ({h1_count}), should have exactly 1")
        
        # =================================================================
        # HEADING STRUCTURE
        # =================================================================
        heading_structure = {tag: len(tags) for tag, tags in content.headings.items()}
        
        # =================================================================
        # KEYWORD EXTRACTION (unigrams, bigrams, trigrams)
        # =================================================================
        # Tokenize
        tokens = re.findall(r'(?u)\b\w\w+\b', text.lower())
        tokens_filtered = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
        
        # Unigrams
        word_freq = Counter(tokens_filtered)
        top_keywords = word_freq.most_common(20)
        
        # Bigrams
        bigrams = [' '.join(tokens[i:i+2]) for i in range(len(tokens)-1)]
        bigrams_filtered = [b for b in bigrams if not any(w in STOP_WORDS for w in b.split()[:1])]
        bigram_freq = Counter(bigrams_filtered)
        top_bigrams = [(b, c) for b, c in bigram_freq.most_common(30) if c > 2][:15]
        
        # Trigrams
        trigrams = [' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)]
        trigrams_filtered = [t for t in trigrams if not any(w in STOP_WORDS for w in t.split()[:1])]
        trigram_freq = Counter(trigrams_filtered)
        top_trigrams = [(t, c) for t, c in trigram_freq.most_common(30) if c > 2][:10]
        
        # Keyword density
        word_count = len(tokens)
        keyword_density = {k: round(c / word_count * 100, 2) for k, c in top_keywords[:10]}
        
        # =================================================================
        # LINK ANALYSIS
        # =================================================================
        internal_links = 0
        external_links = 0
        
        if soup:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and content.url not in href:
                    external_links += 1
                elif href.startswith('/') or href.startswith('#'):
                    internal_links += 1
        
        # =================================================================
        # IMAGE ANALYSIS
        # =================================================================
        images_with_alt = 0
        images_without_alt = 0
        
        if soup:
            for img in soup.find_all('img'):
                if img.get('alt'):
                    images_with_alt += 1
                else:
                    images_without_alt += 1
                    if images_without_alt <= 3:
                        src = img.get('src', img.get('data-src', 'unknown'))[:50]
                        warnings.append(f"Image missing alt: {src}...")
        
        # =================================================================
        # N-E-E-A-T-T CREDIBILITY SCORING
        # =================================================================
        text_lower = text.lower()
        
        # Notability
        notability = min(len(re.findall(r'(?:award|recognized|featured|leading|premier)', text_lower)) / 3, 1.0)
        
        # Experience
        experience = min(len(re.findall(r'(?:years? of experience|since \d{4}|established|founded)', text_lower)) / 2, 1.0)
        
        # Expertise
        expertise = min(len(re.findall(r'(?:certified|licensed|specialist|expert|professional)', text_lower)) / 3, 1.0)
        
        # Authoritativeness
        authoritativeness = min(len(re.findall(r'(?:research|studies|according to|data shows)', text_lower)) / 3, 1.0)
        
        # Trustworthiness
        trustworthiness = min(len(re.findall(r'(?:guarantee|secure|privacy|verified|trusted)', text_lower)) / 3, 1.0)
        
        # Transparency
        transparency = min(len(re.findall(r'(?:contact|about us|our team|phone|email|address)', text_lower)) / 3, 1.0)
        
        neeat_scores = {
            'notability': round(notability, 2),
            'experience': round(experience, 2),
            'expertise': round(expertise, 2),
            'authoritativeness': round(authoritativeness, 2),
            'trustworthiness': round(trustworthiness, 2),
            'transparency': round(transparency, 2)
        }
        
        # =================================================================
        # OVERALL SEO SCORE
        # =================================================================
        overall = (
            title_score * 0.20 +
            meta_score * 0.15 +
            h1_score * 0.15 +
            min(len(top_keywords) / 10, 1.0) * 0.15 +
            (1.0 if content.schema_data else 0.3) * 0.15 +
            np.mean(list(neeat_scores.values())) * 0.20
        )
        
        return SEOMetrics(
            overall_score=overall,
            title_score=title_score,
            title_length=title_length,
            meta_score=meta_score,
            meta_length=meta_length,
            h1_score=h1_score,
            h1_count=h1_count,
            word_count=word_count,
            keyword_density=keyword_density,
            top_keywords=top_keywords,
            top_bigrams=top_bigrams,
            top_trigrams=top_trigrams,
            warnings=warnings,
            heading_structure=heading_structure,
            internal_links=internal_links,
            external_links=external_links,
            images_with_alt=images_with_alt,
            images_without_alt=images_without_alt,
            neeat_scores=neeat_scores,
            details={}
        )

    # =========================================================================
    # KEYWORD GAP ANALYSIS
    # =========================================================================
    
    def _analyze_keyword_gaps(self, client: ScrapedContent, competitors: List[ScrapedContent], 
                               industry: str = '') -> List[dict]:
        """Find keywords competitors use that client doesn't"""
        
        if not competitors:
            return []
        
        # Preprocess
        def preprocess(text):
            tokens = re.findall(r'(?u)\b\w\w+\b', text.lower())
            return ' '.join([t for t in tokens if t not in STOP_WORDS and len(t) > 2])
        
        client_text = preprocess(client.text)
        comp_texts = [preprocess(c.text) for c in competitors]
        
        all_texts = [client_text] + comp_texts
        
        try:
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            features = self.tfidf.get_feature_names_out()
            
            client_scores = tfidf_matrix[0].toarray()[0]
            comp_scores = tfidf_matrix[1:].toarray()
            comp_avg = np.mean(comp_scores, axis=0)
            
            gaps = []
            for i, feature in enumerate(features):
                gap = comp_avg[i] - client_scores[i]
                if gap > 0.02:
                    gaps.append({
                        'keyword': feature,
                        'score': round(float(gap), 3),
                        'client': round(float(client_scores[i]), 3),
                        'competitor': round(float(comp_avg[i]), 3)
                    })
            
            gaps.sort(key=lambda x: x['score'], reverse=True)
            return gaps[:15]
        except:
            return []

    # =========================================================================
    # COMPETITIVE ANALYSIS
    # =========================================================================
    
    def _competitive_analysis(self, client_geo: GEOMetrics, client_seo: SEOMetrics,
                               competitors: List[ScrapedContent]) -> dict:
        """Analyze competitive positioning"""
        
        if not competitors:
            return {'similarity': 0.5, 'position': 'unknown'}
        
        try:
            client_text = ' '.join(client_seo.top_keywords[i][0] for i in range(min(10, len(client_seo.top_keywords))))
            client_emb = self.sentence_model.encode([client_text])
            
            similarities = []
            for comp in competitors:
                comp_tokens = re.findall(r'(?u)\b\w\w+\b', comp.text.lower())
                comp_keywords = [t for t in comp_tokens if t not in STOP_WORDS][:50]
                comp_text = ' '.join(comp_keywords)
                comp_emb = self.sentence_model.encode([comp_text])
                sim = float(cosine_similarity(client_emb, comp_emb)[0][0])
                similarities.append(sim)
            
            return {
                'similarity': np.mean(similarities),
                'position': 'competitive' if np.mean(similarities) > 0.5 else 'differentiated'
            }
        except:
            return {'similarity': 0.5, 'position': 'unknown'}

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    
    def _generate_recommendations(self, geo: GEOMetrics, seo: SEOMetrics, 
                                   gaps: List[dict]) -> List[dict]:
        """Generate prioritized recommendations"""
        
        recs = []
        
        # GEO recommendations
        if geo.claim_density < 4:
            recs.append({
                'priority': 'CRITICAL',
                'category': 'GEO-CLAIMS',
                'message': f'Increase claim density from {geo.claim_density:.1f} to 4+ per 100 words. Add more facts, statistics, and definitive statements.'
            })
        
        if geo.frontloading_score < 0.6:
            recs.append({
                'priority': 'CRITICAL', 
                'category': 'GEO-FRONTLOADING',
                'message': f'Improve answer frontloading. Only {geo.claims_in_first_100} claims in first 100 words. Lead with key facts.'
            })
        
        if geo.avg_sentence_length < 12 or geo.avg_sentence_length > 25:
            recs.append({
                'priority': 'HIGH',
                'category': 'GEO-SENTENCES',
                'message': f'Optimize sentence length. Currently {geo.avg_sentence_length:.0f} words avg, target 15-20 for AI extraction.'
            })
        
        if geo.schema_markup < 0.5:
            recs.append({
                'priority': 'HIGH',
                'category': 'GEO-SCHEMA',
                'message': 'Add JSON-LD schema for LocalBusiness and FAQPage.'
            })
        
        # SEO recommendations
        for warning in seo.warnings[:3]:
            recs.append({
                'priority': 'HIGH',
                'category': 'SEO-TECHNICAL',
                'message': warning
            })
        
        # Keyword gaps
        if gaps:
            top_gaps = ', '.join([g['keyword'] for g in gaps[:3]])
            recs.append({
                'priority': 'MEDIUM',
                'category': 'SEO-KEYWORDS',
                'message': f'Target competitor keywords: {top_gaps}'
            })
        
        # N-E-E-A-T-T
        weak_neeat = [k for k, v in seo.neeat_scores.items() if v < 0.5]
        if weak_neeat:
            recs.append({
                'priority': 'MEDIUM',
                'category': 'CREDIBILITY',
                'message': f'Improve credibility signals: {", ".join(weak_neeat)}'
            })
        
        return recs

    # =========================================================================
    # PROMPT GENERATION - COMPREHENSIVE
    # =========================================================================
    
    def generate_prompt(self, project: dict) -> str:
        """
        Generate a comprehensive, metrics-driven prompt for website generation.
        Uses ALL analysis data to create the most optimized output possible.
        """
        
        results = project.get('results', {})
        name = project.get('client_name', 'Business')
        location = project.get('location', 'Your Area')
        industry = project.get('industry', 'Services')
        
        # Extract all metrics
        geo_metrics = results.get('geoMetrics', {})
        seo_metrics = results.get('seoMetrics', {})
        keywords = results.get('topKeywords', [])
        bigrams = results.get('topBigrams', [])
        trigrams = results.get('topTrigrams', [])
        gaps = results.get('keywordGaps', [])
        geo_components = results.get('geoComponents', [])
        recommendations = results.get('recommendations', [])
        warnings = results.get('warnings', [])
        neeat_scores = seo_metrics.get('neeatScores', {})
        entities = geo_metrics.get('topEntities', [])
        
        # Current scores
        current_geo = results.get('geoScore', 0)
        current_seo = results.get('seoScore', 0)
        claim_density = geo_metrics.get('claimDensity', 0)
        avg_sentence = geo_metrics.get('avgSentenceLength', 25)
        frontloading = geo_metrics.get('frontloadingScore', 0)
        extractability = geo_metrics.get('extractability', 0)
        coverage_pred = geo_metrics.get('coveragePrediction', 50)
        word_count = seo_metrics.get('wordCount', 0)
        
        # Format keywords
        kw_primary = '\n'.join([f"  - {k['keyword']} (used {k['count']}x by client)" 
                                for k in keywords[:8]]) or f"  - {industry}"
        
        kw_bigrams = '\n'.join([f"  - \"{b['phrase']}\" ({b['count']}x)" 
                                for b in bigrams[:6]]) if bigrams else "  - (none found)"
        
        kw_trigrams = '\n'.join([f"  - \"{t['phrase']}\" ({t['count']}x)" 
                                 for t in trigrams[:4]]) if trigrams else "  - (none found)"
        
        kw_gaps = '\n'.join([f"  - {g['keyword']} (competitor score: {g['competitor']:.2f}, client: {g['client']:.2f})" 
                            for g in gaps[:8]]) if gaps else "  - (no competitors analyzed)"
        
        # Format weak areas that need improvement
        weak_components = [c for c in geo_components if c.get('score', 1) < 0.6]
        weak_areas = '\n'.join([f"  ⚠️ {c['name']}: {c['score']:.0%} - {c['tip']}" 
                                for c in weak_components]) if weak_components else "  ✓ All components adequate"
        
        # Format N-E-E-A-T-T weaknesses
        weak_neeat = [f"{k}: {v:.0%}" for k, v in neeat_scores.items() if v < 0.5]
        neeat_focus = ', '.join(weak_neeat) if weak_neeat else "All adequate"
        
        # Format critical recommendations
        critical_recs = [r for r in recommendations if r.get('priority') in ['CRITICAL', 'HIGH']]
        recs_text = '\n'.join([f"  • [{r['category']}] {r['message']}" 
                               for r in critical_recs[:5]]) if critical_recs else "  • No critical issues"
        
        # Calculate targets based on current performance
        target_claims = max(4, int(claim_density) + 2)  # At least 4, or current + 2
        target_words = 1200 if word_count < 800 else (1000 if word_count > 2000 else word_count)
        
        # Build the comprehensive prompt
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
    # UTILITY METHODS
    # =========================================================================
    
    def _error_results(self, client_info: dict, error: str) -> dict:
        return {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': 0, 'seoScore': 0, 'geoScore': 0, 'competitiveScore': 0,
            'error': error,
            'geoMetrics': {}, 'seoMetrics': {},
            'topKeywords': [], 'topBigrams': [], 'topTrigrams': [], 'keywordGaps': [],
            'geoComponents': [], 'radarData': [], 'warnings': [error],
            'recommendations': [{'priority': 'CRITICAL', 'category': 'ERROR', 'message': error}]
        }
    
    def analyze_geo_only(self, url: str) -> dict:
        """Standalone GEO analysis"""
        content = self._scrape_website(url)
        if not content.success:
            return {'error': content.error}
        
        geo = self._analyze_geo_comprehensive(content)
        
        return {
            'url': url,
            'overallScore': round(geo.overall_score * 100),
            'extractability': round(geo.extractability_score * 100),
            'readability': round(geo.readability_score * 100),
            'citability': round(geo.citability_score * 100),
            'metrics': {
                'claimDensity': round(geo.claim_density, 2),
                'totalClaims': geo.total_claims,
                'claimsInFirst100': geo.claims_in_first_100,
                'avgSentenceLength': round(geo.avg_sentence_length, 1),
                'wordCount': geo.word_count,
                'coveragePrediction': geo.coverage_prediction,
                'entityCount': geo.entity_count
            },
            'entities': geo.entities[:15],
            'details': geo.details
        }


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    pipeline = AtlanticDigitalPipeline()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        
        if '--geo' in sys.argv:
            print(f"\n🤖 GEO Analysis: {url}")
            result = pipeline.analyze_geo_only(url)
            
            print(f"\n{'='*50}")
            print(f"Overall GEO Score: {result.get('overallScore', 'N/A')}%")
            print(f"{'='*50}")
            print(f"Extractability:  {result.get('extractability', 'N/A')}%")
            print(f"Readability:     {result.get('readability', 'N/A')}%")
            print(f"Citability:      {result.get('citability', 'N/A')}%")
            print(f"\nMetrics:")
            for k, v in result.get('metrics', {}).items():
                print(f"  {k}: {v}")
            print(f"\nTop Entities: {', '.join(result.get('entities', [])[:10])}")
        else:
            print(f"\n🔍 Full Analysis: {url}")
            competitors = [a for a in sys.argv[2:] if not a.startswith('--')]
            
            results = pipeline.run_analysis(
                url, competitors,
                {'name': 'Test', 'location': 'Test', 'industry': 'Test'}
            )
            
            print(f"\n{'='*50}")
            print(f"Overall: {results['overallScore']}")
            print(f"SEO:     {results['seoScore']}")
            print(f"GEO:     {results['geoScore']}")
            print(f"\nGEO Metrics:")
            for k, v in results.get('geoMetrics', {}).items():
                print(f"  {k}: {v}")
    else:
        print("Usage:")
        print("  python pipeline_v4.py <url> --geo           # GEO-only analysis")
        print("  python pipeline_v4.py <url> [comp1] [comp2] # Full analysis")
