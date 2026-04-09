import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Image as ImageIcon, 
  Cpu, 
  Target, 
  MapPin, 
  UserCircle 
} from 'lucide-react';
import { cn } from './CyberButton'; // Assuming we put the cn utility here or in a utils file


const NAV_LINKS = [

  { name: 'DASHBOARD', path: '/dashboard', icon: LayoutDashboard },
  { name: 'RAW_IMAGES', path: '/images', icon: ImageIcon },
  { name: 'INFERENCE_CORE', path: '/inference', icon: Cpu },
  { name: 'DETECTIONS', path: '/detections', icon: Target },
  { name: 'LOCATIONS', path: '/locations', icon: MapPin },
  { name: 'SYS_PROFILE', path: '/me', icon: UserCircle },

];

export const Sidebar: React.FC = () => {

  return (

    <aside className="w-64 flex-shrink-0 hidden md:flex flex-col border-r border-crack-neon/30 bg-crack-dark/95 backdrop-blur-md relative z-40">
      {/* Decorative Top Grid */}
      <div className="h-12 border-b border-crack-neon/20 flex items-center px-4">
        <span className="text-xs font-mono text-crack-cyan/50 tracking-widest">
          SYS.NAV_MODULE_v1.0
        </span>
      </div>

      <nav className="flex-1 py-6 px-3 flex flex-col gap-2 overflow-y-auto">
        
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.name}
            to={link.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-4 py-3 rounded-sm font-mono tracking-wider transition-all duration-300 relative group overflow-hidden",
                isActive 
                  ? "bg-crack-electric/40 text-white border-l-2 border-crack-neon shadow-[inset_4px_0_10px_rgba(0,119,182,0.3)]" 
                  : "text-crack-cyan/70 hover:bg-crack-deep/50 hover:text-crack-cyan"
              )
            }
          >
            {({ isActive }) => (
              <>
                {/* Hover scanline effect */}
                <div className="absolute inset-0 bg-scanline opacity-0 group-hover:opacity-20 transition-opacity pointer-events-none"></div>
                
                <link.icon className={cn(
                  "w-5 h-5 z-10 transition-transform duration-300",
                  isActive ? "text-crack-neon scale-110" : "group-hover:scale-110"
                )} />
                <span className="text-sm z-10">{link.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Decorative Bottom Module */}
      <div className="p-4 border-t border-crack-neon/20">
        <div className="bg-crack-dark border border-crack-cyan/30 p-3 flex flex-col gap-1 shadow-[inset_0_0_10px_rgba(0,119,182,0.1)]">
          <span className="text-[10px] font-mono text-crack-cyan/60 uppercase">Uplink Status</span>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-crack-cyan animate-pulse"></span>
            <span className="text-xs font-orbitron text-crack-cyan tracking-widest">CONNECTED</span>
          </div>
        </div>
      </div>
    </aside>
  );
};