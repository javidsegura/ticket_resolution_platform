import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { auth, isMockMode } from "../../firebase"
import { signIn, signUp, signOut } from "@/utils/auth"
import { AlertCircle, CheckCircle, XCircle } from "lucide-react"

export default function FirebaseTest() {
  const [testEmail] = useState("test@example.com")
  const [testPassword] = useState("test123456")
  const [testResults, setTestResults] = useState<Array<{ name: string; status: "success" | "error" | "pending"; message: string }>>([])
  const [loading, setLoading] = useState(false)

  const addResult = (name: string, status: "success" | "error" | "pending", message: string) => {
    setTestResults(prev => [...prev, { name, status, message }])
  }

  const testFirebaseConnection = async () => {
    setTestResults([])
    setLoading(true)

    // Test 1: Check if we're in mock mode
    addResult(
      "Mode Check",
      "pending",
      isMockMode ? "Using MOCK authentication" : "Using REAL Firebase"
    )

    // Test 2: Check auth object
    if (!auth) {
      addResult("Auth Object", "error", "Auth object is null/undefined")
      setLoading(false)
      return
    }
    addResult("Auth Object", "success", "Auth object exists")

    // Test 3: Check environment variables
    const envCheck = {
      apiKey: import.meta.env.VITE_FIREBASE_API_KEY ? "✓" : "✗",
      authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN ? "✓" : "✗",
      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID ? "✓" : "✗",
    }
    addResult(
      "Environment Variables",
      Object.values(envCheck).includes("✗") ? "error" : "success",
      `API Key: ${envCheck.apiKey}, Auth Domain: ${envCheck.authDomain}, Project ID: ${envCheck.projectId}`
    )

    // Test 4: Try to sign up (this will test Firebase connection)
    try {
      addResult("Sign Up Test", "pending", `Attempting to create user: ${testEmail}`)
      const user = await signUp(testEmail, testPassword)
      addResult("Sign Up Test", "success", `User created: ${user.email || "Email not available"}`)
      
      // Test 5: Try to sign out
      try {
        await signOut()
        addResult("Sign Out Test", "success", "Successfully signed out")
      } catch (err: any) {
        addResult("Sign Out Test", "error", err.message || "Failed to sign out")
      }

      // Test 6: Try to sign in
      try {
        addResult("Sign In Test", "pending", `Attempting to sign in: ${testEmail}`)
        const signedInUser = await signIn(testEmail, testPassword)
        addResult("Sign In Test", "success", `Signed in: ${signedInUser.email || "Email not available"}`)
      } catch (err: any) {
        addResult("Sign In Test", "error", err.message || "Failed to sign in")
      }

    } catch (err: any) {
      addResult("Sign Up Test", "error", err.message || "Failed to create user")
    }

    setLoading(false)
  }

  const getStatusIcon = (status: "success" | "error" | "pending") => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />
      case "pending":
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
    }
  }

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>Firebase Connection Test</CardTitle>
          <CardDescription>
            Test your Firebase authentication setup and connection
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-gray-50 rounded-md">
            <p className="text-sm font-semibold mb-2">Current Mode:</p>
            <p className={isMockMode ? "text-yellow-600" : "text-green-600"}>
              {isMockMode ? "🔶 MOCK Authentication (Firebase not configured or failed)" : "✅ REAL Firebase Authentication"}
            </p>
          </div>

          <Button 
            onClick={testFirebaseConnection} 
            disabled={loading}
            className="w-full"
          >
            {loading ? "Running Tests..." : "Run Firebase Tests"}
          </Button>

          {testResults.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-semibold">Test Results:</h3>
              {testResults.map((result, index) => (
                <div 
                  key={index}
                  className={`p-3 rounded-md border ${
                    result.status === "success" 
                      ? "bg-green-50 border-green-200" 
                      : result.status === "error"
                      ? "bg-red-50 border-red-200"
                      : "bg-yellow-50 border-yellow-200"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {getStatusIcon(result.status)}
                    <div className="flex-1">
                      <p className="font-medium text-sm">{result.name}</p>
                      <p className="text-xs text-gray-600 mt-1">{result.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="p-4 bg-blue-50 rounded-md border border-blue-200">
            <p className="text-sm font-semibold mb-2">Debug Info:</p>
            <pre className="text-xs overflow-auto">
              {JSON.stringify({
                isMockMode,
                hasAuth: !!auth,
                env: {
                  VITE_FIREBASE_API_KEY: import.meta.env.VITE_FIREBASE_API_KEY 
                    ? `${import.meta.env.VITE_FIREBASE_API_KEY.substring(0, 10)}...` 
                    : "NOT SET",
                  VITE_FIREBASE_AUTH_DOMAIN: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "NOT SET",
                  VITE_FIREBASE_PROJECT_ID: import.meta.env.VITE_FIREBASE_PROJECT_ID || "NOT SET",
                  VITE_USE_MOCK_AUTH: import.meta.env.VITE_USE_MOCK_AUTH || "NOT SET",
                }
              }, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

