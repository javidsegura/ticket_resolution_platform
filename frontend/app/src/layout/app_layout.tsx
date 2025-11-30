import { Outlet, Link } from "react-router-dom";
import { Ticket } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import UserProfile from "@/components/userProfile";

export default function AppLayout() {
  const [user] = useAuth();

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <header className="bg-white shadow-md py-4 px-6 flex items-center justify-between">
        <div className="h-max">
          <Link
            to="/dashboard"
            className="text-xl font-bold text-gray-800 tracking-wide flex items-center gap-2"
          >
            <Ticket className="h-6 w-6" />
            Ticket Resolution Platform
          </Link>
        </div>
        <nav className="flex items-center gap-4">
          <Link
            to="/dashboard"
            className="text-gray-600 hover:text-primary-600 transition-colors duration-200"
          >
            Dashboard
          </Link>
          {user && (
            <div className="flex items-center gap-3 pl-4 border-l border-gray-300">
              <span className="text-sm text-gray-600">
                {(user as any).email || (user as any).displayName || "User"}
              </span>
              <UserProfile />
            </div>
          )}
        </nav>
      </header>
      <main className="flex-grow p-8">
        <Outlet />
      </main>
      <footer className="bg-gray-800 text-white text-center p-4">
        <p>Ticket Resolution Platform © 2024</p>
      </footer>
    </div>
  );
}
