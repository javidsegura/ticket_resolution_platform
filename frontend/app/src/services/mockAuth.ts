// Mock Firebase Auth Service
// This simulates Firebase Auth behavior for development when credentials aren't available

export interface MockUser {
  uid: string
  email: string | null
  displayName: string | null
  emailVerified: boolean
}

type AuthStateListener = (user: MockUser | null) => void

class MockAuthService {
  private currentUser: MockUser | null = null
  private listeners: Set<AuthStateListener> = new Set()
  private storageKey = 'mock_auth_user'

  constructor() {
    // Load persisted user from localStorage on init
    const stored = localStorage.getItem(this.storageKey)
    if (stored) {
      try {
        this.currentUser = JSON.parse(stored)
        this.notifyListeners()
      } catch (e) {
        localStorage.removeItem(this.storageKey)
      }
    }
  }

  private notifyListeners() {
    this.listeners.forEach(listener => {
      listener(this.currentUser)
    })
  }

  onAuthStateChanged(callback: (user: MockUser | null) => void): () => void {
    this.listeners.add(callback)
    // Immediately call with current user
    callback(this.currentUser)
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback)
    }
  }

  async signInWithEmailAndPassword(email: string, password: string): Promise<MockUser> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // In real app, this would validate with Firebase
    // For mock, we accept any email/password combination
    if (!email || !password) {
      throw new Error('Email and password are required')
    }

    const user: MockUser = {
      uid: `mock_${Date.now()}`,
      email,
      displayName: email.split('@')[0],
      emailVerified: true
    }

    this.currentUser = user
    localStorage.setItem(this.storageKey, JSON.stringify(user))
    this.notifyListeners()
    
    return user
  }

  async createUserWithEmailAndPassword(email: string, password: string): Promise<MockUser> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (!email || !password) {
      throw new Error('Email and password are required')
    }

    if (password.length < 6) {
      throw new Error('Password should be at least 6 characters')
    }

    const user: MockUser = {
      uid: `mock_${Date.now()}`,
      email,
      displayName: email.split('@')[0],
      emailVerified: false
    }

    this.currentUser = user
    localStorage.setItem(this.storageKey, JSON.stringify(user))
    this.notifyListeners()
    
    return user
  }

  async signOut(): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 200))
    this.currentUser = null
    localStorage.removeItem(this.storageKey)
    this.notifyListeners()
  }

  getCurrentUser(): MockUser | null {
    return this.currentUser
  }
}

export const mockAuth = new MockAuthService()

