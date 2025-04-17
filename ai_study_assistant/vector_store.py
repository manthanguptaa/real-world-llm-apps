# vector_store.py
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)
from pymilvus.exceptions import ConnectionNotExistException


class StudyMaterialsStore:
    def __init__(
        self,
        collection: str = "study_materials",
        dimension: int = 1536,
        uri: str = None,
        token: Optional[str] = None,
    ):
        """
        Vector database implementation for storing study materials.

        Args:
            collection: Name of the Milvus collection
            dimension: Dimension of the vector embeddings
            uri: URI for Milvus connection
                - For local storage with Milvus Lite, use a path ending with .db
                - For a Milvus server, use http://host:port format
            token: Optional authentication token for Milvus server
        """
        self.collection_name = collection
        self.dimension = dimension
        # Get the workspace root directory (parent of ai_study_assistant)
        self.workspace_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # Generate a unique URI if none provided
        if uri is None:
            unique_id = str(uuid.uuid4())[:8]
            timestamp = str(int(time.time()))[-6:]
            tmp_dir = os.path.join(self.workspace_root, "tmp")
            os.makedirs(tmp_dir, exist_ok=True)  # Create tmp folder
            self.uri = os.path.join(tmp_dir, f"sa_{unique_id}_{timestamp}.db")
        else:
            self.uri = uri

        self.token = token
        self.connection_alias = f"sa_{uuid.uuid4().hex[:6]}"
        self.cleanup_old_dbs()  # Clean up old DBs on init

        # Ensure directory exists for local DB
        if "tmp" in self.uri or self.uri.startswith("./"):
            os.makedirs(os.path.dirname(os.path.abspath(self.uri)), exist_ok=True)

        # Connect to Milvus and set up collection
        self._connect()
        self._setup_collection()

    def cleanup_old_dbs(self):
        """Clean up old database files in the tmp directory."""
        tmp_dir = os.path.join(self.workspace_root, "tmp")
        if os.path.exists(tmp_dir):
            current_time = time.time()
            # Keep databases younger than 1 day
            for db_file in os.listdir(tmp_dir):
                if db_file.endswith(".db"):
                    db_path = os.path.join(tmp_dir, db_file)
                    file_age = current_time - os.path.getmtime(db_path)
                    if file_age > 24 * 3600:  # Older than 1 day
                        try:
                            os.remove(db_path)
                            print(f"Deleted old database: {db_path}")
                        except Exception as e:
                            print(f"Error deleting {db_path}: {e}")

    def _connect(self):
        """Connect to Milvus server or local storage."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Disconnect any existing connection to avoid conflicts
                try:
                    connections.disconnect(alias=self.connection_alias)
                except:
                    pass

                # Connect to Milvus
                connections.connect(
                    alias=self.connection_alias,
                    uri=self.uri,
                    token=self.token,
                    timeout=10,
                )

                # Verify connection by listing collections
                utility.list_collections(using=self.connection_alias)
                print(
                    f"Successfully connected to Milvus with alias {self.connection_alias}"
                )
                return
            except Exception as e:
                print(f"Connection error (attempt {retry_count+1}/{max_retries}): {e}")
                retry_count += 1
                time.sleep(1)  # Brief pause before retrying

                if retry_count >= max_retries:
                    # Try with a new unique URI on the last attempt
                    if "tmp" in self.uri or self.uri.startswith("./"):
                        unique_id = str(uuid.uuid4())[:8]
                        timestamp = str(int(time.time()))[-6:]
                        self.uri = os.path.join(
                            self.workspace_root,
                            f"tmp/sa_{unique_id}_{timestamp}.db",
                        )
                        print(f"Trying with new URI: {self.uri}")
                        os.makedirs(
                            os.path.dirname(os.path.abspath(self.uri)), exist_ok=True
                        )
                        retry_count = 0  # Reset retry count to try with new URI
                    else:
                        raise ConnectionNotExistException(
                            message=f"Failed to connect to Milvus after {max_retries} attempts: {str(e)}"
                        )

    def _setup_collection(self):
        """Set up the collection if it doesn't exist."""
        try:
            # Ensure connection is active
            if not connections.has_connection(self.connection_alias):
                self._connect()

            if not utility.has_collection(
                self.collection_name, using=self.connection_alias
            ):
                fields = [
                    FieldSchema(
                        name="id", dtype=DataType.INT64, is_primary=True, auto_id=True
                    ),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(
                        name="metadata", dtype=DataType.VARCHAR, max_length=10000
                    ),
                    FieldSchema(
                        name="embedding",
                        dtype=DataType.FLOAT_VECTOR,
                        dim=self.dimension,
                    ),
                ]
                schema = CollectionSchema(fields=fields)
                self.collection = Collection(
                    name=self.collection_name,
                    schema=schema,
                    using=self.connection_alias,
                )

                # Create index
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024},
                }
                self.collection.create_index(
                    field_name="embedding", index_params=index_params
                )
                self.collection.load()
            else:
                self.collection = Collection(
                    name=self.collection_name, using=self.connection_alias
                )
                self.collection.load()
        except Exception as e:
            print(f"Setup collection error: {e}")
            raise

    def store_vectors(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict] = None,
    ) -> List[int]:
        """
        Store vectors in the collection.

        Args:
            texts: List of text content
            embeddings: List of embedding vectors
            metadata: Optional list of metadata dictionaries

        Returns:
            List of primary keys for the inserted entities
        """
        try:
            # Handle metadata
            if metadata is None:
                metadata = [{}] * len(texts)

            # Convert metadata dicts to JSON strings
            metadata_json = [json.dumps(m) for m in metadata]

            entities = [texts, metadata_json, embeddings]
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            return insert_result.primary_keys
        except ConnectionNotExistException:
            self._connect()
            self._setup_collection()
            return self.store_vectors(texts, embeddings, metadata)
        except Exception as e:
            print(f"Store vectors error: {e}")
            raise

    def search_vectors(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return

        Returns:
            List of dictionaries containing id, text, metadata, and distance
        """
        try:
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "metadata"],
            )

            return [
                {
                    "id": hit.id,
                    "text": hit.entity.get("text"),
                    "metadata": hit.entity.get("metadata"),
                    "distance": hit.distance,
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

    def drop(self):
        """Drop the collection."""
        try:
            if utility.has_collection(
                self.collection_name, using=self.connection_alias
            ):
                utility.drop_collection(
                    self.collection_name, using=self.connection_alias
                )
                # Reconnect and recreate
                self._connect()
                self._setup_collection()
        except Exception as e:
            print(f"Drop collection error: {e}")
            raise
