import { useNavigate } from "react-router-dom"
import { signOut } from "@/utils/auth"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"

export default function UserProfile() {
  const navigate = useNavigate()

  const handleUserSignOut = async () => {
    try {
      await signOut()
      navigate("/login")
    } catch (error) {
      console.error("Error signing out:", error)
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={handleUserSignOut}>
      <LogOut className="mr-2 h-4 w-4" />
      Sign out
    </Button>
  )
}