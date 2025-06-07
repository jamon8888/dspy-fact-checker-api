"""
URL Content Extractor

Advanced URL content extraction with multiple strategies and quality assessment.
"""

import asyncio
import logging
import re
import time
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse, urljoin
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .models import (
    ExtractionOptions, ExtractedWebContent, ExtractionStrategy, 
    ContentType, URLAnalysis, LanguageInfo
)
from .exceptions import (
    URLExtractionError, ExtractionTimeoutError, 
    UnsupportedContentTypeError, ContentQualityError
)

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logger.warning("newspaper3k not available. Install with: pip install newspaper3k")

try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False
    logger.warning("readability-lxml not available. Install with: pip install readability-lxml")

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logger.warning("trafilatura not available. Install with: pip install trafilatura")


class BaseExtractor:
    """Base class for content extractors."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def extract(self, url: str, options: ExtractionOptions) -> Dict[str, Any]:
        """Extract content from URL."""
        raise NotImplementedError
    
    def _assess_quality(self, content: Dict[str, Any]) -> float:
        """Assess content quality (0.0 to 1.0)."""
        if not content.get('text'):
            return 0.0
        
        text = content['text']
        score = 0.0
        
        # Length score (optimal around 500-5000 chars)
        length = len(text)
        if 500 <= length <= 5000:
            score += 0.3
        elif 200 <= length < 500 or 5000 < length <= 10000:
            score += 0.2
        elif 100 <= length < 200:
            score += 0.1
        
        # Title presence
        if content.get('title') and len(content['title']) > 10:
            score += 0.2
        
        # Structure indicators
        if '\n\n' in text:  # Paragraph breaks
            score += 0.1
        if any(word in text.lower() for word in ['the', 'and', 'that', 'with']):
            score += 0.1
        
        # Sentence structure
        sentences = text.split('.')
        if 3 <= len(sentences) <= 100:
            score += 0.2
        
        # Author/date presence
        if content.get('author'):
            score += 0.1
        if content.get('publish_date'):
            score += 0.1
        
        return min(score, 1.0)


class NewspaperExtractor(BaseExtractor):
    """Newspaper3k-based content extractor."""
    
    def __init__(self):
        super().__init__("newspaper")
        self.available = NEWSPAPER_AVAILABLE
    
    async def extract(self, url: str, options: ExtractionOptions) -> Dict[str, Any]:
        """Extract content using newspaper3k."""
        if not self.available:
            raise URLExtractionError("Newspaper3k not available", url=url)
        
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                'text': article.text,
                'title': article.title,
                'author': ', '.join(article.authors) if article.authors else None,
                'publish_date': article.publish_date,
                'summary': article.summary if hasattr(article, 'summary') else None,
                'images': list(article.images) if options.include_images else [],
                'metadata': {
                    'top_image': article.top_image,
                    'meta_keywords': article.meta_keywords,
                    'meta_description': article.meta_description
                }
            }
        except Exception as e:
            raise URLExtractionError(f"Newspaper extraction failed: {str(e)}", url=url)


class ReadabilityExtractor(BaseExtractor):
    """Readability-based content extractor."""
    
    def __init__(self):
        super().__init__("readability")
        self.available = READABILITY_AVAILABLE
    
    async def extract(self, url: str, options: ExtractionOptions) -> Dict[str, Any]:
        """Extract content using readability."""
        if not self.available:
            raise URLExtractionError("Readability not available", url=url)
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=options.timeout_seconds)
            ) as session:
                async with session.get(url) as response:
                    html = await response.text()
            
            doc = Document(html)
            soup = BeautifulSoup(doc.content(), 'html.parser')
            
            # Extract text
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            
            return {
                'text': text,
                'title': doc.title(),
                'author': None,
                'publish_date': None,
                'summary': doc.summary(),
                'images': [],
                'metadata': {
                    'readability_score': getattr(doc, 'score', 0)
                }
            }
        except Exception as e:
            raise URLExtractionError(f"Readability extraction failed: {str(e)}", url=url)


class TrafilaturaExtractor(BaseExtractor):
    """Trafilatura-based content extractor."""
    
    def __init__(self):
        super().__init__("trafilatura")
        self.available = TRAFILATURA_AVAILABLE
    
    async def extract(self, url: str, options: ExtractionOptions) -> Dict[str, Any]:
        """Extract content using trafilatura."""
        if not self.available:
            raise URLExtractionError("Trafilatura not available", url=url)
        
        try:
            # Download content
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise URLExtractionError("Failed to download content", url=url)
            
            # Extract content
            text = trafilatura.extract(downloaded, include_comments=False)
            metadata = trafilatura.extract_metadata(downloaded)
            
            return {
                'text': text or '',
                'title': metadata.title if metadata else None,
                'author': metadata.author if metadata else None,
                'publish_date': metadata.date if metadata else None,
                'summary': None,
                'images': [],
                'metadata': {
                    'sitename': metadata.sitename if metadata else None,
                    'description': metadata.description if metadata else None
                }
            }
        except Exception as e:
            raise URLExtractionError(f"Trafilatura extraction failed: {str(e)}", url=url)


class CustomExtractor(BaseExtractor):
    """Custom BeautifulSoup-based content extractor."""
    
    def __init__(self):
        super().__init__("custom")
        self.available = True
    
    async def extract(self, url: str, options: ExtractionOptions) -> Dict[str, Any]:
        """Extract content using custom BeautifulSoup logic."""
        try:
            headers = options.headers or {}
            if options.user_agent:
                headers['User-Agent'] = options.user_agent
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=options.timeout_seconds)
            ) as session:
                async with session.get(
                    url, 
                    headers=headers,
                    allow_redirects=options.follow_redirects,
                    ssl=options.verify_ssl
                ) as response:
                    if response.status >= 400:
                        raise URLExtractionError(
                            f"HTTP {response.status}: {response.reason}",
                            url=url,
                            status_code=response.status
                        )
                    
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Extract title
            title = None
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content
            content_selectors = [
                'article', '[role="main"]', 'main', '.content', '#content',
                '.post-content', '.entry-content', '.article-content'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                content_element = soup.find('body') or soup
            
            # Extract text
            text = content_element.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Extract metadata
            author = self._extract_author(soup)
            publish_date = self._extract_date(soup)
            
            return {
                'text': text,
                'title': title,
                'author': author,
                'publish_date': publish_date,
                'summary': None,
                'images': self._extract_images(soup, url) if options.include_images else [],
                'metadata': self._extract_metadata(soup)
            }
            
        except aiohttp.ClientError as e:
            raise URLExtractionError(f"Network error: {str(e)}", url=url)
        except Exception as e:
            raise URLExtractionError(f"Custom extraction failed: {str(e)}", url=url)
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from HTML."""
        author_selectors = [
            '[rel="author"]', '.author', '.byline', '[itemprop="author"]',
            'meta[name="author"]', 'meta[property="article:author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content')
                else:
                    return element.get_text().strip()
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publish date from HTML."""
        date_selectors = [
            'time[datetime]', '[itemprop="datePublished"]',
            'meta[property="article:published_time"]',
            'meta[name="date"]', '.date', '.published'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_str = element.get('datetime') or element.get('content') or element.get_text()
                if date_str:
                    try:
                        # Try to parse common date formats
                        from dateutil import parser
                        return parser.parse(date_str)
                    except:
                        continue
        return None
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from HTML."""
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith('http'):
                images.append(src)
            else:
                images.append(urljoin(base_url, src))
        return images[:10]  # Limit to 10 images
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        return metadata


class URLContentExtractor:
    """Advanced URL content extractor with multiple strategies."""

    def __init__(self):
        self.extractors = {
            ExtractionStrategy.NEWSPAPER: NewspaperExtractor(),
            ExtractionStrategy.READABILITY: ReadabilityExtractor(),
            ExtractionStrategy.TRAFILATURA: TrafilaturaExtractor(),
            ExtractionStrategy.CUSTOM: CustomExtractor()
        }

        # Determine available extractors
        self.available_extractors = [
            strategy for strategy, extractor in self.extractors.items()
            if extractor.available
        ]

        logger.info(f"Available extractors: {[e.value for e in self.available_extractors]}")

    async def extract_content(
        self,
        url: str,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractedWebContent:
        """
        Extract content from URL using the best available strategy.

        Args:
            url: URL to extract content from
            options: Extraction options

        Returns:
            ExtractedWebContent with extracted content and metadata
        """
        if options is None:
            options = ExtractionOptions()

        start_time = time.time()

        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise URLExtractionError("Invalid URL format", url=url)

            # Analyze URL
            url_analysis = await self._analyze_url(url)

            # Determine extraction strategy
            strategy = self._select_strategy(options.strategy, url_analysis)

            # Extract content
            extracted_data = await self._extract_with_strategy(url, strategy, options)

            # Assess quality
            quality_score = self.extractors[strategy]._assess_quality(extracted_data)

            if quality_score < options.quality_threshold:
                # Try fallback strategies
                for fallback_strategy in self.available_extractors:
                    if fallback_strategy != strategy:
                        try:
                            fallback_data = await self._extract_with_strategy(
                                url, fallback_strategy, options
                            )
                            fallback_quality = self.extractors[fallback_strategy]._assess_quality(fallback_data)

                            if fallback_quality > quality_score:
                                extracted_data = fallback_data
                                quality_score = fallback_quality
                                strategy = fallback_strategy
                                break
                        except Exception as e:
                            logger.warning(f"Fallback strategy {fallback_strategy} failed: {e}")
                            continue

            # Final quality check
            if quality_score < options.quality_threshold:
                raise ContentQualityError(
                    f"Content quality ({quality_score:.2f}) below threshold ({options.quality_threshold})",
                    quality_score=quality_score,
                    min_threshold=options.quality_threshold
                )

            # Detect language if requested
            language_info = None
            if options.include_metadata and extracted_data.get('text'):
                language_info = await self._detect_language(extracted_data['text'])

            # Create result
            processing_time = time.time() - start_time

            result = ExtractedWebContent(
                url=url,
                title=extracted_data.get('title'),
                content=extracted_data.get('text', ''),
                author=extracted_data.get('author'),
                publish_date=extracted_data.get('publish_date'),
                extraction_method=strategy,
                content_type=url_analysis.content_type,
                quality_score=quality_score,
                language=language_info,
                metadata={
                    **extracted_data.get('metadata', {}),
                    'url_analysis': url_analysis.dict(),
                    'extraction_attempts': 1,  # Could be more with fallbacks
                },
                images=extracted_data.get('images', []),
                links=extracted_data.get('links', []),
                processing_time=processing_time
            )

            logger.info(f"Successfully extracted content from {url} using {strategy.value} "
                       f"(quality: {quality_score:.2f}, time: {processing_time:.2f}s)")

            return result

        except asyncio.TimeoutError:
            raise ExtractionTimeoutError(
                f"Content extraction timed out after {options.timeout_seconds}s",
                url=url,
                timeout_seconds=options.timeout_seconds
            )
        except Exception as e:
            if isinstance(e, (URLExtractionError, ContentQualityError)):
                raise
            else:
                raise URLExtractionError(f"Unexpected error during extraction: {str(e)}", url=url)

    async def _extract_with_strategy(
        self,
        url: str,
        strategy: ExtractionStrategy,
        options: ExtractionOptions
    ) -> Dict[str, Any]:
        """Extract content using specific strategy."""
        extractor = self.extractors[strategy]
        if not extractor.available:
            raise URLExtractionError(f"Extractor {strategy.value} not available", url=url)

        return await asyncio.wait_for(
            extractor.extract(url, options),
            timeout=options.timeout_seconds
        )

    def _select_strategy(
        self,
        requested_strategy: ExtractionStrategy,
        url_analysis: URLAnalysis
    ) -> ExtractionStrategy:
        """Select the best extraction strategy."""
        if requested_strategy != ExtractionStrategy.AUTO:
            if requested_strategy in self.available_extractors:
                return requested_strategy
            else:
                logger.warning(f"Requested strategy {requested_strategy.value} not available, using auto")

        # Auto-select based on content type and available extractors
        if url_analysis.content_type == ContentType.NEWS_ARTICLE:
            if ExtractionStrategy.NEWSPAPER in self.available_extractors:
                return ExtractionStrategy.NEWSPAPER

        if url_analysis.content_type in [ContentType.BLOG_POST, ContentType.ACADEMIC_PAPER]:
            if ExtractionStrategy.TRAFILATURA in self.available_extractors:
                return ExtractionStrategy.TRAFILATURA

        # Default fallback order
        for strategy in [ExtractionStrategy.TRAFILATURA, ExtractionStrategy.NEWSPAPER,
                        ExtractionStrategy.READABILITY, ExtractionStrategy.CUSTOM]:
            if strategy in self.available_extractors:
                return strategy

        raise URLExtractionError("No extraction strategies available")

    async def _analyze_url(self, url: str) -> URLAnalysis:
        """Analyze URL to determine content type and characteristics."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Determine content type based on domain patterns
        content_type = ContentType.GENERAL
        is_news_site = False
        is_academic = False
        is_social_media = False
        trust_score = 0.5

        # News sites
        news_indicators = ['news', 'cnn', 'bbc', 'reuters', 'ap', 'nytimes', 'guardian', 'wsj']
        if any(indicator in domain for indicator in news_indicators):
            content_type = ContentType.NEWS_ARTICLE
            is_news_site = True
            trust_score = 0.8

        # Academic sites
        academic_indicators = ['.edu', 'arxiv', 'scholar', 'pubmed', 'jstor', 'springer']
        if any(indicator in domain for indicator in academic_indicators):
            content_type = ContentType.ACADEMIC_PAPER
            is_academic = True
            trust_score = 0.9

        # Wikipedia
        if 'wikipedia.org' in domain:
            content_type = ContentType.WIKIPEDIA
            trust_score = 0.8

        # Social media
        social_indicators = ['twitter', 'facebook', 'instagram', 'linkedin', 'reddit']
        if any(indicator in domain for indicator in social_indicators):
            content_type = ContentType.SOCIAL_MEDIA
            is_social_media = True
            trust_score = 0.3

        # Blog indicators
        blog_indicators = ['blog', 'medium.com', 'substack', 'wordpress']
        if any(indicator in domain for indicator in blog_indicators):
            content_type = ContentType.BLOG_POST
            trust_score = 0.6

        return URLAnalysis(
            url=url,
            domain=domain,
            content_type=content_type,
            is_news_site=is_news_site,
            is_academic=is_academic,
            is_social_media=is_social_media,
            trust_score=trust_score,
            metadata={
                'path': parsed.path,
                'query': parsed.query,
                'fragment': parsed.fragment
            }
        )

    async def _detect_language(self, text: str) -> Optional[LanguageInfo]:
        """Detect language of text content."""
        try:
            # Try langdetect first
            try:
                from langdetect import detect, detect_langs
                detected = detect(text[:1000])  # Use first 1000 chars
                langs = detect_langs(text[:1000])

                return LanguageInfo(
                    language=detected,
                    confidence=langs[0].prob if langs else 0.5,
                    detected_languages=[
                        {lang.lang: lang.prob} for lang in langs[:3]
                    ]
                )
            except ImportError:
                logger.warning("langdetect not available for language detection")

            # Fallback to simple heuristics
            return LanguageInfo(
                language='en',  # Default to English
                confidence=0.5,
                detected_languages=[{'en': 0.5}]
            )

        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None

    def get_available_strategies(self) -> List[ExtractionStrategy]:
        """Get list of available extraction strategies."""
        return self.available_extractors.copy()

    def is_strategy_available(self, strategy: ExtractionStrategy) -> bool:
        """Check if a specific extraction strategy is available."""
        return strategy in self.available_extractors
