import os
import sys

# Add the project root to sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from dotenv import load_dotenv
load_dotenv()

from LegalAI.services.qdrant_service import get_qdrant_client, COLLECTION_NAME

def verify():
    print("--- QDRANT VERIFICATION DIAGNOSTIC ---")
    client = get_qdrant_client()
    if not client:
        print("ERROR: Could not connect to Qdrant.")
        return

    try:
        collections_response = client.get_collections()
        collections = [c.name for c in collections_response.collections]
        
        if COLLECTION_NAME not in collections:
            print(f"Collection '{COLLECTION_NAME}' does not exist.")
            return

        print(f"Collection Name: {COLLECTION_NAME}")
        
        info = client.get_collection(collection_name=COLLECTION_NAME)
        print(f"Vectors Config Size: {info.config.params.vectors.size}")
        print(f"Distance Metric: {info.config.params.vectors.distance}")
        
        count_result = client.count(collection_name=COLLECTION_NAME)
        print(f"Total Chunks/Vectors: {count_result.count}")

        # Fetch one sample to check payload
        if count_result.count > 0:
            sample, _ = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1,
                with_payload=True
            )
            if sample:
                payload = sample[0].payload
                print("\nSample Payload Structure:")
                for k, v in payload.items():
                    print(f"  - {k}: {type(v).__name__}")
        
        print("--- VERIFICATION COMPLETE ---")

    except Exception as e:
        print(f"Failed during verification: {e}")

if __name__ == "__main__":
    verify()
