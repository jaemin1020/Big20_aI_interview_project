import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
ai_worker_path = os.path.join(root_dir, "ai-worker")
sys.path.insert(0, ai_worker_path)

try:
    import db
    print(f"✅ Imported db from: {db.__file__}")
    print(f"✅ Functions: {dir(db)}")
    if 'update_transcript_sentiment' in dir(db):
        print("✅ update_transcript_sentiment exists!")
    else:
        print("❌ update_transcript_sentiment MISSING!")
except Exception as e:
    print(f"❌ Failed to import db: {e}")
