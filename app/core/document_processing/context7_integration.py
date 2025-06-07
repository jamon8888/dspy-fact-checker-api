#!/usr/bin/env python3
"""
Context7 Integration for Enhanced Document Processing
Provides real-time access to documentation and library information
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests not available for Context7 integration")


class Context7Client:
    """Client for Context7 MCP server integration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Context7 client."""
        config = config or {}
        
        self.base_url = config.get("base_url", "http://localhost:3000")
        self.timeout = config.get("timeout", 30)
        self.max_tokens = config.get("max_tokens", 4000)
        self.enabled = config.get("enabled", True) and REQUESTS_AVAILABLE
        
        if not self.enabled:
            logger.info("Context7 integration disabled")
    
    async def get_library_documentation(
        self, 
        library_name: str, 
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get documentation for a specific library and topic.
        
        Args:
            library_name: Name of the library (e.g., "docling", "spacy")
            topic: Specific topic within the library (optional)
            
        Returns:
            Dictionary containing documentation content
        """
        if not self.enabled:
            return {"error": "Context7 integration not available"}
        
        try:
            # Resolve library name to Context7 ID
            library_id = await self._resolve_library_name(library_name)
            if not library_id:
                return {"error": f"Library '{library_name}' not found in Context7"}
            
            # Fetch documentation
            if topic:
                docs = await self._fetch_topic_documentation(library_id, topic)
            else:
                docs = await self._fetch_library_documentation(library_id)
            
            return {
                "library": library_name,
                "library_id": library_id,
                "topic": topic,
                "documentation": docs,
                "timestamp": datetime.now().isoformat(),
                "source": "context7"
            }
            
        except Exception as e:
            logger.error(f"Failed to get documentation for {library_name}: {e}")
            return {"error": str(e)}
    
    async def search_documentation(
        self, 
        query: str, 
        libraries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search across documentation for specific information.
        
        Args:
            query: Search query
            libraries: List of libraries to search in (optional)
            
        Returns:
            Dictionary containing search results
        """
        if not self.enabled:
            return {"error": "Context7 integration not available"}
        
        try:
            # Perform documentation search
            results = await self._search_across_libraries(query, libraries)
            
            return {
                "query": query,
                "libraries_searched": libraries,
                "results": results,
                "timestamp": datetime.now().isoformat(),
                "source": "context7"
            }
            
        except Exception as e:
            logger.error(f"Documentation search failed: {e}")
            return {"error": str(e)}
    
    async def get_processing_recommendations(
        self, 
        document_type: str, 
        processing_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Get processing recommendations based on document type and goals.
        
        Args:
            document_type: Type of document (pdf, docx, etc.)
            processing_goals: List of processing goals (extract_tables, ocr, etc.)
            
        Returns:
            Dictionary containing processing recommendations
        """
        if not self.enabled:
            return {"error": "Context7 integration not available"}
        
        try:
            # Build query for processing recommendations
            query = f"best practices for processing {document_type} documents with goals: {', '.join(processing_goals)}"
            
            # Search relevant libraries
            relevant_libraries = ["docling", "spacy", "transformers", "opencv"]
            recommendations = await self.search_documentation(query, relevant_libraries)
            
            # Process and structure recommendations
            structured_recommendations = self._structure_recommendations(
                recommendations, document_type, processing_goals
            )
            
            return {
                "document_type": document_type,
                "processing_goals": processing_goals,
                "recommendations": structured_recommendations,
                "timestamp": datetime.now().isoformat(),
                "source": "context7"
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing recommendations: {e}")
            return {"error": str(e)}
    
    async def _resolve_library_name(self, library_name: str) -> Optional[str]:
        """Resolve library name to Context7 library ID."""
        try:
            # This would call the Context7 API to resolve library names
            # For now, return a simple mapping
            library_mapping = {
                "docling": "docling-project/docling",
                "spacy": "explosion/spacy",
                "transformers": "huggingface/transformers",
                "opencv": "opencv/opencv-python",
                "pandas": "pandas-dev/pandas",
                "numpy": "numpy/numpy"
            }
            
            return library_mapping.get(library_name.lower())
            
        except Exception as e:
            logger.error(f"Failed to resolve library name {library_name}: {e}")
            return None
    
    async def _fetch_library_documentation(self, library_id: str) -> Dict[str, Any]:
        """Fetch general documentation for a library."""
        try:
            # This would make an actual API call to Context7
            # For now, return mock documentation structure
            return {
                "overview": f"Documentation for {library_id}",
                "installation": "Installation instructions",
                "basic_usage": "Basic usage examples",
                "advanced_features": "Advanced features documentation",
                "api_reference": "API reference documentation"
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch documentation for {library_id}: {e}")
            return {}
    
    async def _fetch_topic_documentation(self, library_id: str, topic: str) -> Dict[str, Any]:
        """Fetch documentation for a specific topic within a library."""
        try:
            # This would make an actual API call to Context7
            # For now, return mock topic-specific documentation
            return {
                "topic": topic,
                "description": f"Documentation for {topic} in {library_id}",
                "examples": f"Examples for {topic}",
                "parameters": f"Parameters for {topic}",
                "best_practices": f"Best practices for {topic}"
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch topic documentation for {topic}: {e}")
            return {}
    
    async def _search_across_libraries(
        self, 
        query: str, 
        libraries: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search across multiple libraries for documentation."""
        try:
            # This would perform actual search across Context7
            # For now, return mock search results
            results = []
            
            search_libraries = libraries or ["docling", "spacy", "transformers"]
            
            for library in search_libraries:
                library_id = await self._resolve_library_name(library)
                if library_id:
                    results.append({
                        "library": library,
                        "library_id": library_id,
                        "relevance_score": 0.8,
                        "content": f"Search results for '{query}' in {library}",
                        "sections": ["overview", "examples", "api"]
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Search across libraries failed: {e}")
            return []
    
    def _structure_recommendations(
        self, 
        search_results: Dict[str, Any], 
        document_type: str, 
        processing_goals: List[str]
    ) -> Dict[str, Any]:
        """Structure processing recommendations from search results."""
        try:
            recommendations = {
                "preprocessing": [],
                "extraction_methods": [],
                "postprocessing": [],
                "libraries_to_use": [],
                "configuration_tips": []
            }
            
            # Analyze search results and structure recommendations
            results = search_results.get("results", [])
            
            for result in results:
                library = result.get("library", "")
                content = result.get("content", "")
                
                # Add library-specific recommendations
                if library == "docling":
                    recommendations["extraction_methods"].append({
                        "method": "Advanced PDF processing with Docling",
                        "description": "Use Docling for comprehensive PDF analysis",
                        "configuration": "Enable table structure recognition and OCR"
                    })
                
                elif library == "spacy":
                    recommendations["postprocessing"].append({
                        "method": "NLP processing with spaCy",
                        "description": "Use spaCy for text analysis and entity extraction",
                        "configuration": "Load appropriate language model"
                    })
                
                recommendations["libraries_to_use"].append(library)
            
            # Add general recommendations based on document type
            if document_type.lower() == "pdf":
                recommendations["preprocessing"].append({
                    "step": "PDF validation",
                    "description": "Validate PDF structure before processing"
                })
            
            # Add goal-specific recommendations
            for goal in processing_goals:
                if goal == "extract_tables":
                    recommendations["configuration_tips"].append({
                        "tip": "Enable table structure recognition",
                        "description": "Use TableFormer for accurate table extraction"
                    })
                elif goal == "ocr":
                    recommendations["configuration_tips"].append({
                        "tip": "Configure OCR language detection",
                        "description": "Set appropriate language models for OCR"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to structure recommendations: {e}")
            return {}


class DocumentProcessingEnhancer:
    """Enhances document processing using Context7 insights."""
    
    def __init__(self, context7_client: Context7Client):
        """Initialize with Context7 client."""
        self.context7 = context7_client
    
    async def enhance_processing_config(
        self, 
        document_type: str, 
        current_config: Dict[str, Any],
        processing_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Enhance processing configuration using Context7 recommendations.
        
        Args:
            document_type: Type of document being processed
            current_config: Current processing configuration
            processing_goals: List of processing goals
            
        Returns:
            Enhanced configuration dictionary
        """
        try:
            # Get processing recommendations from Context7
            recommendations = await self.context7.get_processing_recommendations(
                document_type, processing_goals
            )
            
            if "error" in recommendations:
                logger.warning(f"Context7 recommendations failed: {recommendations['error']}")
                return current_config
            
            # Apply recommendations to current config
            enhanced_config = current_config.copy()
            
            # Apply configuration tips
            config_tips = recommendations.get("recommendations", {}).get("configuration_tips", [])
            for tip in config_tips:
                self._apply_configuration_tip(enhanced_config, tip)
            
            # Add metadata about enhancements
            enhanced_config["context7_enhanced"] = True
            enhanced_config["enhancement_timestamp"] = datetime.now().isoformat()
            enhanced_config["applied_recommendations"] = len(config_tips)
            
            return enhanced_config
            
        except Exception as e:
            logger.error(f"Failed to enhance processing config: {e}")
            return current_config
    
    def _apply_configuration_tip(self, config: Dict[str, Any], tip: Dict[str, Any]) -> None:
        """Apply a specific configuration tip to the config."""
        try:
            tip_description = tip.get("tip", "").lower()
            
            if "table structure" in tip_description:
                config["enable_table_structure"] = True
                config["table_mode"] = "accurate"
            
            elif "ocr" in tip_description:
                config["enable_ocr"] = True
                config["ocr_language"] = ["en"]  # Could be enhanced with language detection
            
            elif "picture extraction" in tip_description:
                config["enable_picture_extraction"] = True
            
            elif "formula detection" in tip_description:
                config["enable_formula_detection"] = True
            
        except Exception as e:
            logger.error(f"Failed to apply configuration tip: {e}")


# Factory function for easy integration
def create_context7_enhanced_processor(config: Optional[Dict[str, Any]] = None) -> DocumentProcessingEnhancer:
    """Create a Context7-enhanced document processor."""
    context7_client = Context7Client(config)
    return DocumentProcessingEnhancer(context7_client)
