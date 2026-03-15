import firebase_admin
from firebase_admin import credentials
import os

# Ensure the service account key is correctly placed in the backend directory
SERVICE_ACCOUNT_KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "serviceAccountKey.json")

def init_firebase():
    """Initializes the Firebase Admin SDK."""
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)
            print("Successfully initialized Firebase Admin SDK.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")

# Call init on import so the app is always ready
init_firebase()
