/// <reference path="./env.d.ts" />
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { mockAuth, type MockUser } from "./src/services/mockAuth";

const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH === 'true' || 
                      !import.meta.env.VITE_FIREBASE_API_KEY;

let auth: any;
let isMockMode = false;

if (USE_MOCK_AUTH) {
  isMockMode = true;
  auth = mockAuth;
} else {
  const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
    measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
  };

  // Validate required config values - fall back to mock if invalid
  if (!firebaseConfig.apiKey || !firebaseConfig.authDomain || !firebaseConfig.projectId) {
    isMockMode = true;
    auth = mockAuth;
  } else if (firebaseConfig.apiKey.includes("your-") || firebaseConfig.apiKey.trim() === "") {
    // Check for placeholder values
    isMockMode = true;
    auth = mockAuth;
  } else {
    // Try to initialize Firebase
    try {
      const app = initializeApp(firebaseConfig);
      auth = getAuth(app);
    } catch (error: any) {
      // If Firebase initialization fails, fall back to mock instead of crashing
      console.error("Firebase initialization error, falling back to mock auth:", error.message);
      isMockMode = true;
      auth = mockAuth;
    }
  }
}

export { auth, isMockMode };
export type { MockUser };