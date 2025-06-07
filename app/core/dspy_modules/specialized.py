"""
Specialized modules for document-type specific fact-checking.

This module contains specialized fact-checking modules that extend the base
functionality for specific document types like academic papers, news articles,
and legal documents.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from .data_models import DocumentClaim, Evidence, ClaimVerificationResult

logger = logging.getLogger(__name__)


class SpecializedModule(ABC):
    """Base class for specialized fact-checking modules."""
    
    def __init__(self, module_name: str):
        """Initialize the specialized module."""
        self.module_name = module_name
        self.logger = logging.getLogger(__name__ + f".{module_name}")
    
    @abstractmethod
    def analyze(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Perform specialized analysis on the document and verification results."""
        pass


class AcademicCitationVerifier(SpecializedModule):
    """Specialized module for verifying academic citations and references."""
    
    def __init__(self):
        super().__init__("AcademicCitationVerifier")
    
    def analyze(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Analyze academic citations and reference quality."""
        try:
            # Extract citation patterns
            citations = self._extract_citations(document_content)
            
            # Verify citation formats
            citation_quality = self._assess_citation_quality(citations)
            
            # Check for citation-claim alignment
            citation_alignment = self._check_citation_alignment(citations, verification_results)
            
            return {
                "module": self.module_name,
                "total_citations": len(citations),
                "citation_quality_score": citation_quality,
                "citation_alignment_score": citation_alignment,
                "citation_issues": self._identify_citation_issues(citations),
                "recommendations": self._generate_citation_recommendations(citations, citation_quality)
            }
            
        except Exception as e:
            self.logger.error(f"Error in academic citation analysis: {e}")
            return {"module": self.module_name, "error": str(e)}
    
    def _extract_citations(self, document_content: str) -> List[Dict[str, Any]]:
        """Extract citations from academic document."""
        # Simplified citation extraction
        # In practice, this would use more sophisticated parsing
        citations = []
        
        # Look for common citation patterns
        import re
        
        # Pattern for author-year citations: (Author, Year)
        author_year_pattern = r'\(([A-Za-z\s,&]+),?\s*(\d{4})\)'
        matches = re.findall(author_year_pattern, document_content)
        
        for i, (author, year) in enumerate(matches):
            citations.append({
                "id": f"cite_{i}",
                "type": "author_year",
                "author": author.strip(),
                "year": int(year),
                "text": f"({author}, {year})"
            })
        
        return citations
    
    def _assess_citation_quality(self, citations: List[Dict[str, Any]]) -> float:
        """Assess the quality of citations."""
        if not citations:
            return 0.0
        
        quality_score = 0.0
        
        for citation in citations:
            # Check recency (higher score for more recent citations)
            current_year = datetime.now().year
            age = current_year - citation.get("year", current_year)
            recency_score = max(0.0, 1.0 - (age / 20))  # Decay over 20 years
            
            # Check author format
            author_score = 1.0 if citation.get("author") else 0.0
            
            # Combine scores
            citation_quality = (recency_score + author_score) / 2
            quality_score += citation_quality
        
        return quality_score / len(citations)
    
    def _check_citation_alignment(
        self,
        citations: List[Dict[str, Any]],
        verification_results: List[ClaimVerificationResult]
    ) -> float:
        """Check alignment between citations and verified claims."""
        if not citations or not verification_results:
            return 0.0
        
        # Simplified alignment check
        # In practice, this would involve more sophisticated matching
        aligned_claims = 0
        
        for result in verification_results:
            # Check if claim has supporting evidence that matches citations
            has_academic_evidence = any(
                evidence.evidence_type.value == "academic_paper"
                for evidence in result.supporting_evidence
            )
            if has_academic_evidence:
                aligned_claims += 1
        
        return aligned_claims / len(verification_results) if verification_results else 0.0
    
    def _identify_citation_issues(self, citations: List[Dict[str, Any]]) -> List[str]:
        """Identify potential issues with citations."""
        issues = []
        
        if not citations:
            issues.append("No citations found in academic document")
        
        # Check for old citations
        current_year = datetime.now().year
        old_citations = [c for c in citations if current_year - c.get("year", current_year) > 10]
        if len(old_citations) > len(citations) * 0.5:
            issues.append("More than 50% of citations are older than 10 years")
        
        # Check for missing author information
        missing_authors = [c for c in citations if not c.get("author")]
        if missing_authors:
            issues.append(f"{len(missing_authors)} citations missing author information")
        
        return issues
    
    def _generate_citation_recommendations(
        self,
        citations: List[Dict[str, Any]],
        quality_score: float
    ) -> List[str]:
        """Generate recommendations for improving citations."""
        recommendations = []
        
        if quality_score < 0.5:
            recommendations.append("Consider updating citations with more recent sources")
        
        if not citations:
            recommendations.append("Add citations to support factual claims")
        
        if len(citations) < 5:
            recommendations.append("Consider adding more citations to strengthen evidence base")
        
        return recommendations


class MethodologyAnalyzer(SpecializedModule):
    """Specialized module for analyzing research methodology in academic papers."""
    
    def __init__(self):
        super().__init__("MethodologyAnalyzer")
    
    def analyze(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Analyze research methodology quality."""
        try:
            # Look for methodology section
            methodology_section = self._extract_methodology_section(document_content)
            
            # Assess methodology quality
            methodology_quality = self._assess_methodology_quality(methodology_section)
            
            # Check for statistical claims
            statistical_claims = self._identify_statistical_claims(verification_results)
            
            return {
                "module": self.module_name,
                "has_methodology_section": bool(methodology_section),
                "methodology_quality_score": methodology_quality,
                "statistical_claims_count": len(statistical_claims),
                "methodology_issues": self._identify_methodology_issues(methodology_section),
                "recommendations": self._generate_methodology_recommendations(methodology_quality)
            }
            
        except Exception as e:
            self.logger.error(f"Error in methodology analysis: {e}")
            return {"module": self.module_name, "error": str(e)}
    
    def _extract_methodology_section(self, document_content: str) -> str:
        """Extract methodology section from document."""
        # Look for common methodology section headers
        import re
        
        methodology_patterns = [
            r'(?i)(methodology|methods?|experimental\s+design|study\s+design).*?(?=\n\s*[A-Z][^.]*\n|\n\s*\d+\.|\Z)',
            r'(?i)##?\s*(methodology|methods?|experimental\s+design).*?(?=\n\s*##?|\Z)'
        ]
        
        for pattern in methodology_patterns:
            match = re.search(pattern, document_content, re.DOTALL)
            if match:
                return match.group(0)
        
        return ""
    
    def _assess_methodology_quality(self, methodology_section: str) -> float:
        """Assess the quality of the methodology section."""
        if not methodology_section:
            return 0.0
        
        quality_indicators = [
            "sample size", "participants", "data collection", "statistical analysis",
            "control group", "randomized", "blind", "procedure", "instruments",
            "validity", "reliability", "ethics", "limitations"
        ]
        
        found_indicators = sum(
            1 for indicator in quality_indicators
            if indicator.lower() in methodology_section.lower()
        )
        
        return min(1.0, found_indicators / len(quality_indicators))
    
    def _identify_statistical_claims(
        self,
        verification_results: List[ClaimVerificationResult]
    ) -> List[ClaimVerificationResult]:
        """Identify claims that involve statistical information."""
        statistical_keywords = [
            "percent", "%", "significant", "correlation", "p-value", "confidence",
            "mean", "average", "median", "standard deviation", "regression"
        ]
        
        statistical_claims = []
        for result in verification_results:
            claim_text = result.claim.text.lower()
            if any(keyword in claim_text for keyword in statistical_keywords):
                statistical_claims.append(result)
        
        return statistical_claims
    
    def _identify_methodology_issues(self, methodology_section: str) -> List[str]:
        """Identify potential issues with methodology."""
        issues = []
        
        if not methodology_section:
            issues.append("No methodology section found")
            return issues
        
        # Check for common methodology issues
        if "sample size" not in methodology_section.lower():
            issues.append("Sample size not clearly specified")
        
        if "control" not in methodology_section.lower():
            issues.append("Control group or control conditions not mentioned")
        
        if "limitation" not in methodology_section.lower():
            issues.append("Study limitations not discussed")
        
        return issues
    
    def _generate_methodology_recommendations(self, quality_score: float) -> List[str]:
        """Generate recommendations for methodology improvement."""
        recommendations = []
        
        if quality_score < 0.3:
            recommendations.append("Methodology section needs significant improvement")
        elif quality_score < 0.6:
            recommendations.append("Consider adding more methodological details")
        
        recommendations.append("Verify statistical claims against reported methodology")
        
        return recommendations


class NewsSourceCredibilityAnalyzer(SpecializedModule):
    """Specialized module for analyzing news source credibility."""
    
    def __init__(self):
        super().__init__("NewsSourceCredibilityAnalyzer")
        # In practice, this would load from a credibility database
        self.credible_sources = {
            "reuters.com": 0.9, "ap.org": 0.9, "bbc.com": 0.85,
            "npr.org": 0.85, "pbs.org": 0.8, "cnn.com": 0.7,
            "nytimes.com": 0.8, "washingtonpost.com": 0.8
        }
    
    def analyze(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Analyze news source credibility."""
        try:
            source_url = document_metadata.get("source_url", "")
            source_domain = self._extract_domain(source_url)
            
            # Assess source credibility
            credibility_score = self._assess_source_credibility(source_domain)
            
            # Check for bias indicators
            bias_indicators = self._detect_bias_indicators(document_content)
            
            # Analyze evidence sources
            evidence_credibility = self._analyze_evidence_sources(verification_results)
            
            return {
                "module": self.module_name,
                "source_domain": source_domain,
                "source_credibility_score": credibility_score,
                "bias_indicators": bias_indicators,
                "evidence_credibility_score": evidence_credibility,
                "recommendations": self._generate_credibility_recommendations(
                    credibility_score, bias_indicators
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error in news source credibility analysis: {e}")
            return {"module": self.module_name, "error": str(e)}
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        import re
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else ""
    
    def _assess_source_credibility(self, domain: str) -> float:
        """Assess credibility of news source."""
        return self.credible_sources.get(domain, 0.5)  # Default to neutral
    
    def _detect_bias_indicators(self, content: str) -> List[str]:
        """Detect potential bias indicators in content."""
        bias_indicators = []
        
        # Emotional language indicators
        emotional_words = [
            "outrageous", "shocking", "devastating", "incredible", "amazing",
            "terrible", "wonderful", "disgusting", "brilliant"
        ]
        
        found_emotional = [word for word in emotional_words if word in content.lower()]
        if len(found_emotional) > 5:
            bias_indicators.append("High use of emotional language")
        
        # Opinion indicators
        opinion_phrases = [
            "i think", "in my opinion", "clearly", "obviously", "undoubtedly"
        ]
        
        found_opinion = [phrase for phrase in opinion_phrases if phrase in content.lower()]
        if found_opinion:
            bias_indicators.append("Contains opinion statements")
        
        return bias_indicators
    
    def _analyze_evidence_sources(
        self,
        verification_results: List[ClaimVerificationResult]
    ) -> float:
        """Analyze credibility of evidence sources used in verification."""
        if not verification_results:
            return 0.0
        
        total_credibility = 0.0
        evidence_count = 0
        
        for result in verification_results:
            for evidence in result.supporting_evidence:
                total_credibility += evidence.credibility_score
                evidence_count += 1
        
        return total_credibility / evidence_count if evidence_count > 0 else 0.0
    
    def _generate_credibility_recommendations(
        self,
        credibility_score: float,
        bias_indicators: List[str]
    ) -> List[str]:
        """Generate recommendations for assessing credibility."""
        recommendations = []
        
        if credibility_score < 0.5:
            recommendations.append("Source has low credibility - verify claims with additional sources")
        
        if bias_indicators:
            recommendations.append("Potential bias detected - consider alternative perspectives")
        
        recommendations.append("Cross-reference claims with multiple independent sources")
        
        return recommendations


class NewsBiasDetector(SpecializedModule):
    """Specialized module for detecting bias in news articles."""
    
    def __init__(self):
        super().__init__("NewsBiasDetector")
    
    def analyze(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Detect bias in news content."""
        try:
            # Detect different types of bias
            selection_bias = self._detect_selection_bias(document_content, verification_results)
            framing_bias = self._detect_framing_bias(document_content)
            source_bias = self._detect_source_bias(verification_results)
            
            # Calculate overall bias score
            overall_bias = (selection_bias + framing_bias + source_bias) / 3
            
            return {
                "module": self.module_name,
                "selection_bias_score": selection_bias,
                "framing_bias_score": framing_bias,
                "source_bias_score": source_bias,
                "overall_bias_score": overall_bias,
                "bias_level": self._categorize_bias_level(overall_bias),
                "recommendations": self._generate_bias_recommendations(overall_bias)
            }
            
        except Exception as e:
            self.logger.error(f"Error in bias detection: {e}")
            return {"module": self.module_name, "error": str(e)}
    
    def _detect_selection_bias(
        self,
        content: str,
        verification_results: List[ClaimVerificationResult]
    ) -> float:
        """Detect selection bias in claim presentation."""
        # Simplified selection bias detection
        # Check if only positive or negative claims are presented
        if not verification_results:
            return 0.0
        
        supported_claims = sum(1 for r in verification_results if r.verification_result.value == "SUPPORTED")
        refuted_claims = sum(1 for r in verification_results if r.verification_result.value == "REFUTED")
        
        total_claims = supported_claims + refuted_claims
        if total_claims == 0:
            return 0.0
        
        # High bias if heavily skewed toward one side
        ratio = abs(supported_claims - refuted_claims) / total_claims
        return min(1.0, ratio)
    
    def _detect_framing_bias(self, content: str) -> float:
        """Detect framing bias in language use."""
        # Look for loaded language and framing
        positive_words = ["success", "achievement", "progress", "improvement", "benefit"]
        negative_words = ["failure", "disaster", "crisis", "problem", "threat"]
        
        positive_count = sum(1 for word in positive_words if word in content.lower())
        negative_count = sum(1 for word in negative_words if word in content.lower())
        
        total_loaded = positive_count + negative_count
        if total_loaded == 0:
            return 0.0
        
        # High bias if heavily skewed toward positive or negative framing
        ratio = abs(positive_count - negative_count) / total_loaded
        return min(1.0, ratio)
    
    def _detect_source_bias(self, verification_results: List[ClaimVerificationResult]) -> float:
        """Detect bias in source selection."""
        # Check diversity of evidence sources
        if not verification_results:
            return 0.0
        
        source_types = set()
        for result in verification_results:
            for evidence in result.supporting_evidence:
                source_types.add(evidence.evidence_type.value)
        
        # Low diversity indicates potential source bias
        max_diversity = 5  # Assume 5 different source types available
        diversity_ratio = len(source_types) / max_diversity
        
        return max(0.0, 1.0 - diversity_ratio)
    
    def _categorize_bias_level(self, bias_score: float) -> str:
        """Categorize bias level based on score."""
        if bias_score < 0.3:
            return "Low bias"
        elif bias_score < 0.6:
            return "Moderate bias"
        else:
            return "High bias"
    
    def _generate_bias_recommendations(self, bias_score: float) -> List[str]:
        """Generate recommendations for addressing bias."""
        recommendations = []
        
        if bias_score > 0.6:
            recommendations.append("High bias detected - seek alternative sources")
        elif bias_score > 0.3:
            recommendations.append("Moderate bias detected - consider multiple perspectives")
        
        recommendations.append("Compare with sources from different political orientations")
        recommendations.append("Look for primary sources and official statements")
        
        return recommendations


class LegalPrecedentChecker(SpecializedModule):
    """Specialized module for checking legal precedents and citations."""
    
    def __init__(self):
        super().__init__("LegalPrecedentChecker")
    
    def analyze(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Analyze legal precedents and citations."""
        try:
            # Extract legal citations
            legal_citations = self._extract_legal_citations(document_content)
            
            # Verify precedent validity
            precedent_validity = self._verify_precedent_validity(legal_citations)
            
            # Check jurisdiction alignment
            jurisdiction_alignment = self._check_jurisdiction_alignment(
                legal_citations, document_metadata
            )
            
            return {
                "module": self.module_name,
                "legal_citations_count": len(legal_citations),
                "precedent_validity_score": precedent_validity,
                "jurisdiction_alignment_score": jurisdiction_alignment,
                "legal_citations": legal_citations,
                "recommendations": self._generate_legal_recommendations(
                    precedent_validity, jurisdiction_alignment
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error in legal precedent analysis: {e}")
            return {"module": self.module_name, "error": str(e)}
    
    def _extract_legal_citations(self, content: str) -> List[Dict[str, Any]]:
        """Extract legal citations from document."""
        import re
        
        citations = []
        
        # Pattern for case citations: Case Name, Volume Reporter Page (Year)
        case_pattern = r'([A-Za-z\s]+v\.?\s+[A-Za-z\s]+),?\s*(\d+)\s+([A-Za-z\.]+)\s+(\d+)\s*\((\d{4})\)'
        matches = re.findall(case_pattern, content)
        
        for i, (case_name, volume, reporter, page, year) in enumerate(matches):
            citations.append({
                "id": f"case_{i}",
                "type": "case",
                "case_name": case_name.strip(),
                "volume": volume,
                "reporter": reporter,
                "page": page,
                "year": int(year)
            })
        
        return citations
    
    def _verify_precedent_validity(self, citations: List[Dict[str, Any]]) -> float:
        """Verify validity of legal precedents."""
        if not citations:
            return 0.0
        
        # Simplified validity check
        # In practice, this would check against legal databases
        valid_citations = 0
        
        for citation in citations:
            # Check if citation has required elements
            if all(key in citation for key in ["case_name", "volume", "reporter", "page", "year"]):
                # Check if year is reasonable
                if 1800 <= citation["year"] <= datetime.now().year:
                    valid_citations += 1
        
        return valid_citations / len(citations)
    
    def _check_jurisdiction_alignment(
        self,
        citations: List[Dict[str, Any]],
        document_metadata: Dict[str, Any]
    ) -> float:
        """Check if citations align with document jurisdiction."""
        # Simplified jurisdiction check
        # In practice, this would involve sophisticated jurisdiction analysis
        return 0.8  # Placeholder score
    
    def _generate_legal_recommendations(
        self,
        validity_score: float,
        jurisdiction_score: float
    ) -> List[str]:
        """Generate recommendations for legal document analysis."""
        recommendations = []
        
        if validity_score < 0.7:
            recommendations.append("Some legal citations may be invalid - verify with legal databases")
        
        if jurisdiction_score < 0.7:
            recommendations.append("Check jurisdiction alignment of cited cases")
        
        recommendations.append("Verify current status of cited cases (not overturned)")
        
        return recommendations


class StatuteVerifier(SpecializedModule):
    """Specialized module for verifying statutory references."""
    
    def __init__(self):
        super().__init__("StatuteVerifier")
    
    def analyze(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        verification_results: List[ClaimVerificationResult]
    ) -> Dict[str, Any]:
        """Verify statutory references and citations."""
        try:
            # Extract statute references
            statute_refs = self._extract_statute_references(document_content)
            
            # Verify statute validity
            statute_validity = self._verify_statute_validity(statute_refs)
            
            # Check for current status
            current_status = self._check_current_status(statute_refs)
            
            return {
                "module": self.module_name,
                "statute_references_count": len(statute_refs),
                "statute_validity_score": statute_validity,
                "current_status_score": current_status,
                "statute_references": statute_refs,
                "recommendations": self._generate_statute_recommendations(
                    statute_validity, current_status
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error in statute verification: {e}")
            return {"module": self.module_name, "error": str(e)}
    
    def _extract_statute_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract statute references from document."""
        import re
        
        references = []
        
        # Pattern for USC references: Title U.S.C. § Section
        usc_pattern = r'(\d+)\s+U\.?S\.?C\.?\s*§\s*(\d+(?:\.\d+)*)'
        matches = re.findall(usc_pattern, content, re.IGNORECASE)
        
        for i, (title, section) in enumerate(matches):
            references.append({
                "id": f"usc_{i}",
                "type": "usc",
                "title": title,
                "section": section,
                "text": f"{title} U.S.C. § {section}"
            })
        
        return references
    
    def _verify_statute_validity(self, references: List[Dict[str, Any]]) -> float:
        """Verify validity of statute references."""
        if not references:
            return 0.0
        
        # Simplified validity check
        # In practice, this would check against legal databases
        valid_refs = 0
        
        for ref in references:
            # Check if reference has required elements
            if ref.get("title") and ref.get("section"):
                # Basic format validation
                try:
                    title_num = int(ref["title"])
                    if 1 <= title_num <= 54:  # Valid USC titles
                        valid_refs += 1
                except ValueError:
                    pass
        
        return valid_refs / len(references)
    
    def _check_current_status(self, references: List[Dict[str, Any]]) -> float:
        """Check current status of statutes (not repealed)."""
        # Simplified status check
        # In practice, this would check current legal status
        return 0.9  # Placeholder score
    
    def _generate_statute_recommendations(
        self,
        validity_score: float,
        status_score: float
    ) -> List[str]:
        """Generate recommendations for statute verification."""
        recommendations = []
        
        if validity_score < 0.8:
            recommendations.append("Some statute references may be invalid - verify format and existence")
        
        if status_score < 0.8:
            recommendations.append("Check current status of referenced statutes")
        
        recommendations.append("Verify statute references against official legal databases")
        
        return recommendations
