import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { getAuthToken, removeAuthToken } from "@/lib/utils";
import { Button } from "./button";

export const Navbar = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  
  // Check if user is logged in on mount and when token changes
  useEffect(() => {
    const token = getAuthToken();
    setIsLoggedIn(!!token);
  }, []);
  
  const handleLogout = () => {
    removeAuthToken();
    setIsLoggedIn(false);
    router.push("/login");
  };
  
  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };
  
  const navItems = [
    { name: "Home", path: "/" },
    { name: "Dashboard", path: "/dashboard", requiresAuth: true },
    { name: "Databases", path: "/databases", requiresAuth: true },
    { name: "Agents", path: "/agents", requiresAuth: true },
  ];
  
  // Filter nav items based on auth status
  const filteredNavItems = navItems.filter(
    (item) => !item.requiresAuth || isLoggedIn
  );
  
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center space-x-4">
          <Link href="/" className="flex items-center space-x-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-8 w-8 text-purple-500"
            >
              <path d="M12 3v19" />
              <path d="M5 8h14" />
              <path d="M15 5V2" />
              <path d="M9 5V2" />
              <path d="M15 22v-3" />
              <path d="M9 22v-3" />
              <path d="M4 5v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2Z" />
            </svg>
            <span className="text-xl font-bold bg-gradient-to-r from-violet-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              PrismDB
            </span>
          </Link>
        </div>
        
        {/* Desktop Navigation */}
        <div className="hidden md:flex md:items-center md:space-x-6">
          <div className="flex space-x-6">
            {filteredNavItems.map((item) => (
              <Link 
                key={item.path} 
                href={item.path}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-white",
                  pathname === item.path
                    ? "text-white"
                    : "text-zinc-400"
                )}
              >
                {item.name}
              </Link>
            ))}
          </div>
          
          <div className="ml-6 flex items-center space-x-2">
            {isLoggedIn ? (
              <Button 
                variant="outline" 
                onClick={handleLogout}
                className="border-white/20 hover:bg-white/10"
              >
                Logout
              </Button>
            ) : (
              <>
                <Link href="/login">
                  <Button 
                    variant="outline" 
                    className="border-white/20 hover:bg-white/10"
                  >
                    Login
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
        
        {/* Mobile menu button */}
        <div className="flex md:hidden">
          <button
            onClick={toggleMenu}
            className="inline-flex items-center justify-center rounded-md p-2 text-zinc-400 hover:bg-zinc-900 hover:text-white focus:outline-none"
          >
            <span className="sr-only">Open main menu</span>
            {isMenuOpen ? (
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            ) : (
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="space-y-1 px-2 pb-3 pt-2 sm:px-3">
            {filteredNavItems.map((item) => (
              <Link
                key={item.path}
                href={item.path}
                className={cn(
                  "block rounded-md px-3 py-2 text-base font-medium",
                  pathname === item.path
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                )}
                onClick={() => setIsMenuOpen(false)}
              >
                {item.name}
              </Link>
            ))}
            
            {isLoggedIn ? (
              <button
                onClick={() => {
                  handleLogout();
                  setIsMenuOpen(false);
                }}
                className="mt-4 block w-full rounded-md bg-zinc-900 px-3 py-2 text-base font-medium text-white hover:bg-zinc-800"
              >
                Logout
              </button>
            ) : (
              <Link
                href="/login"
                className="mt-4 block rounded-md bg-zinc-900 px-3 py-2 text-center text-base font-medium text-white hover:bg-zinc-800"
                onClick={() => setIsMenuOpen(false)}
              >
                Login
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}; 