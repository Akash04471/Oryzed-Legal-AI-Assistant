import os
import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

COLLECTION_NAME = "legal_knowledge_base"
EMBEDDING_DIMENSION = 384  # Dimension of sentence-transformers/all-MiniLM-L6-v2

_qdrant_client = None

def get_qdrant_client():
    """
    Initializes and caches the Qdrant Client based on environment settings.
    - Uses QDRANT_URL and QDRANT_API_KEY if defined.
    - Otherwise, falls back to a local storage database in 'qdrant_local' directory.
    - On serverless Vercel deployments, defaults to in-memory store.
    """
    global _qdrant_client
    if _qdrant_client is None:
        qdrant_url = os.environ.get("QDRANT_URL")
        qdrant_api_key = os.environ.get("QDRANT_API_KEY")
        
        if qdrant_url:
            logger.info(f"Connecting to Qdrant Cloud/Server at: {qdrant_url}")
            _qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            if os.environ.get("VERCEL"):
                logger.info("Vercel environment detected. Running Qdrant client in-memory (unpersistent).")
                _qdrant_client = QdrantClient(":memory:")
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                db_folder = "qdrant_local_test" if os.environ.get("TESTING") == "true" else "qdrant_local"
                qdrant_local_path = os.path.join(base_dir, db_folder)
                logger.info(f"Using local disk-based Qdrant database at: {qdrant_local_path}")
                _qdrant_client = QdrantClient(path=qdrant_local_path)
                
    return _qdrant_client


def init_collection():
    """
    Initializes the 'legal_knowledge_base' collection in Qdrant.
    Checks if the collection exists and recreates it if a vector size mismatch is found.
    """
    client = get_qdrant_client()
    try:
        collections_response = client.get_collections()
        collections = [c.name for c in collections_response.collections]
        
        recreate = False
        if COLLECTION_NAME in collections:
            # Check existing collection dimensions to avoid mismatched vector inserts
            info = client.get_collection(collection_name=COLLECTION_NAME)
            existing_size = info.config.params.vectors.size
            if existing_size != EMBEDDING_DIMENSION:
                logger.info(f"Existing Qdrant collection size {existing_size} does not match target {EMBEDDING_DIMENSION}. Recreating...")
                client.delete_collection(collection_name=COLLECTION_NAME)
                recreate = True
        else:
            recreate = True
            
        if recreate:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Collection '{COLLECTION_NAME}' created successfully with dimension {EMBEDDING_DIMENSION}.")
        else:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists in Qdrant and is up-to-date.")
    except Exception as e:
        logger.error(f"Error initializing Qdrant collection: {e}")
        raise e


def upsert_chunks(chunks, embeddings):
    """
    Upserts document chunks and their OpenAI embeddings into Qdrant.
    
    Args:
        chunks (list of dict): List of document chunk objects.
        embeddings (list of list of float): List of corresponding vector embeddings.
    """
    if not chunks or not embeddings:
        return
        
    if len(chunks) != len(embeddings):
        raise ValueError("The number of chunks and embeddings must match.")
        
    client = get_qdrant_client()
    
    # Make sure collection exists
    init_collection()
    
    points = []
    for idx, chunk in enumerate(chunks):
        point_id = str(uuid.uuid4())
        metadata = chunk["metadata"]
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=embeddings[idx],
                payload={
                    "text": chunk["text"],
                    "file_name": metadata["file_name"],
                    "start_page": metadata["start_page"],
                    "end_page": metadata["end_page"],
                    "upload_date": metadata["upload_date"]
                }
            )
        )
        
    try:
        # Upsert in batches of 100 points
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch
            )
        logger.info(f"Successfully upserted {len(points)} chunks into Qdrant collection '{COLLECTION_NAME}'.")
    except Exception as e:
        logger.error(f"Failed to upsert points to Qdrant: {e}")
        raise e


def search_similar_chunks(query_vector, limit=5, file_filter=None):
    """
    Searches Qdrant collection for chunks similar to the query vector.
    
    Args:
        query_vector (list of float): The vector embedding of the query.
        limit (int): Top-K matches. Defaults to 5.
        file_filter (str): Optional file name to filter results by.
        
    Returns:
        list of dict: Search matches containing payloads and scores.
    """
    client = get_qdrant_client()
    
    query_filter = None
    if file_filter:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="file_name",
                    match=models.MatchValue(value=file_filter)
                )
            ]
        )
        
    try:
        # Ensure collection exists before querying (safely inside try-except)
        init_collection()
        
        # Using query_points as client.search is deprecated/removed in newer qdrant-client versions
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            query_filter=query_filter
        )
        
        search_results = response.points if hasattr(response, "points") else response
        
        results = []
        for hit in search_results:
            results.append({
                "text": hit.payload.get("text", ""),
                "file_name": hit.payload.get("file_name", "Unknown"),
                "start_page": hit.payload.get("start_page", 1),
                "end_page": hit.payload.get("end_page", 1),
                "upload_date": hit.payload.get("upload_date", ""),
                "score": hit.score
            })
            
        logger.info(f"Qdrant search found {len(results)} matches.")
        return results
    except Exception as e:
        logger.error(f"Failed to search Qdrant collection '{COLLECTION_NAME}': {e}")
        return []


def delete_file_chunks(file_name):
    """
    Deletes all vector points associated with a specific file name from Qdrant.
    Used during document updates to replace old chunks.
    """
    client = get_qdrant_client()
    try:
        # Check if collection exists first
        collections_response = client.get_collections()
        collections = [c.name for c in collections_response.collections]
        if COLLECTION_NAME not in collections:
            return

        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_name",
                            match=models.MatchValue(value=file_name)
                         )
                    ]
                )
            )
        )
        logger.info(f"Deleted existing chunks for file '{file_name}' from Qdrant.")
    except Exception as e:
        logger.error(f"Failed to delete chunks for file '{file_name}' from Qdrant: {e}")
        raise e

