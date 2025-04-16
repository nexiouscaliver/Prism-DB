'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Navbar(){
    const router = useRouter();
    
    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };
    
    return(        
        <nav className="w-full py-6 bg-black bg-opacity-10 backdrop-blur-md">
            <div className="max-w-4xl mx-auto flex justify-center items-center space-x-8">                  
                <Link 
                    href="/"
                    onClick={(e) => {
                        e.preventDefault();
                        scrollToSection('home');
                    }}
                    className="text-lg font-medium px-4 py-2 text-white rounded-md hover:bg-purple-600 hover:text-white transition-colors cursor-pointer"
                >
                    Home
                </Link>
                
                <Link 
                    href="/login"
                    onClick={(e) => {
                        e.preventDefault();
                        scrollToSection('login');
                    }}
                    className="text-lg font-medium px-4 py-2 text-white rounded-md hover:bg-purple-600 hover:text-white transition-colors cursor-pointer"
                >
                    Get Started
                </Link>

                <Link 
                    href="/login"
                    onClick={(e) => {
                        e.preventDefault();
                        scrollToSection('features');
                    }}
                    className="text-lg font-medium px-4 py-2 text-white rounded-md hover:bg-purple-600 hover:text-white transition-colors cursor-pointer"
                >
                    Features
                </Link>

                <Link 
                    href="/login"
                    onClick={(e) => {
                        e.preventDefault();
                        scrollToSection('why-us');
                    }}
                    className="text-lg font-medium px-4 py-2 text-white rounded-md hover:bg-purple-600 hover:text-white transition-colors cursor-pointer"
                >
                    Why us
                </Link>

                <Link 
                    href="/login"
                    onClick={(e) => {
                        e.preventDefault();
                        scrollToSection('demo');
                    }}
                    className="text-lg font-medium px-4 py-2 text-white rounded-md hover:bg-purple-600 hover:text-white transition-colors cursor-pointer"
                >
                    Demo
                </Link>
            </div>
        </nav>
    );
}


// "use client";
// import React from "react";
// import { BackgroundGradient } from "../ui/background-gradient";
// import { IconAppWindow } from "@tabler/icons-react";
// import Image from "next/image";

// export function BackgroundGradientDemo() {
//   return (
//     <div>
//       <BackgroundGradient className="rounded-[22px] max-w-sm p-4 sm:p-10 bg-white dark:bg-zinc-900">
//         <Image
//           src={`/jordans.webp`}
//           alt="jordans"
//           height="400"
//           width="400"
//           className="object-contain"
//         />
//         <p className="text-base sm:text-xl text-black mt-4 mb-2 dark:text-neutral-200">
//           Air Jordan 4 Retro Reimagined
//         </p>

//         <p className="text-sm text-neutral-600 dark:text-neutral-400">
//           The Air Jordan 4 Retro Reimagined Bred will release on Saturday,
//           February 17, 2024. Your best opportunity to get these right now is by
//           entering raffles and waiting for the official releases.
//         </p>
//         <button className="rounded-full pl-4 pr-1 py-1 text-white flex items-center space-x-1 bg-black mt-4 text-xs font-bold dark:bg-zinc-800">
//           <span>Buy now </span>
//           <span className="bg-zinc-700 rounded-full text-[0.6rem] px-2 py-0 text-white">
//             $100
//           </span>
//         </button>
//       </BackgroundGradient>
//     </div>
//   );
// }
