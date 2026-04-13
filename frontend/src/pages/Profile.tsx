import React, { useState } from 'react';
import {
  User as UserIcon,
  Mail,
  Shield,
  Globe,
  Settings,
  LogOut,
  Fingerprint,
  Calendar,
  Activity
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { CyberButton } from '../components/CyberButton';

export const Profile: React.FC = () => {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="border-b border-crack-neon/30 pb-4">
        <h1 className="text-2xl font-orbitron font-bold text-white tracking-widest uppercase">
          System <span className="text-crack-cyan">Operator</span> Profile
        </h1>
        <p className="text-crack-cyan/60 font-mono text-xs mt-1">
          USER_IDENTITY_VERIFICATION // ACCESS_CORE_V1.2
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left Column: Avatar & Quick Actions */}
        <div className="md:col-span-4 space-y-6">
          <div className="border border-crack-electric/50 bg-crack-dark/80 p-6 flex flex-col items-center text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>

            <div className="w-32 h-32 rounded-full border-2 border-crack-cyan p-1 relative mb-4">
              <div className="w-full h-full rounded-full bg-crack-electric/20 flex items-center justify-center">
                <UserIcon className="w-16 h-16 text-crack-cyan" />
              </div>
              <div className="absolute -bottom-2 -right-2 bg-crack-cyan p-2 rounded-full shadow-[0_0_10px_cyan]">
                <Shield className="w-4 h-4 text-crack-dark" />
              </div>
            </div>

            <h2 className="text-xl font-orbitron text-white tracking-wider truncate w-full">
              {user?.username}
            </h2>
            <p className="text-crack-cyan/50 font-mono text-xs uppercase tracking-[0.2em] mb-6">
              {user?.is_admin ? 'Level_0_Administrator' : 'Standard_Inspector'}
            </p>

            <div className="w-full space-y-3">
              <CyberButton onClick={() => setIsEditing(!isEditing)} className="w-full justify-center">
                <Settings className="w-4 h-4" />
                {isEditing ? 'SYNC_CHANGES' : 'EDIT_INTERFACE'}
              </CyberButton>
              <CyberButton variant="ghost" onClick={logout} className="w-full justify-center border-red-500/50 text-red-500 hover:bg-red-500/10 hover:text-red-400">
                <LogOut className="w-4 h-4" />
                TERMINATE_SESSION
              </CyberButton>
            </div>
          </div>

          <div className="border border-crack-electric/30 bg-crack-deep/40 p-5 space-y-4 font-mono">
            <h4 className="text-[10px] text-crack-cyan/40 tracking-[0.3em] uppercase">Uplink_Stats</h4>
            <div className="flex justify-between items-end border-b border-crack-electric/10 pb-2">
              <span className="text-xs text-crack-cyan/60 uppercase">Session_Live</span>
              <span className="text-sm text-crack-neon">ACTIVE</span>
            </div>
            <div className="flex justify-between items-end border-b border-crack-electric/10 pb-2">
              <span className="text-xs text-crack-cyan/60 uppercase">Access_Tokens</span>
              <span className="text-sm text-crack-neon">ENCRYPTED</span>
            </div>
          </div>
        </div>

        {/* Right Column: Detailed Info */}
        <div className="md:col-span-8 space-y-6">
          <div className="border border-crack-electric/50 bg-crack-dark/60 p-8 relative">
            <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
            <h3 className="text-sm font-mono text-crack-cyan tracking-widest mb-8 flex items-center gap-2 uppercase">
              <Fingerprint className="w-4 h-4" /> Identity_Matrix
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
              <ProfileField
                icon={UserIcon}
                label="Public_Designation"
                value={user?.username || 'GUEST_USER'}
                editable={isEditing}
              />
              <ProfileField
                icon={Mail}
                label="Comm_Channel"
                value={user?.email || 'OFFLINE'}
                editable={false}
              />
              <ProfileField
                icon={Globe}
                label="Geographic_Origin"
                value={user?.country || 'GLOBAL_NODE'}
                editable={isEditing}
              />
              <ProfileField
                icon={Shield}
                label="Permission_Class"
                value={user?.is_admin ? 'ROOT_ACCESS' : 'USER_ACCESS'}
                editable={false}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 font-mono">
            <div className="border border-crack-electric/30 bg-black/40 p-6">
              <div className="flex items-center gap-3 text-crack-cyan mb-4">
                <Calendar className="w-5 h-5" />
                <span className="text-[10px] tracking-[0.2em] uppercase">Enrollment_Date</span>
              </div>
              <p className="text-lg text-white font-orbitron tracking-widest">
                APRIL_11_2026
              </p>
            </div>
            <div className="border border-crack-electric/30 bg-black/40 p-6">
              <div className="flex items-center gap-3 text-crack-cyan mb-4">
                <Activity className="w-5 h-5" />
                <span className="text-[10px] tracking-[0.2em] uppercase">Core_Health</span>
              </div>
              <p className="text-lg text-crack-neon font-orbitron tracking-widest">
                OPTIMAL
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProfileField = ({ icon: Icon, label, value, editable }: any) => (
  <div className="space-y-2">
    <div className="flex items-center gap-2 text-[10px] font-mono text-crack-cyan/40 tracking-widest uppercase">
      <Icon className="w-3 h-3" />
      {label}
    </div>
    {editable ? (
      <input
        type="text"
        defaultValue={value}
        className="w-full bg-crack-dark border border-crack-cyan/50 p-2 text-white font-mono text-sm focus:border-crack-neon outline-none shadow-[0_0_5px_rgba(0,180,216,0.1)]"
      />
    ) : (
      <div className="p-2 border border-crack-electric/20 bg-black/20 text-white font-mono text-sm tracking-wide">
        {value}
      </div>
    )}
  </div>
);

export default Profile;
