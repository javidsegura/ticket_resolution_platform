import { useState, useEffect } from "react";
import { onAuthStateChanged, type User, type Auth } from "firebase/auth";
import { auth, isMockMode, type MockUser } from "../../firebase";
import { mockAuth } from "../services/mockAuth";

// Unified user type that works with both mock and real Firebase
type AuthUser = User | MockUser | null;

// Type guard to check if auth is Firebase Auth (not mock)
const isFirebaseAuth = (authInstance: typeof auth): authInstance is Auth => {
  return authInstance !== mockAuth;
};

export const useAuth = () => {
  const [user, setUser] = useState<AuthUser>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode) {
      // Use mock auth - TypeScript knows this is mockAuth
      const unsubscribe = mockAuth.onAuthStateChanged(
        (mockUser: MockUser | null) => {
          setUser(mockUser);
          setLoading(false);
        },
      );

      return () => unsubscribe();
    } else {
      // Use real Firebase - Type guard ensures this is Firebase Auth
      if (isFirebaseAuth(auth)) {
        const unsubscribe = onAuthStateChanged(
          auth,
          (firebaseUser: User | null) => {
            setUser(firebaseUser);
            setLoading(false);
          },
        );

        return () => unsubscribe();
      }
      // Fallback if auth is somehow invalid
      setLoading(false);
    }
  }, []);

  return [user, loading] as const;
};
