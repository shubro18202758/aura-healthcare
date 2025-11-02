"""
AURA Healthcare - Medical Knowledge Fetcher
Automatically fetches and populates medical knowledge from various online sources
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class MedicalKnowledgeFetcher:
    """Fetches medical knowledge from various online sources"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'AURA Healthcare System/1.0 (Medical Education)'
                }
            )
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    # ==================== PubMed / NCBI ====================
    
    async def fetch_pubmed_articles(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch medical research articles from PubMed
        Uses NCBI E-utilities API (free, no API key required for basic usage)
        """
        try:
            # Step 1: Search for article IDs
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json'
            }
            
            async with self.session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    logger.error(f"PubMed search failed: {response.status}")
                    return []
                
                data = await response.json()
                id_list = data.get('esearchresult', {}).get('idlist', [])
            
            if not id_list:
                return []
            
            # Step 2: Fetch article summaries
            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            summary_params = {
                'db': 'pubmed',
                'id': ','.join(id_list),
                'retmode': 'json'
            }
            
            async with self.session.get(summary_url, params=summary_params) as response:
                if response.status != 200:
                    logger.error(f"PubMed summary failed: {response.status}")
                    return []
                
                data = await response.json()
                results = data.get('result', {})
            
            # Step 3: Fetch full abstracts
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(id_list),
                'retmode': 'xml'
            }
            
            async with self.session.get(fetch_url, params=fetch_params) as response:
                if response.status != 200:
                    logger.error(f"PubMed fetch failed: {response.status}")
                    return []
                
                xml_text = await response.text()
                abstracts = self._parse_pubmed_xml(xml_text)
            
            # Combine data
            articles = []
            for pmid in id_list:
                if pmid in results and pmid in abstracts:
                    article_data = results[pmid]
                    articles.append({
                        'content': abstracts[pmid],
                        'metadata': {
                            'source': 'PubMed',
                            'pmid': pmid,
                            'title': article_data.get('title', ''),
                            'authors': ', '.join([author.get('name', '') for author in article_data.get('authors', [])[:3]]),
                            'journal': article_data.get('fulljournalname', ''),
                            'pub_date': article_data.get('pubdate', ''),
                            'category': 'research',
                            'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            'fetched_at': datetime.utcnow().isoformat()
                        }
                    })
            
            logger.info(f"Fetched {len(articles)} PubMed articles for query: {query}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching PubMed articles: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_text: str) -> Dict[str, str]:
        """Parse PubMed XML to extract abstracts"""
        try:
            soup = BeautifulSoup(xml_text, 'xml')
            abstracts = {}
            
            for article in soup.find_all('PubmedArticle'):
                pmid_tag = article.find('PMID')
                abstract_tag = article.find('Abstract')
                
                if pmid_tag and abstract_tag:
                    pmid = pmid_tag.text
                    abstract_texts = []
                    
                    for abstract_text in abstract_tag.find_all('AbstractText'):
                        label = abstract_text.get('Label', '')
                        text = abstract_text.text
                        if label:
                            abstract_texts.append(f"{label}: {text}")
                        else:
                            abstract_texts.append(text)
                    
                    abstracts[pmid] = '\n\n'.join(abstract_texts)
            
            return abstracts
        except Exception as e:
            logger.error(f"Error parsing PubMed XML: {e}")
            return {}
    
    # ==================== WHO Guidelines ====================
    
    async def fetch_who_guidelines(self) -> List[Dict[str, Any]]:
        """
        Fetch WHO medical guidelines
        Scrapes from WHO website (public information)
        """
        try:
            guidelines = []
            
            # WHO COVID-19 Guidelines
            covid_url = "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/technical-guidance"
            guidelines.extend(await self._fetch_who_page(covid_url, "COVID-19"))
            
            # WHO Diabetes Guidelines
            diabetes_url = "https://www.who.int/health-topics/diabetes"
            guidelines.extend(await self._fetch_who_page(diabetes_url, "Diabetes"))
            
            # WHO Hypertension Guidelines
            hypertension_url = "https://www.who.int/news-room/fact-sheets/detail/hypertension"
            guidelines.extend(await self._fetch_who_page(hypertension_url, "Hypertension"))
            
            logger.info(f"Fetched {len(guidelines)} WHO guidelines")
            return guidelines
            
        except Exception as e:
            logger.error(f"Error fetching WHO guidelines: {e}")
            return []
    
    async def _fetch_who_page(self, url: str, topic: str) -> List[Dict[str, Any]]:
        """Fetch and parse a WHO guideline page"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract main content
                content_divs = soup.find_all(['div', 'article', 'section'], class_=['content', 'main-content', 'article-body'])
                
                if not content_divs:
                    # Fallback: get all paragraphs
                    content_divs = [soup.find('body')]
                
                content_text = []
                for div in content_divs:
                    if div:
                        paragraphs = div.find_all(['p', 'li'])
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if len(text) > 50:  # Filter out short/empty paragraphs
                                content_text.append(text)
                
                if content_text:
                    return [{
                        'content': '\n\n'.join(content_text[:50]),  # Limit content
                        'metadata': {
                            'source': 'WHO',
                            'topic': topic,
                            'category': 'guidelines',
                            'url': url,
                            'fetched_at': datetime.utcnow().isoformat()
                        }
                    }]
                
                return []
                
        except Exception as e:
            logger.error(f"Error fetching WHO page {url}: {e}")
            return []
    
    # ==================== CDC Guidelines ====================
    
    async def fetch_cdc_guidelines(self) -> List[Dict[str, Any]]:
        """
        Fetch CDC medical guidelines
        Scrapes from CDC website (public information)
        """
        try:
            guidelines = []
            
            # CDC topics
            topics = [
                ("https://www.cdc.gov/diabetes/basics/index.html", "Diabetes"),
                ("https://www.cdc.gov/bloodpressure/index.htm", "Blood Pressure"),
                ("https://www.cdc.gov/heartdisease/about.htm", "Heart Disease"),
                ("https://www.cdc.gov/cancer/preventable/index.htm", "Cancer Prevention"),
            ]
            
            for url, topic in topics:
                guidelines.extend(await self._fetch_cdc_page(url, topic))
            
            logger.info(f"Fetched {len(guidelines)} CDC guidelines")
            return guidelines
            
        except Exception as e:
            logger.error(f"Error fetching CDC guidelines: {e}")
            return []
    
    async def _fetch_cdc_page(self, url: str, topic: str) -> List[Dict[str, Any]]:
        """Fetch and parse a CDC guideline page"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract main content
                content_text = []
                main_content = soup.find(['main', 'article', 'div'], class_=['content', 'main-content'])
                
                if main_content:
                    paragraphs = main_content.find_all(['p', 'li'])
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if len(text) > 50:
                            content_text.append(text)
                
                if content_text:
                    return [{
                        'content': '\n\n'.join(content_text[:50]),
                        'metadata': {
                            'source': 'CDC',
                            'topic': topic,
                            'category': 'guidelines',
                            'url': url,
                            'fetched_at': datetime.utcnow().isoformat()
                        }
                    }]
                
                return []
                
        except Exception as e:
            logger.error(f"Error fetching CDC page {url}: {e}")
            return []
    
    # ==================== Drug Information ====================
    
    async def fetch_drug_information(self, drug_name: str) -> List[Dict[str, Any]]:
        """
        Fetch drug information from RxNorm/DailyMed (NLM APIs)
        Free public API, no key required
        """
        try:
            # Search RxNorm for drug concept
            rxnorm_url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={drug_name}"
            
            async with self.session.get(rxnorm_url) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                drug_group = data.get('drugGroup', {})
                concept_properties = drug_group.get('conceptGroup', [])
                
                drugs = []
                for concept_group in concept_properties:
                    if 'conceptProperties' in concept_group:
                        for prop in concept_group['conceptProperties'][:5]:  # Limit to 5
                            rxcui = prop.get('rxcui')
                            name = prop.get('name')
                            
                            if rxcui:
                                # Get drug properties
                                props_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/allProperties.json?prop=all"
                                async with self.session.get(props_url) as props_response:
                                    if props_response.status == 200:
                                        props_data = await props_response.json()
                                        properties = props_data.get('propConceptGroup', {}).get('propConcept', [])
                                        
                                        content_parts = [f"Drug Name: {name}"]
                                        for prop in properties:
                                            prop_name = prop.get('propName', '')
                                            prop_value = prop.get('propValue', '')
                                            if prop_value:
                                                content_parts.append(f"{prop_name}: {prop_value}")
                                        
                                        drugs.append({
                                            'content': '\n'.join(content_parts),
                                            'metadata': {
                                                'source': 'RxNorm',
                                                'drug_name': name,
                                                'rxcui': rxcui,
                                                'category': 'drug_information',
                                                'url': f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={rxcui}",
                                                'fetched_at': datetime.utcnow().isoformat()
                                            }
                                        })
                
                logger.info(f"Fetched {len(drugs)} drug information entries for: {drug_name}")
                return drugs
                
        except Exception as e:
            logger.error(f"Error fetching drug information: {e}")
            return []
    
    # ==================== Medical Conditions (MedlinePlus) ====================
    
    async def fetch_medlineplus_info(self, condition: str) -> List[Dict[str, Any]]:
        """
        Fetch medical condition information from MedlinePlus
        Uses NLM Connect API (free, no key required)
        """
        try:
            # Search for the condition
            search_url = "https://connect.medlineplus.gov/service"
            params = {
                'mainSearchCriteria.v.cs': '2.16.840.1.113883.6.103',
                'mainSearchCriteria.v.dn': condition,
                'knowledgeResponseType': 'application/json'
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                feed = data.get('feed', {})
                entries = feed.get('entry', [])
                
                conditions = []
                for entry in entries[:5]:  # Limit to 5
                    title = entry.get('title', {}).get('_value', '')
                    summary = entry.get('summary', {}).get('_value', '')
                    link = entry.get('link', [{}])[0].get('href', '')
                    
                    if summary:
                        conditions.append({
                            'content': f"Condition: {title}\n\n{summary}",
                            'metadata': {
                                'source': 'MedlinePlus',
                                'condition': title,
                                'category': 'medical_condition',
                                'url': link,
                                'fetched_at': datetime.utcnow().isoformat()
                            }
                        })
                
                logger.info(f"Fetched {len(conditions)} MedlinePlus entries for: {condition}")
                return conditions
                
        except Exception as e:
            logger.error(f"Error fetching MedlinePlus info: {e}")
            return []
    
    # ==================== Batch Operations ====================
    
    async def fetch_comprehensive_knowledge(self) -> List[Dict[str, Any]]:
        """
        Fetch comprehensive medical knowledge from all sources
        This is the main function to populate the RAG knowledge base
        """
        all_documents = []
        
        try:
            # Fetch from multiple sources concurrently
            tasks = []
            
            # PubMed research articles (various topics)
            pubmed_queries = [
                "diabetes treatment guidelines",
                "hypertension management",
                "cardiovascular disease prevention",
                "cancer screening recommendations",
                "mental health disorders treatment",
                "infectious disease prevention",
                "nutrition and diet recommendations",
                "vaccine safety and efficacy"
            ]
            for query in pubmed_queries:
                tasks.append(self.fetch_pubmed_articles(query, max_results=10))
            
            # WHO and CDC guidelines
            tasks.append(self.fetch_who_guidelines())
            tasks.append(self.fetch_cdc_guidelines())
            
            # Drug information (common medications)
            common_drugs = [
                "metformin", "lisinopril", "amlodipine", "atorvastatin",
                "omeprazole", "levothyroxine", "metoprolol", "albuterol",
                "ibuprofen", "acetaminophen"
            ]
            for drug in common_drugs:
                tasks.append(self.fetch_drug_information(drug))
            
            # Medical conditions (MedlinePlus)
            conditions = [
                "diabetes", "hypertension", "asthma", "depression",
                "arthritis", "heart disease", "obesity", "anxiety"
            ]
            for condition in conditions:
                tasks.append(self.fetch_medlineplus_info(condition))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results
            for result in results:
                if isinstance(result, list):
                    all_documents.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Task failed: {result}")
            
            logger.info(f"Total documents fetched: {len(all_documents)}")
            return all_documents
            
        except Exception as e:
            logger.error(f"Error in comprehensive knowledge fetch: {e}")
            return all_documents


# Global singleton
_medical_fetcher: Optional[MedicalKnowledgeFetcher] = None


async def get_medical_fetcher() -> MedicalKnowledgeFetcher:
    """Get or create the global medical knowledge fetcher"""
    global _medical_fetcher
    if _medical_fetcher is None:
        _medical_fetcher = MedicalKnowledgeFetcher()
        await _medical_fetcher.initialize()
    return _medical_fetcher
