import os
import logging
import requests
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local model (primary) – runs on CPU, no network needed, instant results
# Uses BAAI/bge-small-en-v1.5 which outputs 384-dimension embeddings.
# The model is downloaded once on first use (~130 MB) and cached locally.
# ---------------------------------------------------------------------------
LOCAL_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_local_model = None
_model_load_attempted = False

# Hugging Face Inference API URL (network fallback)
HF_API_URL = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5"


def _get_local_model():
    """
    Lazily loads and caches the local SentenceTransformer model.
    Returns the model instance, or None if sentence-transformers is not installed.
    Only attempts to load once to avoid repeated slow failures.
    """
    global _local_model, _model_load_attempted
    if _local_model is not None:
        return _local_model
    if _model_load_attempted:
        return None
    _model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading local embedding model '{LOCAL_MODEL_NAME}' (first load may download ~130 MB)...")
        _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
        logger.info(f"Local embedding model '{LOCAL_MODEL_NAME}' loaded successfully.")
        return _local_model
    except ImportError:
        logger.warning(
            "sentence-transformers is not installed. Local embeddings unavailable. "
            "Install with: pip install sentence-transformers"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to load local embedding model: {e}")
        return None


def preload_model():
    """
    Eagerly pre-loads the local embedding model at application startup.
    Call this once during app init (before any requests/sync) to avoid
    loading the heavy model mid-request which can cause connection resets.
    """
    model = _get_local_model()
    if model is not None:
        logger.info("Embedding model pre-loaded and ready.")
    else:
        logger.warning("Embedding model could not be pre-loaded. Will use API fallbacks.")


def _get_local_embeddings(texts):
    """
    Generates embeddings using the local SentenceTransformer model.
    Returns a list of lists (embeddings), or None if the local model is unavailable.
    """
    model = _get_local_model()
    if model is None:
        return None
    try:
        logger.info(f"Generating {len(texts)} embeddings locally via '{LOCAL_MODEL_NAME}'...")
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        result = [emb.tolist() for emb in embeddings]
        logger.info(f"Successfully generated {len(result)} local embeddings (dim={len(result[0])}).")
        return result
    except Exception as e:
        logger.error(f"Local embedding generation failed: {e}")
        return None


def get_embeddings_batch(texts, retries=3):
    """
    Generates vector embeddings for a list of text strings.

    Priority order:
      1. Local SentenceTransformer (BAAI/bge-small-en-v1.5) – fastest, no network.
      2. OpenAI text-embedding-3-large (dim=384) – paid API fallback.
      3. Hugging Face Inference API (BAAI/bge-small-en-v1.5) – free API fallback.

    Args:
        texts (list of str): List of input texts.
        retries (int): Number of retries for network-based fallbacks.

    Returns:
        list of list of float: List of 384-dimension vector embeddings.
    """
    if not texts:
        return []

    # ---- 1. Try local model (instant, no network) ----
    local_result = _get_local_embeddings(texts)
    if local_result is not None:
        return local_result

    # ---- 2. Try OpenAI API (paid fallback) ----
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            logger.info(f"Local model unavailable. Trying OpenAI text-embedding-3-large (dim=384) for {len(texts)} texts...")
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": texts,
                "model": "text-embedding-3-large",
                "dimensions": 384
            }
            response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_data = response.json()
                sorted_data = sorted(res_data["data"], key=lambda x: x["index"])
                embeddings = [item["embedding"] for item in sorted_data]
                logger.info(f"Successfully generated {len(embeddings)} embeddings via OpenAI.")
                return embeddings
            else:
                logger.warning(f"OpenAI API returned error: {response.status_code} - {response.text}. Falling back to Hugging Face API...")
        except Exception as e:
            logger.warning(f"OpenAI embedding generation failed: {e}. Falling back to Hugging Face API...")

    # ---- 3. Fallback to Hugging Face Inference API ----
    logger.info("Using Hugging Face Inference API as last resort...")
    hf_token = os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    batch_size = 8
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        payload = {
            "inputs": batch_texts,
            "options": {"wait_for_model": True}
        }

        batch_embeddings = None
        for attempt in range(retries):
            try:
                response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    batch_embeddings = response.json()
                    break
                elif response.status_code == 503:
                    wait_time = response.json().get("estimated_time", 10)
                    logger.warning(f"Hugging Face model is loading. Waiting {wait_time}s (attempt {attempt + 1}/{retries})...")
                    time.sleep(min(wait_time, 15))
                else:
                    logger.error(f"Hugging Face Inference API error {response.status_code}: {response.text}")
                    break
            except Exception as e:
                logger.warning(f"Hugging Face attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    break
                time.sleep(2)

        if not batch_embeddings or not isinstance(batch_embeddings, list):
            raise ValueError(
                "Failed to retrieve embeddings from all providers "
                "(local model, OpenAI, and Hugging Face API)."
            )

        all_embeddings.extend(batch_embeddings)

    logger.info(f"Generated {len(all_embeddings)} embeddings using Hugging Face API fallback.")
    return all_embeddings


def get_embedding(text):
    """
    Generates a vector embedding for a single text string.

    Args:
        text (str): Input text to embed.

    Returns:
        list of float: The 384-dimension vector embedding.
    """
    embeddings = get_embeddings_batch([text])
    if not embeddings:
        raise ValueError("No embedding returned for the input text.")
    return embeddings[0]
