import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';


export const PublicLayout: React.FC = () => {

  return (
    
    <div className="min-h-screen bg-crack-dark flex flex-col overflow-hidden selection:bg-crack-neon selection:text-white">
      
      {/* Global Terminal Noise & Gradient Background */}
      <div className="fixed inset-0 pointer-events-none z-[-1] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-crack-deep/30 via-crack-dark to-crack-dark"></div>

      {/* Top Navigation Bar (Dynamically renders Login/Sign Up buttons) */}
      <Header />

      {/* Main Public Content Area */}
      <main className="flex-1 flex flex-col w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 custom-scrollbar overflow-y-auto">
        {/* The Outlet injects Home, Login, or Register components here */}
        <Outlet />
      </main>

      {/* Global Footer */}
      <Footer />
      
    </div>
  );
};