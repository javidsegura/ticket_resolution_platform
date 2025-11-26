import { Routes, Route, Navigate } from "react-router-dom"

import AppLayout from "./layout/app_layout"
import ProtectedRoute from "./components/ProtectedRoute"

import Landing from "./pages/Landing"
import Dashboard from "./pages/Dashboard"
import TicketDetail from "./pages/TicketDetail"
import ClusterDetail from "./pages/ClusterDetail"
import Login from "./pages/Login"
import Signup from "./pages/Signup"
import FirebaseTest from "./pages/FirebaseTest"

function App(){
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/firebase-test" element={<FirebaseTest />} />
      
      {/* Protected routes with layout */}
      <Route element={<AppLayout />}>
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/ticket/:id" 
          element={
            <ProtectedRoute>
              <TicketDetail />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/cluster/:id" 
          element={
            <ProtectedRoute>
              <ClusterDetail />
            </ProtectedRoute>
          } 
        />
      </Route>
      <Route path="*" element={<p>404 error</p>} />
    </Routes>
  )
}


export default App
