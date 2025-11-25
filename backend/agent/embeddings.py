"""
Embedding service for generating embeddings and performing semantic search.

This module provides functionality to generate embeddings using OpenAI's embedding
models and perform cosine similarity search to find the most relevant records.
"""
import logging
from typing import List, Dict
import numpy as np

from langchain_openai import OpenAIEmbeddings
from config import Config

LOGGER = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings and performing semantic search."""
    
    def __init__(self):
        """Initialize the embedding service with OpenAI embeddings."""
        try:
            if not Config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set. Cannot initialize embeddings.")
            
            self.embedder = OpenAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                api_key=Config.OPENAI_API_KEY
            )
            LOGGER.info(f"EmbeddingService initialized with model: {Config.EMBEDDING_MODEL}")
        except Exception as e:
            LOGGER.error(f"Failed to initialize EmbeddingService: {e}")
            raise
    
    def prepare_text_for_embedding(self, data_item: Dict) -> str:
        """
        Convert a DataItem dictionary to a searchable text string.
        
        Args:
            data_item: Dictionary with keys like FullName, FullAddress, PhoneMobile, etc.
            
        Returns:
            Formatted text string for embedding
        """
        parts = []
        
        if data_item.get("FullName") or data_item.get("full_name"):
            name = data_item.get("FullName") or data_item.get("full_name")
            parts.append(f"Name: {name}")
        
        if data_item.get("FullAddress") or data_item.get("full_address"):
            address = data_item.get("FullAddress") or data_item.get("full_address")
            parts.append(f"Address: {address}")
        
        # Add phone if available (prefer mobile, fallback to landline)
        phone = (data_item.get("PhoneMobile") or 
                data_item.get("phone2_mobile") or
                data_item.get("PhoneLandline") or
                data_item.get("phone1_landline"))
        if phone:
            parts.append(f"Phone: {phone}")
        
        # Add email if available
        email = data_item.get("EmailAddress") or data_item.get("emailaddress")
        if email:
            parts.append(f"Email: {email}")
        
        return ". ".join(parts) if parts else ""
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if not texts:
            return []
        
        try:
            LOGGER.debug(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.embedder.embed_documents(texts)
            LOGGER.debug(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            LOGGER.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query string.
        
        Args:
            query: Query string to embed
            
        Returns:
            Embedding vector as list of floats
        """
        LOGGER.info(f"Embedding query: {query}")
        try:
            return self.embedder.embed_query(query)
        except Exception as e:
            LOGGER.error(f"Error embedding query: {e}")
            raise
    
    def search_similar(
        self,
        query: str,
        data_items: List[Dict],
        embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find most similar data items to query using cosine similarity.
        
        Args:
            query: Query string
            data_items: List of data item dictionaries
            embeddings: Pre-computed embeddings for data_items
            top_k: Number of results to return
            
        Returns:
            List of top_k most similar data items
        """
        if not data_items or not embeddings:
            LOGGER.warning("search_similar called with empty data_items or embeddings")
            return []
        
        if len(data_items) != len(embeddings):
            LOGGER.error(f"Mismatch: {len(data_items)} data_items but {len(embeddings)} embeddings")
            return []
        
        try:
            # Generate query embedding
            query_embedding = np.array(self.embed_query(query))
            
            # Calculate cosine similarities
            similarities = []
            embeddings_array = np.array(embeddings)
            
            for i, item_embedding in enumerate(embeddings_array):
                # Cosine similarity: dot product / (norm(query) * norm(item))
                dot_product = np.dot(query_embedding, item_embedding)
                norm_query = np.linalg.norm(query_embedding)
                norm_item = np.linalg.norm(item_embedding)
                
                if norm_query > 0 and norm_item > 0:
                    similarity = dot_product / (norm_query * norm_item)
                else:
                    similarity = 0.0
                
                similarities.append((similarity, i))
            
            # Sort by similarity (descending) and get top_k
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_indices = [idx for _, idx in similarities[:top_k]]
            
            LOGGER.info(f"Found {len(top_indices)} most similar records (top similarity: {similarities[0][0]:.4f})")
            return [data_items[i] for i in top_indices]
            
        except Exception as e:
            LOGGER.error(f"Error in search_similar: {e}")
            # Fallback: return first top_k items
            LOGGER.warning(f"Falling back to first {min(top_k, len(data_items))} items")
            return data_items[:top_k]

