import { Outlet } from "react-router-dom"
import { Link } from "react-router-dom"


export default function AppLayout() {

  const links = [
    { path: "/", name: "Homepage" },
    { path: "/AboutUs", name: "About Us"}
  ];

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <header className="bg-white shadow-md py-4 px-6 flex items-center justify-between">
        <div className="h-max">
          <Link to="/" className="text-xl font-bold text-gray-800 tracking-wide">
            URL SHORTENER
          </Link>
        </div>
        <nav className="flex gap-4">
          {links.map((item, index) => (
            <Link
              key={index}
              to={item.path}
              className="text-gray-600 hover:text-blue-500 transition-colors duration-200"
            >
              {item.name}
            </Link>
          ))}
        </nav>
      </header>
      <main className="flex-grow p-8">
        <Outlet />
      </main>
      <footer className="bg-gray-800 text-white text-center p-4">
        <p> Made by Javier Domínguez Segura</p>
      </footer>
    </div>
  );
}