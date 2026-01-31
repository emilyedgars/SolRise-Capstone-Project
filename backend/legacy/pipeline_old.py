"""
Atlantic Digital - SEO/GEO Analysis Pipeline v2.0
==================================================
Improved pipeline with:
- Fixed scraping (proper async handling)
- Better preprocessing (preserves meaningful content)
- Comprehensive GEO analysis (all 6 components)
- Fixed regex patterns
- Domain-aware keyword extraction
- Content structure analysis
"""

from datetime import datetime
import asyncio
import re
import json
import numpy as np
from collections import Counter
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ML/NLP imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
from bs4 import BeautifulSoup
import requests

# Database
from pymongo import MongoClient
from bson import ObjectId

# Load spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


@dataclass
class ScrapedContent:
    """Container for scraped website data"""
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
    """Container for GEO analysis results"""
    overall_score: float
    quotable_statements: float
    statistics_density: float
    authoritative_language: float
    definitive_openers: float
    schema_markup: float
    entity_clarity: float
    faq_quality: float
    details: dict


class AtlanticDigitalPipeline:
    """
    Main SEO/GEO analysis pipeline for Atlantic Digital.
    
    Usage:
        pipeline = AtlanticDigitalPipeline(mongodb_uri="mongodb://localhost:27017")
        results = pipeline.run_analysis(
            client_url="https://example.com",
            competitor_urls=["https://competitor1.com", "https://competitor2.com"],
            client_info={"name": "Business Name", "location": "City, State", "industry": "Dental"}
        )
    """
    
    def __init__(self, mongodb_uri: Optional[str] = None, ollama_host: str = "http://localhost:11434"):
        # Database
        if mongodb_uri:
            try:
                self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
                self.client.server_info()  # Test connection
                self.db = self.client.atlantic_digital
                print("✅ Connected to MongoDB")
            except Exception as e:
                print(f"⚠️ MongoDB connection failed: {e}. Running without database.")
                self.db = None
        else:
            self.db = None
            print("⚠️ No MongoDB URI provided. Running without database.")
        
        self.ollama_host = ollama_host
        
        # NLP Models
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # TF-IDF with better settings
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 3),  # Include trigrams for phrases
            max_df=0.85,
            min_df=1,
            max_features=5000,
            stop_words='english',
            token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z]+\b'  # Only alphabetic tokens, 2+ chars
        )
        
        # Common web noise to filter
        self.noise_words = {
            'https', 'http', 'www', 'com', 'org', 'net', 'html', 'css', 'js',
            'svg', 'png', 'jpg', 'gif', 'pdf', 'button', 'click', 'menu',
            'nav', 'footer', 'header', 'sidebar', 'widget', 'copyright',
            'reserved', 'rights', 'privacy', 'policy', 'terms', 'conditions',
            'cookie', 'cookies', 'accept', 'decline', 'subscribe', 'newsletter',
            'follow', 'share', 'tweet', 'facebook', 'twitter', 'instagram',
            'linkedin', 'youtube', 'pinterest', 'email', 'phone', 'fax',
            'address', 'map', 'directions', 'hours', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        }
        
        # Industry-specific term boosters (add more as needed)
        self.industry_terms = {
            'dental': ['dentist', 'dental', 'teeth', 'tooth', 'orthodontic', 'implant', 
                      'crown', 'filling', 'extraction', 'whitening', 'cleaning', 'cavity',
                      'gum', 'periodontal', 'root canal', 'veneer', 'braces', 'invisalign'],
            'legal': ['attorney', 'lawyer', 'legal', 'law', 'court', 'litigation',
                     'settlement', 'injury', 'accident', 'compensation', 'case', 'trial'],
            'medical': ['doctor', 'physician', 'medical', 'health', 'patient', 'treatment',
                       'diagnosis', 'surgery', 'clinic', 'hospital', 'care', 'therapy'],
            'real_estate': ['property', 'home', 'house', 'real estate', 'realtor', 'agent',
                          'listing', 'buyer', 'seller', 'mortgage', 'closing', 'inspection']
        }

    # =========================================================================
    # MAIN ANALYSIS PIPELINE
    # =========================================================================
    
    def run_analysis(self, client_url: str, competitor_urls: List[str], 
                     client_info: dict, project_id: Optional[ObjectId] = None) -> dict:
        """
        Run the complete SEO/GEO analysis pipeline.
        
        Args:
            client_url: URL of the client's website
            competitor_urls: List of competitor URLs to analyze
            client_info: Dict with keys: name, location, industry, services (optional)
            project_id: MongoDB ObjectId for the project (optional)
            
        Returns:
            Dict containing all analysis results
        """
        print("\n" + "="*60)
        print("🚀 ATLANTIC DIGITAL SEO/GEO ANALYSIS PIPELINE")
        print("="*60)
        
        # Extract business info
        business_name = client_info.get('name', '').lower()
        location = client_info.get('location', '').lower()
        industry = client_info.get('industry', '').lower()
        
        # =====================================================================
        # STEP 1: SCRAPE WEBSITES
        # =====================================================================
        print("\n📥 STEP 1: Scraping websites...")
        
        client_data = self._scrape_website(client_url)
        if not client_data.success:
            print(f"   ❌ Failed to scrape client URL: {client_data.error}")
            # Return minimal results
            return self._generate_error_results(client_info, client_data.error)
        print(f"   ✓ Client: {client_data.word_count} words scraped")
        
        competitor_data = []
        for url in competitor_urls:
            if url and url.strip():
                comp = self._scrape_website(url)
                if comp.success:
                    competitor_data.append(comp)
                    print(f"   ✓ Competitor ({url[:40]}...): {comp.word_count} words")
                else:
                    print(f"   ⚠️ Failed: {url[:40]}... - {comp.error}")
        
        # =====================================================================
        # STEP 2: PREPROCESS TEXT
        # =====================================================================
        print("\n🔧 STEP 2: Preprocessing text...")
        
        client_processed = self._preprocess_text(client_data.text, preserve_entities=True)
        competitor_processed = [self._preprocess_text(c.text) for c in competitor_data]
        
        print(f"   ✓ Client: {len(client_processed.split())} tokens after preprocessing")
        
        # =====================================================================
        # STEP 3: TF-IDF KEYWORD ANALYSIS
        # =====================================================================
        print("\n📊 STEP 3: TF-IDF Keyword Analysis...")
        
        all_texts = [client_processed] + [cp for cp in competitor_processed if cp]
        
        if len(all_texts) >= 2 and all(len(t) > 50 for t in all_texts):
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            feature_names = self.tfidf.get_feature_names_out()
            
            # Get client's top keywords
            client_scores = tfidf_matrix[0].toarray()[0]
            top_indices = client_scores.argsort()[::-1][:30]
            top_keywords = [(feature_names[i], float(client_scores[i])) 
                           for i in top_indices if client_scores[i] > 0]
            
            # Find keyword gaps
            keyword_gaps = self._find_keyword_gaps(tfidf_matrix, feature_names, industry)
            
            print(f"   ✓ Found {len(top_keywords)} client keywords")
            print(f"   ✓ Found {len(keyword_gaps)} keyword gaps vs competitors")
        else:
            print("   ⚠️ Insufficient text for TF-IDF analysis")
            top_keywords = []
            keyword_gaps = []
            tfidf_matrix = None
        
        # =====================================================================
        # STEP 4: SEMANTIC SIMILARITY ANALYSIS
        # =====================================================================
        print("\n🧠 STEP 4: Semantic Similarity Analysis...")
        
        try:
            # Chunk long text for better embeddings
            client_embedding = self._get_document_embedding(client_processed)
            
            if competitor_processed:
                competitor_embeddings = [self._get_document_embedding(cp) 
                                        for cp in competitor_processed if cp]
                
                similarities = [float(cosine_similarity([client_embedding], [comp_emb])[0][0])
                               for comp_emb in competitor_embeddings]
                avg_similarity = np.mean(similarities) if similarities else 0.5
                
                print(f"   ✓ Average semantic similarity to competitors: {avg_similarity:.2f}")
            else:
                avg_similarity = 0.5
                print("   ⚠️ No competitors for similarity comparison")
        except Exception as e:
            print(f"   ⚠️ Semantic analysis error: {e}")
            avg_similarity = 0.5
        
        # =====================================================================
        # STEP 5: GEO ANALYSIS (COMPREHENSIVE)
        # =====================================================================
        print("\n🤖 STEP 5: GEO (Generative Engine Optimization) Analysis...")
        
        client_geo = self._analyze_geo_comprehensive(
            client_data, 
            business_name=business_name,
            location=location
        )
        print(f"   ✓ Client GEO Score: {client_geo.overall_score:.2f}")
        
        # Analyze competitor GEO
        competitor_geo_scores = []
        for comp in competitor_data:
            comp_geo = self._analyze_geo_comprehensive(comp)
            competitor_geo_scores.append(comp_geo.overall_score)
        
        avg_competitor_geo = np.mean(competitor_geo_scores) if competitor_geo_scores else 0.6
        print(f"   ✓ Competitor Average GEO: {avg_competitor_geo:.2f}")
        
        # =====================================================================
        # STEP 6: CONTENT STRUCTURE ANALYSIS
        # =====================================================================
        print("\n📝 STEP 6: Content Structure Analysis...")
        
        structure_analysis = self._analyze_content_structure(client_data)
        print(f"   ✓ H1 tags: {len(structure_analysis['h1_tags'])}")
        print(f"   ✓ H2 tags: {len(structure_analysis['h2_tags'])}")
        print(f"   ✓ Has FAQ section: {structure_analysis['has_faq']}")
        print(f"   ✓ Schema types found: {structure_analysis['schema_types']}")
        
        # =====================================================================
        # STEP 7: GENERATE RECOMMENDATIONS
        # =====================================================================
        print("\n🎯 STEP 7: Generating Recommendations...")
        
        recommendations = self._generate_recommendations(
            client_geo, 
            avg_competitor_geo,
            keyword_gaps,
            structure_analysis
        )
        print(f"   ✓ Generated {len(recommendations)} recommendations")
        
        # =====================================================================
        # COMPILE RESULTS
        # =====================================================================
        print("\n✅ ANALYSIS COMPLETE!")
        print("="*60)
        
        # Calculate overall scores
        seo_score = self._calculate_seo_score(structure_analysis, top_keywords)
        overall_score = (seo_score * 0.4) + (client_geo.overall_score * 0.5) + (avg_similarity * 0.1)
        
        results = {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': round(overall_score, 2),
            'seoScore': round(seo_score, 2),
            'geoScore': round(client_geo.overall_score, 2),
            'competitiveScore': round(avg_similarity, 2),
            'competitorAvgGeo': round(avg_competitor_geo, 2),
            
            # Keywords
            'topKeywords': [{'keyword': k[0], 'score': round(k[1], 3)} for k in top_keywords[:15]],
            'keywordGaps': keyword_gaps[:10],
            
            # GEO Components
            'geoComponents': [
                {'name': 'Quotable Statements', 'score': round(client_geo.quotable_statements, 2),
                 'tip': 'Add 5+ explicit citable statements like "At [Business], we believe..."'},
                {'name': 'Statistics Density', 'score': round(client_geo.statistics_density, 2),
                 'tip': 'Include percentages, numbers, years of experience'},
                {'name': 'Authoritative Language', 'score': round(client_geo.authoritative_language, 2),
                 'tip': 'Use phrases like "Research shows...", "Studies indicate..."'},
                {'name': 'Definitive Openers', 'score': round(client_geo.definitive_openers, 2),
                 'tip': 'Start paragraphs with definitive statements, not questions'},
                {'name': 'Schema Markup', 'score': round(client_geo.schema_markup, 2),
                 'tip': 'Add JSON-LD for LocalBusiness and FAQPage'},
                {'name': 'Entity Clarity', 'score': round(client_geo.entity_clarity, 2),
                 'tip': f'Mention "{business_name}" 8+ times and location 5+ times'},
                {'name': 'FAQ Quality', 'score': round(client_geo.faq_quality, 2),
                 'tip': 'Add 8-10 FAQs with definitive answers'}
            ],
            
            # Radar chart data
            'radarData': [
                {'subject': 'Keywords', 'client': int(min(len(top_keywords)/15, 1) * 100), 
                 'competitor': 75},
                {'subject': 'Quotables', 'client': int(client_geo.quotable_statements * 100),
                 'competitor': int(avg_competitor_geo * 100)},
                {'subject': 'Statistics', 'client': int(client_geo.statistics_density * 100),
                 'competitor': int(avg_competitor_geo * 85)},
                {'subject': 'Schema', 'client': int(client_geo.schema_markup * 100),
                 'competitor': 70},
                {'subject': 'Authority', 'client': int(client_geo.authoritative_language * 100),
                 'competitor': int(avg_competitor_geo * 90)},
                {'subject': 'Structure', 'client': int(seo_score * 100),
                 'competitor': 80}
            ],
            
            # Recommendations
            'recommendations': recommendations,
            
            # Raw details for debugging
            'debug': {
                'client_word_count': client_data.word_count,
                'competitors_analyzed': len(competitor_data),
                'geo_details': client_geo.details
            }
        }
        
        # Save to database
        if self.db and project_id:
            self.db.projects.update_one(
                {'_id': project_id},
                {'$set': {
                    'results': results,
                    'status': 'complete',
                    'completed_at': datetime.utcnow()
                }}
            )
        
        return results

    # =========================================================================
    # SCRAPING
    # =========================================================================
    
    def _scrape_website(self, url: str) -> ScrapedContent:
        """
        Scrape a website using Crawl4AI with proper async handling.
        Falls back to requests+BeautifulSoup if Crawl4AI fails.
        """
        if not url:
            return ScrapedContent(url='', html='', text='', title='', 
                                 meta_description='', headings={}, schema_data=[],
                                 word_count=0, success=False, error='Empty URL')
        
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url
        
        try:
            # Try Crawl4AI first (handles JavaScript)
            return self._scrape_with_crawl4ai(url)
        except Exception as e:
            print(f"   ⚠️ Crawl4AI failed, trying fallback: {e}")
            try:
                return self._scrape_with_requests(url)
            except Exception as e2:
                return ScrapedContent(
                    url=url, html='', text='', title='', meta_description='',
                    headings={}, schema_data=[], word_count=0,
                    success=False, error=str(e2)
                )
    
    def _scrape_with_crawl4ai(self, url: str) -> ScrapedContent:
        """Scrape using Crawl4AI (handles JavaScript-rendered content)"""
        from crawl4ai import AsyncWebCrawler
        
        async def crawl():
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                return result
        
        # Run async in sync context properly
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(crawl())
        
        html = result.html or ''
        text = result.markdown or ''
        
        # Parse HTML for additional data
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ''
        
        # Extract meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        meta_description = meta_desc.get('content', '') if meta_desc else ''
        
        # Extract headings
        headings = {
            'h1': [h.get_text().strip() for h in soup.find_all('h1')],
            'h2': [h.get_text().strip() for h in soup.find_all('h2')],
            'h3': [h.get_text().strip() for h in soup.find_all('h3')]
        }
        
        # Extract schema data
        schema_data = []
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                data = json.loads(script.string)
                schema_data.append(data)
            except:
                pass
        
        word_count = len(text.split())
        
        return ScrapedContent(
            url=url, html=html, text=text, title=title,
            meta_description=meta_description, headings=headings,
            schema_data=schema_data, word_count=word_count, success=True
        )
    
    def _scrape_with_requests(self, url: str) -> ScrapedContent:
        """Fallback scraping using requests (for static sites)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        # Extract metadata
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ''
        
        meta_desc = soup.find('meta', {'name': 'description'})
        meta_description = meta_desc.get('content', '') if meta_desc else ''
        
        headings = {
            'h1': [h.get_text().strip() for h in soup.find_all('h1')],
            'h2': [h.get_text().strip() for h in soup.find_all('h2')],
            'h3': [h.get_text().strip() for h in soup.find_all('h3')]
        }
        
        schema_data = []
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                data = json.loads(script.string)
                schema_data.append(data)
            except:
                pass
        
        return ScrapedContent(
            url=url, html=html, text=text, title=title,
            meta_description=meta_description, headings=headings,
            schema_data=schema_data, word_count=len(text.split()), success=True
        )

    # =========================================================================
    # TEXT PREPROCESSING
    # =========================================================================
    
    def _preprocess_text(self, text: str, preserve_entities: bool = False) -> str:
        """
        Preprocess text for NLP analysis.
        
        Args:
            text: Raw text from website
            preserve_entities: If True, preserve named entities (businesses, locations)
        """
        if not text:
            return ""
        
        # Basic cleaning
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'[\+\(]?[0-9][0-9\-\.\(\)\s]{8,}[0-9]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Process with spaCy (limit length to avoid memory issues)
        doc = nlp(text[:100000])
        
        tokens = []
        entities = []
        
        for token in doc:
            # Preserve named entities if requested
            if preserve_entities and token.ent_type_ in ['ORG', 'GPE', 'PERSON', 'PRODUCT']:
                entities.append(token.text)
            
            # Filter criteria
            if (not token.is_stop and 
                not token.is_punct and 
                not token.is_space and
                len(token.text) > 2 and
                token.text.isalpha() and
                token.text not in self.noise_words):
                
                # Use lemma for normalization
                lemma = token.lemma_
                if lemma not in self.noise_words and len(lemma) > 2:
                    tokens.append(lemma)
        
        return ' '.join(tokens)

    # =========================================================================
    # KEYWORD ANALYSIS
    # =========================================================================
    
    def _find_keyword_gaps(self, tfidf_matrix, feature_names: np.ndarray, 
                           industry: str = '') -> List[dict]:
        """
        Find keywords that competitors use more than the client.
        Prioritizes industry-relevant terms.
        """
        if tfidf_matrix is None or tfidf_matrix.shape[0] < 2:
            return []
        
        client_scores = tfidf_matrix[0].toarray()[0]
        competitor_scores = tfidf_matrix[1:].toarray()
        
        # Get industry terms for boosting
        industry_boost = set()
        for ind, terms in self.industry_terms.items():
            if ind in industry.lower():
                industry_boost = set(terms)
                break
        
        gaps = []
        for i, feature in enumerate(feature_names):
            client_score = client_scores[i]
            comp_avg = np.mean(competitor_scores[:, i])
            comp_max = np.max(competitor_scores[:, i])
            
            # Calculate gap
            gap = comp_avg - client_score
            
            # Only include significant gaps
            if gap > 0.02:
                # Boost industry-relevant terms
                relevance_boost = 1.5 if any(term in feature for term in industry_boost) else 1.0
                
                gaps.append({
                    'keyword': feature,
                    'score': round(float(gap * relevance_boost), 3),
                    'client_score': round(float(client_score), 3),
                    'competitor_avg': round(float(comp_avg), 3),
                    'competitor_max': round(float(comp_max), 3)
                })
        
        # Sort by score (gap * relevance)
        gaps.sort(key=lambda x: x['score'], reverse=True)
        
        return gaps[:15]
    
    def _get_document_embedding(self, text: str) -> np.ndarray:
        """
        Get document embedding by chunking long text and averaging.
        """
        if not text:
            return np.zeros(384)  # MiniLM embedding size
        
        # Split into chunks of ~500 words
        words = text.split()
        chunk_size = 500
        chunks = [' '.join(words[i:i+chunk_size]) 
                 for i in range(0, len(words), chunk_size)]
        
        if not chunks:
            return np.zeros(384)
        
        # Encode chunks and average
        embeddings = self.sentence_model.encode(chunks)
        return np.mean(embeddings, axis=0)

    # =========================================================================
    # GEO ANALYSIS (COMPREHENSIVE)
    # =========================================================================
    
    def _analyze_geo_comprehensive(self, content: ScrapedContent,
                                    business_name: str = '',
                                    location: str = '') -> GEOScore:
        """
        Comprehensive GEO (Generative Engine Optimization) analysis.
        Analyzes all 7 key components that affect AI citation rates.
        """
        text = content.text
        html = content.html
        text_lower = text.lower() if text else ''
        
        details = {}
        
        # =====================================================================
        # 1. QUOTABLE STATEMENTS (Weight: 25%)
        # =====================================================================
        # AI systems extract and cite explicit statements
        
        quotable_patterns = [
            r'"[^"]{20,150}"',  # Explicit quotes
            r'"[^"]{20,150}"',  # Smart quotes
            r'(?:we believe|our approach|our mission|our goal|our vision)[^.]{15,100}\.',
            r'(?:at ' + re.escape(business_name) + r')[^.]{20,100}\.' if business_name else r'(?!)',
        ]
        
        quotables_found = []
        for pattern in quotable_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            quotables_found.extend(matches)
        
        quotable_score = min(len(quotables_found) / 5, 1.0)
        details['quotables_count'] = len(quotables_found)
        details['quotables_examples'] = quotables_found[:3]
        
        # =====================================================================
        # 2. STATISTICS DENSITY (Weight: 20%)
        # =====================================================================
        # AI systems prioritize factual, quantifiable claims
        
        stat_patterns = [
            r'\d+%',  # Percentages
            r'\d+\s*(?:years?|months?)\s*(?:of experience|serving|established)',
            r'(?:over|more than|approximately)\s*\d+[,\d]*\s*(?:customers?|patients?|clients?|families?)',
            r'\d+\s*out of\s*\d+',
            r'(?:rated|rating|score)[^.]*\d+(?:\.\d+)?(?:/\d+|%|stars?)',
            r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
            r'(?:since|established in|founded in)\s*\d{4}',
            r'\d+\+?\s*(?:locations?|offices?|branches?)',
        ]
        
        stats_found = []
        for pattern in stat_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            stats_found.extend(matches)
        
        stats_score = min(len(stats_found) / 4, 1.0)
        details['stats_count'] = len(stats_found)
        details['stats_examples'] = stats_found[:5]
        
        # =====================================================================
        # 3. AUTHORITATIVE LANGUAGE (Weight: 15%)
        # =====================================================================
        # Phrases that establish expertise and credibility
        
        authority_patterns = [
            r'(?:studies|research)\s+(?:show|indicate|suggest|demonstrate)',
            r'(?:according to|based on)\s+(?:research|studies|data|experts?)',
            r'(?:experts?|specialists?|professionals?)\s+(?:recommend|suggest|advise)',
            r'(?:board[- ]certified|licensed|accredited|certified)',
            r'(?:clinically|scientifically|medically)\s+(?:proven|tested|validated)',
            r'(?:industry[- ]leading|award[- ]winning|top[- ]rated)',
            r'(?:evidence[- ]based|data[- ]driven|research[- ]backed)',
        ]
        
        authority_count = 0
        authority_examples = []
        for pattern in authority_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            authority_count += len(matches)
            authority_examples.extend(matches)
        
        authority_score = min(authority_count / 6, 1.0)
        details['authority_count'] = authority_count
        details['authority_examples'] = authority_examples[:5]
        
        # =====================================================================
        # 4. DEFINITIVE OPENERS (Weight: 15%)
        # =====================================================================
        # Paragraphs that start with definitive answers, not questions
        
        paragraphs = text.split('\n\n') if text else []
        definitive_patterns = [
            r'^(?:the|our|we|this|here|yes|no)\s',
            r'^\d+',
            r'^[A-Z][a-z]+\s+(?:is|are|was|were|has|have|provides?|offers?)\s',
        ]
        
        definitive_count = 0
        total_paragraphs = 0
        
        for para in paragraphs[:20]:  # Check first 20 paragraphs
            para = para.strip()
            if len(para) < 30:  # Skip short paragraphs
                continue
            total_paragraphs += 1
            
            for pattern in definitive_patterns:
                if re.match(pattern, para, re.IGNORECASE):
                    definitive_count += 1
                    break
        
        definitive_score = definitive_count / max(total_paragraphs, 1)
        details['definitive_openers'] = definitive_count
        details['total_paragraphs_checked'] = total_paragraphs
        
        # =====================================================================
        # 5. SCHEMA MARKUP (Weight: 10%)
        # =====================================================================
        # JSON-LD structured data for machine parsing
        
        schema_types = set()
        for schema in content.schema_data:
            if isinstance(schema, dict):
                schema_type = schema.get('@type', '')
                if isinstance(schema_type, list):
                    schema_types.update(schema_type)
                else:
                    schema_types.add(schema_type)
                
                # Check @graph
                if '@graph' in schema:
                    for item in schema['@graph']:
                        if isinstance(item, dict):
                            item_type = item.get('@type', '')
                            if isinstance(item_type, list):
                                schema_types.update(item_type)
                            else:
                                schema_types.add(item_type)
        
        # Score based on important schema types
        important_schemas = {'LocalBusiness', 'Organization', 'FAQPage', 'Service', 
                           'Product', 'Review', 'AggregateRating', 'WebPage'}
        found_important = schema_types & important_schemas
        
        schema_score = min(len(found_important) / 3, 1.0)
        details['schema_types'] = list(schema_types)
        details['important_schemas'] = list(found_important)
        
        # =====================================================================
        # 6. ENTITY CLARITY (Weight: 10%)
        # =====================================================================
        # How clearly the business name and location are mentioned
        
        if business_name and len(business_name) > 2:
            name_mentions = text_lower.count(business_name)
            name_score = min(name_mentions / 8, 1.0)
        else:
            name_score = 0.5  # Default if no business name provided
        
        if location and len(location) > 2:
            location_mentions = text_lower.count(location)
            location_score = min(location_mentions / 5, 1.0)
        else:
            location_score = 0.5
        
        entity_score = (name_score + location_score) / 2
        details['business_name_mentions'] = name_mentions if business_name else 'N/A'
        details['location_mentions'] = location_mentions if location else 'N/A'
        
        # =====================================================================
        # 7. FAQ QUALITY (Weight: 5%)
        # =====================================================================
        # Presence and quality of FAQ content
        
        # Check for FAQ section
        faq_indicators = [
            r'(?:frequently\s+asked\s+questions?|faq)',
            r'(?:common\s+questions?|q\s*&\s*a)',
        ]
        
        has_faq_section = any(re.search(pattern, text_lower) for pattern in faq_indicators)
        
        # Count Q&A patterns
        qa_patterns = [
            r'(?:^|\n)\s*(?:q:|question:?)\s*[^\n]+\n\s*(?:a:|answer:?)\s*[^\n]+',
            r'(?:^|\n)\s*(?:what|how|why|when|where|who|can|do|does|is|are)\s+[^\n?]+\?\s*\n[^\n]+',
        ]
        
        qa_count = 0
        for pattern in qa_patterns:
            qa_count += len(re.findall(pattern, text_lower, re.MULTILINE))
        
        # Also check for FAQPage schema
        has_faq_schema = 'FAQPage' in schema_types
        
        faq_score = 0.0
        if has_faq_schema:
            faq_score = 1.0
        elif has_faq_section and qa_count >= 5:
            faq_score = 0.8
        elif has_faq_section or qa_count >= 3:
            faq_score = 0.5
        elif qa_count >= 1:
            faq_score = 0.3
        
        details['has_faq_section'] = has_faq_section
        details['has_faq_schema'] = has_faq_schema
        details['qa_count'] = qa_count
        
        # =====================================================================
        # CALCULATE OVERALL GEO SCORE
        # =====================================================================
        weights = {
            'quotable': 0.25,
            'statistics': 0.20,
            'authority': 0.15,
            'openers': 0.15,
            'schema': 0.10,
            'entity': 0.10,
            'faq': 0.05
        }
        
        overall = (
            quotable_score * weights['quotable'] +
            stats_score * weights['statistics'] +
            authority_score * weights['authority'] +
            definitive_score * weights['openers'] +
            schema_score * weights['schema'] +
            entity_score * weights['entity'] +
            faq_score * weights['faq']
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
    # CONTENT STRUCTURE ANALYSIS
    # =========================================================================
    
    def _analyze_content_structure(self, content: ScrapedContent) -> dict:
        """Analyze the HTML structure for SEO best practices."""
        
        soup = BeautifulSoup(content.html, 'html.parser') if content.html else None
        
        result = {
            'h1_tags': content.headings.get('h1', []),
            'h2_tags': content.headings.get('h2', []),
            'h3_tags': content.headings.get('h3', []),
            'title': content.title,
            'title_length': len(content.title),
            'meta_description': content.meta_description,
            'meta_description_length': len(content.meta_description),
            'has_faq': False,
            'schema_types': [],
            'internal_links': 0,
            'external_links': 0,
            'images_with_alt': 0,
            'images_without_alt': 0,
        }
        
        if soup:
            # Check for FAQ section
            faq_section = soup.find(id=re.compile('faq', re.I)) or \
                         soup.find(class_=re.compile('faq', re.I))
            result['has_faq'] = faq_section is not None
            
            # Count links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and content.url not in href:
                    result['external_links'] += 1
                elif href.startswith('/') or href.startswith('#'):
                    result['internal_links'] += 1
            
            # Check images
            for img in soup.find_all('img'):
                if img.get('alt'):
                    result['images_with_alt'] += 1
                else:
                    result['images_without_alt'] += 1
        
        # Schema types
        for schema in content.schema_data:
            if isinstance(schema, dict):
                schema_type = schema.get('@type')
                if schema_type:
                    if isinstance(schema_type, list):
                        result['schema_types'].extend(schema_type)
                    else:
                        result['schema_types'].append(schema_type)
        
        return result

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    
    def _generate_recommendations(self, client_geo: GEOScore, avg_competitor_geo: float,
                                   keyword_gaps: List[dict], structure: dict) -> List[dict]:
        """Generate prioritized recommendations based on analysis."""
        
        recommendations = []
        
        # GEO Recommendations
        if client_geo.schema_markup < 0.5:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'GEO-SCHEMA',
                'message': 'Add JSON-LD structured data for LocalBusiness and FAQPage schemas'
            })
        
        if client_geo.quotable_statements < 0.6:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'GEO-QUOTABLES',
                'message': f'Add more quotable statements. Found {client_geo.details.get("quotables_count", 0)}, need 5+'
            })
        
        if client_geo.statistics_density < 0.5:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'GEO-STATISTICS',
                'message': 'Include more statistics: percentages, years of experience, customer counts'
            })
        
        if client_geo.faq_quality < 0.5:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'GEO-FAQ',
                'message': 'Add FAQ section with 8-10 questions and definitive answers'
            })
        
        if client_geo.authoritative_language < 0.5:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'GEO-AUTHORITY',
                'message': 'Add authoritative phrases: "Research shows...", "Board-certified...", "Studies indicate..."'
            })
        
        if client_geo.definitive_openers < 0.6:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'GEO-OPENERS',
                'message': 'Start paragraphs with definitive statements instead of questions'
            })
        
        if client_geo.entity_clarity < 0.6:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'GEO-ENTITIES',
                'message': 'Mention business name and location more frequently throughout content'
            })
        
        # SEO Recommendations
        if len(structure['h1_tags']) != 1:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'SEO-H1',
                'message': f'Page should have exactly 1 H1 tag. Found: {len(structure["h1_tags"])}'
            })
        
        if structure['title_length'] < 50 or structure['title_length'] > 60:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'SEO-TITLE',
                'message': f'Title should be 50-60 chars. Current: {structure["title_length"]} chars'
            })
        
        if structure['meta_description_length'] < 150 or structure['meta_description_length'] > 160:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'SEO-META',
                'message': f'Meta description should be 150-160 chars. Current: {structure["meta_description_length"]} chars'
            })
        
        # Keyword Recommendations
        if keyword_gaps:
            top_gaps = ', '.join([g['keyword'] for g in keyword_gaps[:3]])
            recommendations.append({
                'priority': 'HIGH',
                'category': 'SEO-KEYWORDS',
                'message': f'Target competitor keywords: {top_gaps}'
            })
        
        # Competitive Recommendations
        if client_geo.overall_score < avg_competitor_geo - 0.15:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'COMPETITIVE',
                'message': f'GEO score ({client_geo.overall_score:.2f}) is significantly below competitors ({avg_competitor_geo:.2f})'
            })
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 99))
        
        return recommendations

    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _calculate_seo_score(self, structure: dict, keywords: List) -> float:
        """Calculate overall SEO score based on technical factors."""
        scores = []
        
        # H1 tag (1 is optimal)
        h1_count = len(structure['h1_tags'])
        scores.append(1.0 if h1_count == 1 else 0.5 if h1_count > 0 else 0.0)
        
        # Title length
        title_len = structure['title_length']
        scores.append(1.0 if 50 <= title_len <= 60 else 0.6 if 40 <= title_len <= 70 else 0.3)
        
        # Meta description
        meta_len = structure['meta_description_length']
        scores.append(1.0 if 150 <= meta_len <= 160 else 0.6 if 120 <= meta_len <= 180 else 0.3)
        
        # Schema markup
        scores.append(1.0 if structure['schema_types'] else 0.0)
        
        # Keyword coverage
        scores.append(min(len(keywords) / 10, 1.0))
        
        return np.mean(scores)
    
    def _generate_error_results(self, client_info: dict, error: str) -> dict:
        """Generate minimal results when analysis fails."""
        return {
            'clientName': client_info.get('name', 'Client'),
            'overallScore': 0,
            'seoScore': 0,
            'geoScore': 0,
            'competitiveScore': 0,
            'error': error,
            'topKeywords': [],
            'keywordGaps': [],
            'geoComponents': [],
            'recommendations': [{
                'priority': 'CRITICAL',
                'category': 'ERROR',
                'message': f'Analysis failed: {error}'
            }],
            'radarData': []
        }

    # =========================================================================
    # PROMPT GENERATION
    # =========================================================================
    
    def generate_prompt(self, project: dict) -> str:
        """Generate an optimized prompt for website generation."""
        
        results = project.get('results', {})
        client_name = project.get('client_name', 'Business')
        location = project.get('location', 'the area')
        industry = project.get('industry', 'services')
        
        top_keywords = results.get('topKeywords', [])
        keyword_gaps = results.get('keywordGaps', [])
        geo_components = results.get('geoComponents', [])
        
        # Format keywords
        keywords_str = '\n'.join([f"- {k['keyword']} (score: {k['score']})" 
                                  for k in top_keywords[:10]] if top_keywords else ['- [Run analysis to get keywords]'])
        
        gaps_str = '\n'.join([f"- {g['keyword']} (gap: {g['score']})" 
                             for g in keyword_gaps[:10]] if keyword_gaps else ['- [Run analysis to find gaps]'])
        
        # Identify weak GEO components
        weak_geo = [c for c in geo_components if c.get('score', 0) < 0.6]
        geo_focus = '\n'.join([f"- {c['name']}: {c['tip']}" for c in weak_geo]) if weak_geo else '- All GEO components adequate'
        
        prompt = f"""You are an expert SEO and GEO website content generator.

## BUSINESS CONTEXT
- Business Name: {client_name}
- Industry: {industry}
- Location: {location}

## PART 1: SEO REQUIREMENTS

### Primary Keywords (use naturally 2-3 times each)
{keywords_str}

### Competitor Keyword Gaps (incorporate these)
{gaps_str}

### Technical SEO Requirements
- Valid HTML5 with semantic tags (header, main, section, article, footer, nav)
- Exactly ONE H1 tag containing primary keyword + location
- Meta title: 50-60 characters, format: "Primary Keyword | {client_name} | {location}"
- Meta description: 150-160 characters with call-to-action
- Use H2 tags for main sections, H3 for subsections
- Include internal navigation links

## PART 2: GEO REQUIREMENTS (CRITICAL FOR AI SEARCH)

### Areas Needing Improvement
{geo_focus}

### Required GEO Elements

1. QUOTABLE STATEMENTS (minimum 5)
   Include explicit, citable statements:
   - "At {client_name}, we believe [definitive statement about values/approach]"
   - "Our mission is to [clear value proposition]"
   - "[X]% of our customers experience [positive outcome]"

2. STATISTICS WITH CONTEXT (minimum 4)
   - Years of experience: "Serving {location} for over X years"
   - Success metrics: "X% customer satisfaction rating"
   - Volume: "Trusted by X+ families in {location}"
   - Credentials: "X board-certified specialists"

3. AUTHORITATIVE LANGUAGE
   Use phrases like:
   - "Research demonstrates that..."
   - "Industry experts recommend..."
   - "Board-certified specialists advise..."
   - "Studies indicate..."

4. ANSWER-FIRST STRUCTURE
   Start every section with a definitive answer:
   ✓ "The best {industry} combines expertise, technology, and patient care."
   ✗ "You might be wondering what makes a great {industry}..."

5. FAQ SECTION (minimum 8 questions)
   Format each as:
   Q: [Natural language question people actually search]
   A: [Definitive first sentence] [Supporting details] [Call to action]

6. JSON-LD SCHEMA MARKUP
   Include in <head>:
   - LocalBusiness schema with name, address, phone, hours
   - FAQPage schema wrapping all FAQ content

## CONTENT STRUCTURE

1. HERO SECTION
   - Clear value proposition in first sentence
   - Business name + location prominently displayed
   - Primary CTA button

2. SERVICES/OFFERINGS
   - List main services with brief descriptions
   - Include relevant keywords naturally

3. ABOUT/TRUST SECTION
   - Team credentials and experience
   - Statistics and achievements
   - Quotable mission statement

4. FAQ SECTION
   - 8-10 questions with schema markup
   - Conversational but authoritative answers

5. CONTACT/CTA SECTION
   - Multiple contact methods
   - Clear call-to-action
   - Location information

## OUTPUT FORMAT

Return ONLY valid HTML5 code starting with <!DOCTYPE html>.
Include all CSS in a <style> tag in the <head>.
Include JSON-LD schema in <script type="application/ld+json"> tags.
Do NOT include any explanations, markdown, or comments.
"""
        return prompt

    # =========================================================================
    # WEBSITE GENERATION (with Ollama or Claude)
    # =========================================================================
    
    def generate_website_ollama(self, prompt: str) -> str:
        """Generate website using local Ollama/Qwen model."""
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
                timeout=300
            )
            
            result = response.json()
            html = result.get('response', '')
            
            # Clean up response (remove markdown if present)
            if '```html' in html:
                html = html.split('```html')[1].split('```')[0]
            elif '```' in html:
                html = html.split('```')[1].split('```')[0]
            
            return html.strip()
            
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return ""
    
    def analyze_geo_only(self, url: str) -> dict:
        """Standalone GEO analysis for any URL."""
        content = self._scrape_website(url)
        if not content.success:
            return {'error': content.error}
        
        geo = self._analyze_geo_comprehensive(content)
        
        return {
            'url': url,
            'score': round(geo.overall_score * 100),
            'components': {
                'quotable_statements': round(geo.quotable_statements * 100),
                'statistics_density': round(geo.statistics_density * 100),
                'authoritative_language': round(geo.authoritative_language * 100),
                'definitive_openers': round(geo.definitive_openers * 100),
                'schema_markup': round(geo.schema_markup * 100),
                'entity_clarity': round(geo.entity_clarity * 100),
                'faq_quality': round(geo.faq_quality * 100)
            },
            'details': geo.details
        }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("🧪 ATLANTIC DIGITAL PIPELINE - TEST MODE")
    print("="*60)
    
    # Initialize pipeline without database for testing
    pipeline = AtlanticDigitalPipeline(mongodb_uri=None)
    
    if len(sys.argv) > 1:
        # Test with provided URL
        test_url = sys.argv[1]
        print(f"\n📍 Testing with URL: {test_url}")
        
        if len(sys.argv) > 2 and sys.argv[2] == '--geo':
            # GEO-only analysis
            print("\n🤖 Running GEO-only analysis...")
            result = pipeline.analyze_geo_only(test_url)
            
            print(f"\n📊 GEO Score: {result.get('score', 'N/A')}%")
            print("\nComponent Scores:")
            for comp, score in result.get('components', {}).items():
                bar = '█' * (score // 10) + '░' * (10 - score // 10)
                print(f"  {comp:25s} [{bar}] {score}%")
            
            print("\nDetails:")
            for key, value in result.get('details', {}).items():
                if not isinstance(value, list) or len(value) <= 3:
                    print(f"  {key}: {value}")
        else:
            # Full analysis with mock competitors
            print("\n🔍 Running full analysis...")
            
            competitors = sys.argv[2:] if len(sys.argv) > 2 else []
            
            results = pipeline.run_analysis(
                client_url=test_url,
                competitor_urls=competitors,
                client_info={
                    'name': 'Test Business',
                    'location': 'Test City',
                    'industry': 'general'
                }
            )
            
            print("\n" + "="*60)
            print("📊 RESULTS SUMMARY")
            print("="*60)
            print(f"Overall Score: {results['overallScore']}")
            print(f"SEO Score: {results['seoScore']}")
            print(f"GEO Score: {results['geoScore']}")
            print(f"Competitive Score: {results['competitiveScore']}")
            
            print("\n🎯 Top Keywords:")
            for kw in results.get('topKeywords', [])[:5]:
                print(f"  - {kw['keyword']}: {kw['score']}")
            
            print("\n📋 Recommendations:")
            for rec in results.get('recommendations', [])[:5]:
                print(f"  [{rec['priority']}] {rec['category']}: {rec['message']}")
    else:
        print("\nUsage:")
        print("  python pipeline_v2.py <url>                    # Full analysis")
        print("  python pipeline_v2.py <url> --geo              # GEO-only analysis")
        print("  python pipeline_v2.py <url> <comp1> <comp2>    # With competitors")
        print("\nExample:")
        print("  python pipeline_v2.py https://example-dental.com --geo")
