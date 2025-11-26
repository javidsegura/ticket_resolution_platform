// Auth utility functions that work with both mock and real Firebase
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut as firebaseSignOut, type Auth } from 'firebase/auth';
import { auth, isMockMode, type MockUser } from '../../firebase';
import { mockAuth } from '../services/mockAuth';

// Type guard to check if auth is Firebase Auth (not mock)
const isFirebaseAuth = (authInstance: typeof auth): authInstance is Auth => {
  return authInstance !== mockAuth;
};

export const signIn = async (email: string, password: string) => {
  if (isMockMode) {
    // TypeScript knows this is mockAuth here
    return await mockAuth.signInWithEmailAndPassword(email, password);
  } else {
    // Type guard ensures this is Firebase Auth
    if (isFirebaseAuth(auth)) {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return userCredential.user;
    }
    throw new Error('Invalid auth instance');
  }
};

export const signUp = async (email: string, password: string) => {
  if (isMockMode) {
    // TypeScript knows this is mockAuth here
    return await mockAuth.createUserWithEmailAndPassword(email, password);
  } else {
    // Type guard ensures this is Firebase Auth
    if (isFirebaseAuth(auth)) {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      return userCredential.user;
    }
    throw new Error('Invalid auth instance');
  }
};

export const signOut = async () => {
  if (isMockMode) {
    // TypeScript knows this is mockAuth here
    return await mockAuth.signOut();
  } else {
    // Type guard ensures this is Firebase Auth
    if (isFirebaseAuth(auth)) {
      return await firebaseSignOut(auth);
    }
    throw new Error('Invalid auth instance');
  }
};

