/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Firebase config variables (from .env.dev - simple names as requested)
  readonly apiKey: string
  readonly authDomain: string
  readonly projectId: string
  readonly storageBucket: string
  readonly messagingSenderId: string
  readonly appId: string
  readonly measurementId?: string
  // Other variables
  readonly VITE_USE_MOCK_AUTH?: string
  readonly VITE_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

