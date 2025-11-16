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
		cred = credentials.Certificate(
			"./src/url_shortener/core/clients/secret.url-shortener-abadb-firebase-adminsdk-fbsvc-48d38c91f0.json"
		)
		try:
			firebase_admin.get_app()
		except ValueError:
			firebase_admin.initialize_app(cred)
	
