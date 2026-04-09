import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { Footer } from '../components/Footer';


export const HudLayout: React.FC = () => {

  return (
    
    <div className="min-h-screen bg-crack-dark flex flex-col overflow-hidden selection:bg-crack-neon selection:text-white">
      {/* Global Terminal Noise Background */}
      <div className="fixed inset-0 pointer-events-none z-[-1] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-crack-deep/20 via-crack-dark to-crack-dark"></div>

      {/* Top Navigation Bar */}
      <Header />

      {/* Main Interface Area */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Left Navigation Panel */}
        <Sidebar />

        {/* Dynamic Content Viewport */}
        <div className="flex-1 flex flex-col relative overflow-hidden">
          
          {/* Main scrollable area for specific pages (Dashboard, Images, etc.) */}
          <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6 lg:p-8 custom-scrollbar">
            {/* The Outlet acts as a placeholder for the matched route component */}
            <Outlet />
          </main>

          {/* Footer remains at the bottom of the content viewport */}
          <Footer />
        </div>

      </div>
    </div>
  );
};