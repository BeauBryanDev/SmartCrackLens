import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Terminal, User, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { CyberButton } from './CyberButton';


export const Header: React.FC = () => {

  const { isAuthenticated, user, logout } = useAuth();

  const navigate = useNavigate();

  const handleLogout = () => {
    
    logout();
    navigate('/');
  };

  return (

    <header className="w-full border-b border-crack-neon/30 bg-crack-dark/80 backdrop-blur-md sticky top-0 z-50 shadow-hud">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* LOGO & BRAND */}
        <Link to={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-2 group">
          <Terminal className="w-6 h-6 text-crack-cyan group-hover:animate-pulse" />
          <span className="text-xl font-orbitron font-bold text-white tracking-widest">
            SMART<span className="text-crack-cyan">CRACK</span>LENS
          </span>
        </Link>

        {/* DYNAMIC NAVIGATION */}
        <nav className="flex items-center gap-4">
          {isAuthenticated ? (
            // COMMAND CENTER ZONE (Logged In)
            <>
              <div className="hidden md:flex items-center gap-2 mr-4 border border-crack-electric bg-crack-deep/50 px-4 py-1 rounded-sm shadow-[inset_0_0_8px_rgba(0,119,182,0.5)]">
                <User className="w-4 h-4 text-crack-neon" />
                <span className="text-sm font-mono text-crack-cyan tracking-wider">
                  SYS_USER: <strong className="text-white drop-shadow-[0_0_5px_rgba(144,224,239,0.8)]">{user?.username || 'UNKNOWN'}</strong>
                </span>
              </div>
              
              <Link to="/dashboard">
                <CyberButton variant="ghost" className="text-sm">HUD</CyberButton>
              </Link>
              
              <CyberButton variant="ghost" onClick={handleLogout} className="text-sm group">
                <LogOut className="w-4 h-4 group-hover:text-red-400 transition-colors" />
              </CyberButton>
            </>
          ) : (
            // PUBLIC ZONE (Not Logged In)
            <>
              <Link to="/login">
                <CyberButton variant="ghost">LOG IN</CyberButton>
              </Link>
              <Link to="/register">
                <CyberButton variant="primary">INITIALIZE</CyberButton>
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};