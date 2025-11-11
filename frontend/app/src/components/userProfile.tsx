import { signOut } from "firebase/auth"
import { auth } from "../../firebase"


export default function UserProfile(){

      const handleUserSignOut = async () => {
            await signOut(auth)
      }
      return ( 
            <>
            <button className="btn-secondary" onClick={handleUserSignOut}> Sign out </button>
            
            </>
      )
}