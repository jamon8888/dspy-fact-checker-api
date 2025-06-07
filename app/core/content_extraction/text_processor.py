"""
Advanced Text Processor

Comprehensive text processing, segmentation, and claim detection for fact-checking.
"""

import asyncio
import logging
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .models import (
    TextProcessingOptions, ProcessedTextContent, SegmentationStrategy,
    TextSegment, PotentialClaim, ContentStructure, LanguageInfo
)
from .exceptions import (
    TextProcessingError, LanguageDetectionError, ClaimDetectionError
)

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: python -m spacy download en_core_web_sm")

try:
    from textstat import flesch_reading_ease, flesch_kincaid_grade
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    logger.warning("textstat not available. Install with: pip install textstat")

try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available. Install with: pip install langdetect")


class TextCleaner:
    """Text cleaning and normalization utilities."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Clean up spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        return text.strip()
    
    @staticmethod
    def remove_boilerplate(text: str) -> str:
        """Remove common boilerplate text."""
        # Common boilerplate patterns
        boilerplate_patterns = [
            r'cookie policy.*?(?=\n|$)',
            r'privacy policy.*?(?=\n|$)',
            r'terms of service.*?(?=\n|$)',
            r'subscribe to.*?newsletter.*?(?=\n|$)',
            r'follow us on.*?(?=\n|$)',
            r'share this article.*?(?=\n|$)',
            r'advertisement.*?(?=\n|$)',
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and not sentence.isupper():
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences


class LanguageDetector:
    """Language detection utilities."""
    
    @staticmethod
    async def detect_language(text: str) -> Optional[LanguageInfo]:
        """Detect language of text content."""
        try:
            if LANGDETECT_AVAILABLE:
                # Use first 1000 characters for detection
                sample = text[:1000]
                detected = detect(sample)
                langs = detect_langs(sample)
                
                return LanguageInfo(
                    language=detected,
                    confidence=langs[0].prob if langs else 0.5,
                    detected_languages=[
                        {lang.lang: lang.prob} for lang in langs[:3]
                    ]
                )
            else:
                # Fallback to simple heuristics
                return LanguageInfo(
                    language='en',  # Default to English
                    confidence=0.5,
                    detected_languages=[{'en': 0.5}]
                )
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return LanguageInfo(
                language='en',
                confidence=0.3,
                detected_languages=[{'en': 0.3}]
            )


class StructureAnalyzer:
    """Text structure analysis utilities."""
    
    @staticmethod
    def analyze_structure(text: str) -> ContentStructure:
        """Analyze text structure and complexity."""
        # Count structural elements
        paragraphs = text.split('\n\n')
        paragraph_count = len([p for p in paragraphs if len(p.strip()) > 50])
        
        # Estimate headings (lines that are short and followed by longer content)
        lines = text.split('\n')
        heading_count = 0
        for i, line in enumerate(lines[:-1]):
            if (10 <= len(line.strip()) <= 80 and 
                not line.strip().endswith('.') and
                i + 1 < len(lines) and len(lines[i + 1].strip()) > 100):
                heading_count += 1
        
        # Count lists (lines starting with bullets or numbers)
        list_count = len(re.findall(r'^\s*[•\-\*\d+\.]\s+', text, re.MULTILINE))
        
        # Estimate tables (lines with multiple tabs or pipes)
        table_count = len(re.findall(r'^.*\|.*\|.*$', text, re.MULTILINE))
        
        # Calculate reading time (average 200 words per minute)
        word_count = len(text.split())
        reading_time = word_count / 200.0
        
        # Calculate complexity score
        complexity_score = StructureAnalyzer._calculate_complexity(text)
        
        return ContentStructure(
            has_title=heading_count > 0,
            has_headings=heading_count > 1,
            has_paragraphs=paragraph_count > 1,
            has_lists=list_count > 0,
            has_tables=table_count > 0,
            heading_count=heading_count,
            paragraph_count=paragraph_count,
            list_count=list_count,
            table_count=table_count,
            estimated_reading_time=reading_time,
            complexity_score=complexity_score
        )
    
    @staticmethod
    def _calculate_complexity(text: str) -> float:
        """Calculate text complexity score (0.0 to 1.0)."""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Sentence length variety
        sentences = TextCleaner.extract_sentences(text)
        if sentences:
            lengths = [len(s.split()) for s in sentences]
            avg_length = sum(lengths) / len(lengths)
            
            if 10 <= avg_length <= 20:
                score += 0.3
            elif 5 <= avg_length < 10 or 20 < avg_length <= 30:
                score += 0.2
            
            # Length variance
            if len(set(lengths)) > len(lengths) * 0.5:
                score += 0.2
        
        # Vocabulary complexity
        words = text.lower().split()
        unique_words = set(words)
        if words:
            vocabulary_ratio = len(unique_words) / len(words)
            score += min(vocabulary_ratio * 0.5, 0.3)
        
        # Punctuation variety
        punct_types = set(re.findall(r'[.!?;:,]', text))
        score += min(len(punct_types) * 0.05, 0.2)
        
        return min(score, 1.0)


class ClaimDetector:
    """Factual claim detection utilities."""
    
    def __init__(self):
        self.factual_indicators = [
            r'\b(?:according to|research shows|studies indicate|data reveals)\b',
            r'\b(?:statistics show|evidence suggests|findings indicate)\b',
            r'\b(?:experts say|scientists believe|researchers found)\b',
            r'\b(?:\d+(?:\.\d+)?%|\d+(?:,\d{3})*(?:\.\d+)?)\b',  # Numbers and percentages
            r'\b(?:in \d{4}|since \d{4}|by \d{4})\b',  # Years
            r'\b(?:increased by|decreased by|rose to|fell to)\b',
            r'\b(?:compared to|versus|vs\.?|relative to)\b'
        ]
        
        self.claim_patterns = [
            r'[A-Z][^.!?]*(?:is|are|was|were|will be|has been|have been)[^.!?]*[.!?]',
            r'[A-Z][^.!?]*(?:shows?|proves?|demonstrates?|indicates?)[^.!?]*[.!?]',
            r'[A-Z][^.!?]*(?:\d+(?:\.\d+)?%|\d+(?:,\d{3})*(?:\.\d+)?)[^.!?]*[.!?]'
        ]
    
    async def detect_claims(
        self, 
        text: str, 
        confidence_threshold: float = 0.5
    ) -> List[PotentialClaim]:
        """Detect potential factual claims in text."""
        claims = []
        
        try:
            sentences = TextCleaner.extract_sentences(text)
            
            for sentence in sentences:
                confidence = self._calculate_claim_confidence(sentence)
                
                if confidence >= confidence_threshold:
                    # Find position in original text
                    start_pos = text.find(sentence)
                    if start_pos == -1:
                        continue
                    
                    end_pos = start_pos + len(sentence)
                    
                    # Extract keywords and entities
                    keywords = self._extract_keywords(sentence)
                    entities = self._extract_entities(sentence)
                    
                    claim = PotentialClaim(
                        text=sentence,
                        start_position=start_pos,
                        end_position=end_pos,
                        confidence=confidence,
                        claim_type="factual",
                        context=self._get_context(text, start_pos, end_pos),
                        keywords=keywords,
                        entities=entities
                    )
                    
                    claims.append(claim)
            
            return claims
            
        except Exception as e:
            raise ClaimDetectionError(f"Claim detection failed: {str(e)}")
    
    def _calculate_claim_confidence(self, sentence: str) -> float:
        """Calculate confidence that sentence contains a factual claim."""
        confidence = 0.0
        
        # Check for factual indicators
        for pattern in self.factual_indicators:
            if re.search(pattern, sentence, re.IGNORECASE):
                confidence += 0.3
        
        # Check for claim patterns
        for pattern in self.claim_patterns:
            if re.search(pattern, sentence):
                confidence += 0.2
        
        # Check for numbers/statistics
        if re.search(r'\b\d+(?:\.\d+)?%\b', sentence):
            confidence += 0.3
        
        if re.search(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', sentence):
            confidence += 0.2
        
        # Check for temporal references
        if re.search(r'\b(?:in|since|by|during) \d{4}\b', sentence):
            confidence += 0.2
        
        # Check for comparative language
        if re.search(r'\b(?:more|less|higher|lower|increased|decreased)\b', sentence, re.IGNORECASE):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter common words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'must', 'shall'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        return list(set(keywords))[:10]  # Return unique keywords, max 10
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        # Simple entity extraction using patterns
        entities = []
        
        # Proper nouns (capitalized words)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(proper_nouns)
        
        # Organizations (words ending in common org suffixes)
        orgs = re.findall(r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*(?:\s+(?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University|College))\b', text)
        entities.extend(orgs)
        
        return list(set(entities))[:5]  # Return unique entities, max 5
    
    def _get_context(self, text: str, start_pos: int, end_pos: int, context_chars: int = 200) -> str:
        """Get context around a text segment."""
        context_start = max(0, start_pos - context_chars)
        context_end = min(len(text), end_pos + context_chars)
        
        context = text[context_start:context_end]
        
        # Clean up context boundaries
        if context_start > 0:
            context = '...' + context
        if context_end < len(text):
            context = context + '...'
        
        return context


class TextSegmenter:
    """Text segmentation utilities."""

    @staticmethod
    async def segment_text(
        text: str,
        strategy: SegmentationStrategy,
        min_length: int = 50,
        max_length: int = 5000
    ) -> List[TextSegment]:
        """Segment text according to specified strategy."""
        segments = []

        try:
            if strategy == SegmentationStrategy.PARAGRAPH:
                segments = TextSegmenter._segment_by_paragraphs(text, min_length, max_length)
            elif strategy == SegmentationStrategy.SENTENCE:
                segments = TextSegmenter._segment_by_sentences(text, min_length, max_length)
            elif strategy == SegmentationStrategy.SEMANTIC:
                segments = await TextSegmenter._segment_by_semantics(text, min_length, max_length)
            elif strategy == SegmentationStrategy.TOPIC:
                segments = await TextSegmenter._segment_by_topics(text, min_length, max_length)
            elif strategy == SegmentationStrategy.CLAIM_BASED:
                segments = await TextSegmenter._segment_by_claims(text, min_length, max_length)
            else:
                segments = TextSegmenter._segment_by_paragraphs(text, min_length, max_length)

            return segments

        except Exception as e:
            logger.error(f"Text segmentation failed: {e}")
            # Fallback to simple paragraph segmentation
            return TextSegmenter._segment_by_paragraphs(text, min_length, max_length)

    @staticmethod
    def _segment_by_paragraphs(text: str, min_length: int, max_length: int) -> List[TextSegment]:
        """Segment text by paragraphs."""
        segments = []
        paragraphs = text.split('\n\n')

        current_pos = 0
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) >= min_length:
                # Split long paragraphs
                if len(paragraph) > max_length:
                    sub_segments = TextSegmenter._split_long_text(paragraph, max_length)
                    for sub_text in sub_segments:
                        if len(sub_text) >= min_length:
                            start_pos = text.find(sub_text, current_pos)
                            if start_pos != -1:
                                segments.append(TextSegment(
                                    text=sub_text,
                                    start_position=start_pos,
                                    end_position=start_pos + len(sub_text),
                                    segment_type="paragraph_split",
                                    confidence=0.8
                                ))
                else:
                    start_pos = text.find(paragraph, current_pos)
                    if start_pos != -1:
                        segments.append(TextSegment(
                            text=paragraph,
                            start_position=start_pos,
                            end_position=start_pos + len(paragraph),
                            segment_type="paragraph",
                            confidence=1.0
                        ))

                current_pos = text.find(paragraph, current_pos) + len(paragraph)

        return segments

    @staticmethod
    def _segment_by_sentences(text: str, min_length: int, max_length: int) -> List[TextSegment]:
        """Segment text by sentences, grouping to meet length requirements."""
        segments = []
        sentences = TextCleaner.extract_sentences(text)

        current_segment = ""
        current_start = 0

        for sentence in sentences:
            if not current_segment:
                current_segment = sentence
                current_start = text.find(sentence)
            else:
                test_segment = current_segment + " " + sentence
                if len(test_segment) <= max_length:
                    current_segment = test_segment
                else:
                    # Finalize current segment
                    if len(current_segment) >= min_length:
                        segments.append(TextSegment(
                            text=current_segment,
                            start_position=current_start,
                            end_position=current_start + len(current_segment),
                            segment_type="sentence_group",
                            confidence=0.9
                        ))

                    # Start new segment
                    current_segment = sentence
                    current_start = text.find(sentence, current_start + len(current_segment))

        # Add final segment
        if current_segment and len(current_segment) >= min_length:
            segments.append(TextSegment(
                text=current_segment,
                start_position=current_start,
                end_position=current_start + len(current_segment),
                segment_type="sentence_group",
                confidence=0.9
            ))

        return segments

    @staticmethod
    async def _segment_by_semantics(text: str, min_length: int, max_length: int) -> List[TextSegment]:
        """Segment text by semantic coherence (simplified implementation)."""
        # For now, use paragraph-based segmentation with semantic hints
        # In a full implementation, this would use NLP models for semantic similarity
        return TextSegmenter._segment_by_paragraphs(text, min_length, max_length)

    @staticmethod
    async def _segment_by_topics(text: str, min_length: int, max_length: int) -> List[TextSegment]:
        """Segment text by topic boundaries (simplified implementation)."""
        # For now, use paragraph-based segmentation
        # In a full implementation, this would use topic modeling
        return TextSegmenter._segment_by_paragraphs(text, min_length, max_length)

    @staticmethod
    async def _segment_by_claims(text: str, min_length: int, max_length: int) -> List[TextSegment]:
        """Segment text around factual claims."""
        claim_detector = ClaimDetector()
        claims = await claim_detector.detect_claims(text, confidence_threshold=0.3)

        if not claims:
            return TextSegmenter._segment_by_paragraphs(text, min_length, max_length)

        segments = []
        last_end = 0

        for claim in claims:
            # Create segment around each claim with context
            context_start = max(last_end, claim.start_position - 200)
            context_end = min(len(text), claim.end_position + 200)

            # Adjust to sentence boundaries
            context_start = TextSegmenter._find_sentence_start(text, context_start)
            context_end = TextSegmenter._find_sentence_end(text, context_end)

            segment_text = text[context_start:context_end].strip()

            if len(segment_text) >= min_length and context_start >= last_end:
                segments.append(TextSegment(
                    text=segment_text,
                    start_position=context_start,
                    end_position=context_end,
                    segment_type="claim_context",
                    confidence=claim.confidence,
                    metadata={
                        "claim_text": claim.text,
                        "claim_confidence": claim.confidence
                    }
                ))
                last_end = context_end

        return segments

    @staticmethod
    def _split_long_text(text: str, max_length: int) -> List[str]:
        """Split long text into smaller chunks."""
        if len(text) <= max_length:
            return [text]

        chunks = []
        sentences = TextCleaner.extract_sentences(text)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + " " + sentence) <= max_length:
                current_chunk = current_chunk + " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    @staticmethod
    def _find_sentence_start(text: str, pos: int) -> int:
        """Find the start of the sentence containing position."""
        while pos > 0 and text[pos-1] not in '.!?':
            pos -= 1
        return pos

    @staticmethod
    def _find_sentence_end(text: str, pos: int) -> int:
        """Find the end of the sentence containing position."""
        while pos < len(text) and text[pos] not in '.!?':
            pos += 1
        return min(pos + 1, len(text))


class AdvancedTextProcessor:
    """Advanced text processor with comprehensive analysis capabilities."""

    def __init__(self):
        self.text_cleaner = TextCleaner()
        self.language_detector = LanguageDetector()
        self.structure_analyzer = StructureAnalyzer()
        self.claim_detector = ClaimDetector()
        self.text_segmenter = TextSegmenter()

        logger.info("AdvancedTextProcessor initialized")

    async def process_text(
        self,
        text: str,
        options: Optional[TextProcessingOptions] = None
    ) -> ProcessedTextContent:
        """
        Process text with comprehensive analysis.

        Args:
            text: Input text to process
            options: Processing options

        Returns:
            ProcessedTextContent with analysis results
        """
        if options is None:
            options = TextProcessingOptions()

        start_time = time.time()

        try:
            # Validate input
            if not text or len(text.strip()) < 10:
                raise TextProcessingError("Text too short for processing", text_length=len(text))

            # Clean text
            original_text = text
            cleaned_text = self.text_cleaner.clean_text(text)
            cleaned_text = self.text_cleaner.remove_boilerplate(cleaned_text)

            if len(cleaned_text) < 10:
                raise TextProcessingError("Text too short after cleaning", text_length=len(cleaned_text))

            # Language detection
            language_info = None
            if options.detect_language:
                try:
                    language_info = await self.language_detector.detect_language(cleaned_text)
                except Exception as e:
                    logger.warning(f"Language detection failed: {e}")

            # Structure analysis
            structure = ContentStructure()
            if options.analyze_structure:
                try:
                    structure = self.structure_analyzer.analyze_structure(cleaned_text)
                except Exception as e:
                    logger.warning(f"Structure analysis failed: {e}")

            # Text segmentation
            segments = []
            try:
                segments = await self.text_segmenter.segment_text(
                    cleaned_text,
                    options.segmentation_strategy,
                    options.min_segment_length,
                    options.max_segment_length
                )
            except Exception as e:
                logger.warning(f"Text segmentation failed: {e}")
                # Fallback to simple paragraph segmentation
                segments = await self.text_segmenter.segment_text(
                    cleaned_text,
                    SegmentationStrategy.PARAGRAPH,
                    options.min_segment_length,
                    options.max_segment_length
                )

            # Claim detection
            potential_claims = []
            if options.detect_claims:
                try:
                    potential_claims = await self.claim_detector.detect_claims(
                        cleaned_text,
                        options.claim_confidence_threshold
                    )
                except Exception as e:
                    logger.warning(f"Claim detection failed: {e}")

            # Compile processing metadata
            processing_time = time.time() - start_time
            processing_metadata = {
                "original_length": len(original_text),
                "cleaned_length": len(cleaned_text),
                "reduction_ratio": 1 - (len(cleaned_text) / len(original_text)) if original_text else 0,
                "processing_options": options.dict(),
                "segments_count": len(segments),
                "claims_count": len(potential_claims),
                "language_detected": language_info.language if language_info else None,
                "language_confidence": language_info.confidence if language_info else None
            }

            # Add statistics if requested
            if options.include_statistics:
                processing_metadata.update(self._calculate_statistics(cleaned_text))

            # Create result
            result = ProcessedTextContent(
                original_text=original_text,
                cleaned_text=cleaned_text,
                language=language_info,
                structure=structure,
                segments=segments,
                potential_claims=potential_claims,
                processing_metadata=processing_metadata,
                processing_time=processing_time
            )

            logger.info(f"Text processing completed successfully in {processing_time:.2f}s "
                       f"({len(segments)} segments, {len(potential_claims)} claims)")

            return result

        except Exception as e:
            if isinstance(e, TextProcessingError):
                raise
            else:
                raise TextProcessingError(f"Unexpected error during text processing: {str(e)}")

    def _calculate_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate text statistics."""
        words = text.split()
        sentences = TextCleaner.extract_sentences(text)

        stats = {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(text.split('\n\n')),
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "average_sentence_length": len(words) / len(sentences) if sentences else 0,
            "unique_words": len(set(word.lower() for word in words)),
            "vocabulary_richness": len(set(word.lower() for word in words)) / len(words) if words else 0
        }

        # Add readability scores if available
        if TEXTSTAT_AVAILABLE:
            try:
                stats["flesch_reading_ease"] = flesch_reading_ease(text)
                stats["flesch_kincaid_grade"] = flesch_kincaid_grade(text)
            except Exception as e:
                logger.warning(f"Readability calculation failed: {e}")

        return stats

    async def extract_key_information(self, text: str) -> Dict[str, Any]:
        """Extract key information from text for fact-checking."""
        try:
            # Process text with claim detection
            options = TextProcessingOptions(
                detect_claims=True,
                claim_confidence_threshold=0.3,
                segmentation_strategy=SegmentationStrategy.CLAIM_BASED
            )

            processed = await self.process_text(text, options)

            # Extract high-confidence claims
            high_confidence_claims = [
                claim for claim in processed.potential_claims
                if claim.confidence >= 0.7
            ]

            # Extract entities and keywords from claims
            all_keywords = set()
            all_entities = set()

            for claim in processed.potential_claims:
                all_keywords.update(claim.keywords)
                all_entities.update(claim.entities)

            return {
                "total_claims": len(processed.potential_claims),
                "high_confidence_claims": len(high_confidence_claims),
                "claims": [claim.dict() for claim in high_confidence_claims[:10]],  # Top 10
                "keywords": list(all_keywords)[:20],  # Top 20
                "entities": list(all_entities)[:15],  # Top 15
                "language": processed.language.language if processed.language else "unknown",
                "complexity_score": processed.structure.complexity_score,
                "estimated_reading_time": processed.structure.estimated_reading_time
            }

        except Exception as e:
            logger.error(f"Key information extraction failed: {e}")
            return {
                "total_claims": 0,
                "high_confidence_claims": 0,
                "claims": [],
                "keywords": [],
                "entities": [],
                "language": "unknown",
                "complexity_score": 0.0,
                "estimated_reading_time": 0.0,
                "error": str(e)
            }

    def get_processing_capabilities(self) -> Dict[str, Any]:
        """Get information about available processing capabilities."""
        return {
            "segmentation_strategies": [strategy.value for strategy in SegmentationStrategy],
            "language_detection_available": LANGDETECT_AVAILABLE,
            "spacy_available": SPACY_AVAILABLE,
            "textstat_available": TEXTSTAT_AVAILABLE,
            "claim_detection": True,
            "structure_analysis": True,
            "text_cleaning": True,
            "supported_languages": ["en", "es", "fr", "de", "it", "pt", "nl", "auto"],
            "max_text_length": 1000000,  # 1MB
            "min_segment_length": 10,
            "max_segment_length": 10000
        }
