import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { mockAuth, type MockUser } from "./src/services/mockAuth";

// Check if we should use mock auth (when credentials aren't available)
const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH === 'true' || 
                      !import.meta.env.VITE_FIREBASE_API_KEY;

let auth: any;
let isMockMode = false;

if (USE_MOCK_AUTH) {
  // Use mock auth service
  isMockMode = true;
  auth = mockAuth;
} else {
  // Use real Firebase
  const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
    measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
  };
    
  const app = initializeApp(firebaseConfig);
  auth = getAuth(app);
}

export { auth, isMockMode };
export type { MockUser };