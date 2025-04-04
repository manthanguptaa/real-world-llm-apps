from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np
from typing import List, Dict, Any, Optional
import os
from pymilvus.exceptions import ConnectionNotExistException

class Milvus:
    def __init__(
        self,
        collection: str = "knowledge",
        dimension: int = 1536,
        uri: str = "tmp/milvus.db",
        token: Optional[str] = None
    ):
        """
        Milvus vector database implementation.
        
        Args:
            collection: Name of the Milvus collection
            dimension: Dimension of the vector embeddings
            uri: URI for Milvus connection
                - For local storage with Milvus Lite, use a path ending with .db (e.g., "tmp/milvus.db")
                - For a Milvus server, use http://host:port format
            token: Optional authentication token for Milvus server
        """
        self.collection_name = collection
        self.dimension = dimension
        self.uri = uri
        self.token = token
        self.connection_alias = "default"
        
        # Ensure directory exists for local DB
        if uri.startswith("tmp/") or uri.startswith("./"):
            os.makedirs(os.path.dirname(os.path.abspath(uri)), exist_ok=True)
        
        # Connect and set up collection
        self._connect()
        self._setup_collection()

    def _connect(self):
        """Connect to Milvus server or local storage."""
        try:
            # Disconnect first if we're already connected to avoid issues
            try:
                connections.disconnect(alias=self.connection_alias)
            except:
                pass
                
            # Connect to Milvus
            connections.connect(
                alias=self.connection_alias,
                uri=self.uri,
                token=self.token
            )
        except Exception as e:
            print(f"Connection error: {e}")
            raise

    def _setup_collection(self):
        """Set up the collection if it doesn't exist."""
        try:
            if not utility.has_collection(self.collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension)
                ]
                schema = CollectionSchema(fields=fields)
                self.collection = Collection(name=self.collection_name, schema=schema)
                
                # Create index
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                }
                self.collection.create_index(field_name="embedding", index_params=index_params)
                self.collection.load()
            else:
                self.collection = Collection(self.collection_name)
                self.collection.load()
        except ConnectionNotExistException:
            self._connect()
            self._setup_collection()
        except Exception as e:
            print(f"Setup collection error: {e}")
            raise

    def store_vectors(self, texts: List[str], embeddings: List[List[float]]) -> List[int]:
        """
        Store vectors in the collection.
        
        Args:
            texts: List of text content
            embeddings: List of embedding vectors
            
        Returns:
            List of primary keys for the inserted entities
        """
        try:
            entities = [
                texts,
                embeddings
            ]
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            return insert_result.primary_keys
        except ConnectionNotExistException:
            self._connect()
            self._setup_collection()
            return self.store_vectors(texts, embeddings)
        except Exception as e:
            print(f"Store vectors error: {e}")
            raise

    def search_vectors(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for vectors similar to the query embedding.
        
        Args:
            query_embedding: The embedding vector to search for
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing id, text, and distance
        """
        try:
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text"]
            )
            
            return [
                {
                    "id": hit.id,
                    "text": hit.entity.get("text"),
                    "distance": hit.distance
                }
                for hit in results[0]
            ]
        except ConnectionNotExistException:
            self._connect()
            self._setup_collection()
            return self.search_vectors(query_embedding, top_k)
        except Exception as e:
            print(f"Search vectors error: {e}")
            raise
        
    def exists(self) -> bool:
        """Check if the collection exists."""
        try:
            return utility.has_collection(self.collection_name)
        except ConnectionNotExistException:
            self._connect()
            return self.exists()
        except Exception as e:
            print(f"Exists error: {e}")
            return False
        
    def drop(self) -> None:
        """Drop the collection if it exists."""
        try:
            if self.exists():
                self.collection.release()
                utility.drop_collection(self.collection_name)
        except ConnectionNotExistException:
            self._connect()
            self.drop()
        except Exception as e:
            print(f"Drop error: {e}")

    def __del__(self):
        """Clean up resources when the object is deleted."""
        try:
            if hasattr(self, 'collection'):
                self.collection.release()
            connections.disconnect(alias=self.connection_alias)
        except:
            # Ignore errors during cleanup
            pass 