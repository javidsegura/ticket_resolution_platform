import firebase_admin
from firebase_admin import credentials
import logging 
import os 

logger =	logging.getLogger(__name__)

def initialize_firebase():
	logger.debug("Initializing firebase...")
	use_emulator = os.getenv("USING_FIREBASE_EMULATOR")
	if use_emulator:
		logger.info("Using Firebase Auth Emulator")
		try:
			firebase_admin.get_app()
		except ValueError:
			# Initialize with a dummy project ID for emulator
			firebase_admin.initialize_app(
				options={"projectId": os.getenv("FB_PROJECT_ID")}
			)
	else:
		logger.info("Using Real Firebase Auth")
<<<<<<< HEAD
		credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
		if not credentials_path:
			raise ValueError(
				"FIREBASE_CREDENTIALS_PATH environment variable is required when not using emulator"
			)
		if not os.path.exists(credentials_path):
			raise FileNotFoundError(
				f"Firebase credentials file not found at: {credentials_path}"
			)
		cred = credentials.Certificate(credentials_path)
=======
		cred = credentials.Certificate(
			"./src/url_shortener/core/clients/secret.url-shortener-abadb-firebase-adminsdk-fbsvc-48d38c91f0.json"
		)
>>>>>>> b7bda452db4592a7a86ce23afacd2835aa40031d
		try:
			firebase_admin.get_app()
		except ValueError:
			firebase_admin.initialize_app(cred)