// Auth utility functions that work with both mock and real Firebase
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut as firebaseSignOut } from 'firebase/auth';
import { auth, isMockMode, type MockUser } from '../../firebase';

export const signIn = async (email: string, password: string) => {
  if (isMockMode) {
    return await auth.signInWithEmailAndPassword(email, password);
  } else {
    const userCredential = await signInWithEmailAndPassword(auth as any, email, password);
    return userCredential.user;
  }
};

export const signUp = async (email: string, password: string) => {
  if (isMockMode) {
    return await auth.createUserWithEmailAndPassword(email, password);
  } else {
    const userCredential = await createUserWithEmailAndPassword(auth as any, email, password);
    return userCredential.user;
  }
};

export const signOut = async () => {
  if (isMockMode) {
    return await auth.signOut();
  } else {
    return await firebaseSignOut(auth as any);
  }
};

