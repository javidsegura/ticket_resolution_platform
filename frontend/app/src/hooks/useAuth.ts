import { useState, useEffect } from 'react';
import { onAuthStateChanged, type User } from 'firebase/auth';
import { auth, isMockMode, type MockUser } from "../../firebase"

// Unified user type that works with both mock and real Firebase
type AuthUser = User | MockUser | null;

export const useAuth = () => {
  const [user, setUser] = useState<AuthUser>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode) {
      // Use mock auth
      const unsubscribe = auth.onAuthStateChanged((mockUser: MockUser | null) => {
        setUser(mockUser);
        setLoading(false);
      });

      return () => unsubscribe();
    } else {
      // Use real Firebase
      const unsubscribe = onAuthStateChanged(auth as any, (firebaseUser: User | null) => {
        setUser(firebaseUser);
        setLoading(false);
      });

      return () => unsubscribe();
    }
  }, []);

  return [user, loading] as const;
};