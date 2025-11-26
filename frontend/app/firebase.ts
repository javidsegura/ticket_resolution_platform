import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { mockAuth, type MockUser } from "./src/services/mockAuth";

const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH === 'true' || 
                      !import.meta.env.apiKey;

let auth: any;
let isMockMode = false;

if (USE_MOCK_AUTH) {
  isMockMode = true;
  auth = mockAuth;
} else {
  const firebaseConfig = {
    apiKey: import.meta.env.apiKey,
    authDomain: import.meta.env.authDomain,
    projectId: import.meta.env.projectId,
    storageBucket: import.meta.env.storageBucket,
    messagingSenderId: import.meta.env.messagingSenderId,
    appId: import.meta.env.appId,
    measurementId: import.meta.env.measurementId,
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