"""
Qdrant vector database connection and utilities for the DSPy-Enhanced Fact-Checker API Platform.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance, VectorParams, CreateCollection, PointStruct, 
    Filter, FieldCondition, MatchValue, SearchRequest
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Global Qdrant client
qdrant_client = None


async def init_qdrant():
    """Initialize Qdrant client."""
    global qdrant_client
    
    settings = get_settings()
    
    try:
        # Parse Qdrant URL
        qdrant_url = settings.QDRANT_URL
        logger.info(f"Initializing Qdrant connection to: {qdrant_url}")
        
        # Create client
        qdrant_client = QdrantClient(
            url=qdrant_url,
            timeout=30,
            prefer_grpc=False  # Use HTTP for simplicity
        )
        
        # Test connection
        collections = qdrant_client.get_collections()
        logger.info(f"Qdrant connection successful. Found {len(collections.collections)} collections")
        
        # Initialize default collections
        await _init_default_collections()
        
        logger.info("Qdrant client initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        raise


async def close_qdrant():
    """Close Qdrant client."""
    global qdrant_client
    
    if qdrant_client:
        try:
            qdrant_client.close()
            qdrant_client = None
            logger.info("Qdrant client closed")
        except Exception as e:
            logger.error(f"Error closing Qdrant client: {e}")


async def _init_default_collections():
    """Initialize default collections for the fact-checker."""
    global qdrant_client
    
    if not qdrant_client:
        return
    
    # Default collections configuration
    collections_config = {
        "documents": {
            "vector_size": 768,  # Standard embedding size
            "distance": Distance.COSINE,
            "description": "Document embeddings for semantic search"
        },
        "claims": {
            "vector_size": 768,
            "distance": Distance.COSINE,
            "description": "Claim embeddings for fact-checking"
        },
        "sources": {
            "vector_size": 768,
            "distance": Distance.COSINE,
            "description": "Source document embeddings"
        },
        "fact_checks": {
            "vector_size": 768,
            "distance": Distance.COSINE,
            "description": "Fact-check result embeddings"
        }
    }
    
    try:
        existing_collections = {
            col.name for col in qdrant_client.get_collections().collections
        }
        
        for collection_name, config in collections_config.items():
            if collection_name not in existing_collections:
                logger.info(f"Creating collection: {collection_name}")
                
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=config["vector_size"],
                        distance=config["distance"]
                    )
                )
                
                logger.info(f"Collection {collection_name} created successfully")
            else:
                logger.info(f"Collection {collection_name} already exists")
                
    except Exception as e:
        logger.error(f"Failed to initialize default collections: {e}")
        raise


class QdrantManager:
    """Qdrant vector database manager."""
    
    def __init__(self):
        self.client = qdrant_client
    
    async def create_collection(
        self, 
        collection_name: str, 
        vector_size: int = 768,
        distance: Distance = Distance.COSINE,
        **kwargs
    ) -> bool:
        """Create a new collection."""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                ),
                **kwargs
            )
            logger.info(f"Collection {collection_name} created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Collection {collection_name} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def upsert_points(
        self, 
        collection_name: str, 
        points: List[Dict[str, Any]]
    ) -> bool:
        """Insert or update points in a collection."""
        try:
            # Convert to PointStruct objects
            point_structs = []
            for point in points:
                point_id = point.get("id", str(uuid.uuid4()))
                vector = point["vector"]
                payload = point.get("payload", {})
                
                point_structs.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                )
            
            # Upsert points
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            
            logger.info(f"Upserted {len(points)} points to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            return False
    
    async def search_similar(
        self, 
        collection_name: str, 
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)
            
            # Perform search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                    "vector": hit.vector
                })
            
            logger.info(f"Found {len(results)} similar vectors in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            return []
    
    async def get_point(
        self, 
        collection_name: str, 
        point_id: Union[str, int]
    ) -> Optional[Dict[str, Any]]:
        """Get a specific point by ID."""
        try:
            result = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_vectors=True,
                with_payload=True
            )
            
            if result:
                point = result[0]
                return {
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get point {point_id} from {collection_name}: {e}")
            return None
    
    async def delete_points(
        self, 
        collection_name: str, 
        point_ids: List[Union[str, int]]
    ) -> bool:
        """Delete specific points."""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            
            logger.info(f"Deleted {len(point_ids)} points from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete points from {collection_name}: {e}")
            return False
    
    async def count_points(self, collection_name: str) -> int:
        """Count points in a collection."""
        try:
            result = self.client.count(collection_name=collection_name)
            return result.count
            
        except Exception as e:
            logger.error(f"Failed to count points in {collection_name}: {e}")
            return 0
    
    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information."""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "status": info.status,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance.value
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return None
    
    async def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []


class DocumentEmbeddingManager:
    """Manager for document embeddings in Qdrant."""
    
    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name
        self.qdrant = QdrantManager()
    
    async def store_document_embedding(
        self, 
        document_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store document embedding."""
        payload = {
            "document_id": document_id,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
            "type": "document"
        }
        
        if metadata:
            payload.update(metadata)
        
        points = [{
            "id": document_id,
            "vector": embedding,
            "payload": payload
        }]
        
        return await self.qdrant.upsert_points(self.collection_name, points)
    
    async def search_similar_documents(
        self, 
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        return await self.qdrant.search_similar(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
    
    async def get_document_embedding(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document embedding by ID."""
        return await self.qdrant.get_point(self.collection_name, document_id)
    
    async def delete_document_embedding(self, document_id: str) -> bool:
        """Delete document embedding."""
        return await self.qdrant.delete_points(self.collection_name, [document_id])


class QdrantHealthCheck:
    """Qdrant health check utilities."""
    
    @staticmethod
    async def check_connection() -> bool:
        """Check if Qdrant connection is healthy."""
        try:
            global qdrant_client
            if qdrant_client:
                collections = qdrant_client.get_collections()
                return True
            return False
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    @staticmethod
    async def get_info() -> Dict[str, Any]:
        """Get Qdrant server information."""
        try:
            global qdrant_client
            if qdrant_client:
                collections = qdrant_client.get_collections()
                
                total_points = 0
                collection_info = []
                
                for collection in collections.collections:
                    try:
                        info = qdrant_client.get_collection(collection.name)
                        total_points += info.points_count
                        collection_info.append({
                            "name": collection.name,
                            "points_count": info.points_count,
                            "vectors_count": info.vectors_count
                        })
                    except Exception:
                        pass
                
                return {
                    "status": "connected",
                    "collections_count": len(collections.collections),
                    "total_points": total_points,
                    "collections": collection_info
                }
            else:
                return {
                    "status": "not_initialized",
                    "error": "Qdrant client not initialized"
                }
                
        except Exception as e:
            logger.error(f"Failed to get Qdrant info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global instances
qdrant_manager = QdrantManager()
document_embedding_manager = DocumentEmbeddingManager()


# FastAPI dependencies
def get_qdrant_manager() -> QdrantManager:
    """FastAPI dependency for Qdrant manager."""
    return qdrant_manager


def get_document_embedding_manager() -> DocumentEmbeddingManager:
    """FastAPI dependency for document embedding manager."""
    return document_embedding_manager
