import React, { useEffect, useState } from 'react';
import {
  User as UserIcon,
  Mail, Shield, Globe, Settings,
  LogOut, Fingerprint, Calendar,
  Activity, Phone, Lock, Eye, EyeOff,
  Save, X, CheckCircle, AlertTriangle,
  Crown, Users,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useAuthStore } from '../store/useAuthStore';
import { userService } from '../services/userService';
import { authService } from '../services/authService';
import { CyberButton } from '../components/CyberButton';
import type { User } from '../types';

/* ─── helpers ────────────────────────────────────────────────────── */
const fmtDate = (iso?: string | null) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  }).toUpperCase().replace(/ /g, '_').replace(',', '');
};


interface ToastMsg {
  type: 'success' | 'error';
  text: string;
}

const Toast: React.FC<{ msg: ToastMsg; onClose: () => void }> = ({ msg, onClose }) => (
  <div
    className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3 border font-mono text-sm tracking-wide shadow-lg
      animate-in slide-in-from-right-8 duration-300
      ${msg.type === 'success'
        ? 'border-green-500/60 bg-green-950/80 text-green-300 shadow-green-500/20'
        : 'border-red-500/60 bg-red-950/80 text-red-300 shadow-red-500/20'
      }`}
  >
    {msg.type === 'success'
      ? <CheckCircle className="w-4 h-4 shrink-0" />
      : <AlertTriangle className="w-4 h-4 shrink-0" />}
    {msg.text}
    <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100 transition">
      <X className="w-3.5 h-3.5" />
    </button>
  </div>
);

/* main component*/
export const Profile: React.FC = () => {
  const { user, logout } = useAuth();
  const setUser = useAuthStore((s) => s.setUser);

  /* live profile from API */
  const [profile, setProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  /* edit mode state */
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    username: '',
    gender: '',
    phone_number: '',
    country: '',
  });
  const [saving, setSaving] = useState(false);

  /* ── change password state ── */
  const [showPwPanel, setShowPwPanel] = useState(false);
  const [pwForm, setPwForm] = useState({ current: '', newPw: '', confirm: '' });
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [changingPw, setChangingPw] = useState(false);

  /* ── toast ── */
  const [toast, setToast] = useState<ToastMsg | null>(null);
  const flash = (t: ToastMsg) => {
    setToast(t);
    setTimeout(() => setToast(null), 4000);
  };

  /* ── fetch profile on mount ── */
  useEffect(() => {
    (async () => {
      try {
        const me = await userService.getMe();
        setProfile(me);
        setUser(me);                       // keep store in sync
      } catch (err) {
        console.error('[HUD_PROFILE]: Failed to fetch user profile', err);
        // fall back to store user if API fails
        if (user) setProfile(user);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── derived ── */
  const p = profile ?? user;
  const isAdmin = p?.is_admin ?? false;

  /* ── enter / exit edit mode ── */
  const startEditing = () => {
    setEditForm({
      username: p?.username ?? '',
      gender: p?.gender ?? '',
      phone_number: p?.phone_number ?? '',
      country: p?.country ?? '',
    });
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setIsEditing(false);
  };

  /* ── save profile ── */
  const handleSaveProfile = async () => {
    if (!p) return;
    setSaving(true);
    try {
      const updated = await userService.Update(p.id, {
        username: editForm.username || undefined,
        gender: editForm.gender || undefined,
        phone_number: editForm.phone_number || undefined,
        country: editForm.country || undefined,
      });
      setProfile(updated);
      setUser(updated);
      setIsEditing(false);
      flash({ type: 'success', text: 'PROFILE_SYNCED_SUCCESSFULLY' });
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'PROFILE_UPDATE_FAILED';
      flash({ type: 'error', text: typeof detail === 'string' ? detail : JSON.stringify(detail) });
    } finally {
      setSaving(false);
    }
  };

  /* ── change password ── */
  const handleChangePassword = async () => {
    if (pwForm.newPw !== pwForm.confirm) {
      flash({ type: 'error', text: 'PASSWORDS_DO_NOT_MATCH' });
      return;
    }
    if (pwForm.newPw.length < 8) {
      flash({ type: 'error', text: 'PASSWORD_MIN_8_CHARS' });
      return;
    }
    setChangingPw(true);
    try {
      await authService.changePassword(pwForm.current, pwForm.newPw);
      flash({ type: 'success', text: 'PASSWORD_CHANGED_SUCCESSFULLY' });
      setPwForm({ current: '', newPw: '', confirm: '' });
      setShowPwPanel(false);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'PASSWORD_CHANGE_FAILED';
      flash({ type: 'error', text: typeof detail === 'string' ? detail : JSON.stringify(detail) });
    } finally {
      setChangingPw(false);
    }
  };

  /* ── loading skeleton ── */
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-16 flex items-center justify-center gap-3 text-crack-cyan/60 font-mono text-sm tracking-widest">
        <Activity className="w-5 h-5 animate-pulse" />
        LOADING_IDENTITY_MATRIX...
      </div>
    );
  }

  /* ── main render ── */
  return (
    <>
      {toast && <Toast msg={toast} onClose={() => setToast(null)} />}

      <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Header */}
        <div className="border-b border-crack-neon/30 pb-4">
          <h1 className="text-2xl font-orbitron font-bold text-white tracking-widest uppercase">
            System <span className="text-crack-cyan">Operator</span> Profile
          </h1>
          <p className="text-crack-cyan/60 font-mono text-xs mt-1">
            USER_IDENTITY_VERIFICATION // ACCESS_CORE_V1.2
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* ─── Left Column: Avatar & Quick Actions ─── */}
          <div className="md:col-span-4 space-y-6">
            <div className="border border-crack-electric/50 bg-crack-dark/80 p-6 flex flex-col items-center text-center relative overflow-hidden">
              <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>

              {/* Avatar */}
              <div className="w-32 h-32 rounded-full border-2 border-crack-cyan p-1 relative mb-4">
                <div className="w-full h-full rounded-full bg-crack-electric/20 flex items-center justify-center">
                  <UserIcon className="w-16 h-16 text-crack-cyan" />
                </div>
                <div className="absolute -bottom-2 -right-2 bg-crack-cyan p-2 rounded-full shadow-[0_0_10px_cyan]">
                  {isAdmin
                    ? <Crown className="w-4 h-4 text-crack-dark" />
                    : <Shield className="w-4 h-4 text-crack-dark" />}
                </div>
              </div>

              <h2 className="text-xl font-orbitron text-white tracking-wider truncate w-full">
                {p?.username ?? 'UNKNOWN'}
              </h2>
              <p className="text-crack-cyan/50 font-mono text-xs uppercase tracking-[0.2em] mb-6">
                {isAdmin ? 'Level_0_Administrator' : 'Standard_Inspector'}
              </p>

              {/* Action buttons */}
              <div className="w-full space-y-3">
                {!isEditing ? (
                  <CyberButton onClick={startEditing} className="w-full justify-center">
                    <Settings className="w-4 h-4" />
                    EDIT_INTERFACE
                  </CyberButton>
                ) : (
                  <div className="flex gap-2 w-full">
                    <CyberButton onClick={handleSaveProfile} isLoading={saving} className="flex-1 justify-center">
                      <Save className="w-4 h-4" />
                      SYNC
                    </CyberButton>
                    <CyberButton variant="ghost" onClick={cancelEditing} className="justify-center border-crack-electric/40">
                      <X className="w-4 h-4" />
                    </CyberButton>
                  </div>
                )}

                <CyberButton
                  variant="secondary"
                  onClick={() => setShowPwPanel(!showPwPanel)}
                  className="w-full justify-center"
                >
                  <Lock className="w-4 h-4" />
                  {showPwPanel ? 'CLOSE_VAULT' : 'CHANGE_PASSKEY'}
                </CyberButton>

                <CyberButton
                  variant="ghost"
                  onClick={logout}
                  className="w-full justify-center border-red-500/50 text-red-500 hover:bg-red-500/10 hover:text-red-400"
                >
                  <LogOut className="w-4 h-4" />
                  TERMINATE_SESSION
                </CyberButton>
              </div>
            </div>

            {/* Session stats panel */}
            <div className="border border-crack-electric/30 bg-crack-deep/40 p-5 space-y-4 font-mono">
              <h4 className="text-[10px] text-crack-cyan/40 tracking-[0.3em] uppercase">Uplink_Stats</h4>
              <div className="flex justify-between items-end border-b border-crack-electric/10 pb-2">
                <span className="text-xs text-crack-cyan/60 uppercase">Session_Live</span>
                <span className="text-sm text-crack-neon">ACTIVE</span>
              </div>
              <div className="flex justify-between items-end border-b border-crack-electric/10 pb-2">
                <span className="text-xs text-crack-cyan/60 uppercase">Access_Level</span>
                <span className={`text-sm ${isAdmin ? 'text-amber-400' : 'text-crack-neon'}`}>
                  {isAdmin ? 'ROOT' : 'USER'}
                </span>
              </div>
              <div className="flex justify-between items-end border-b border-crack-electric/10 pb-2">
                <span className="text-xs text-crack-cyan/60 uppercase">Account_Status</span>
                <span className={`text-sm ${p?.is_active ? 'text-crack-neon' : 'text-red-500'}`}>
                  {p?.is_active ? 'ONLINE' : 'DISABLED'}
                </span>
              </div>
              <div className="flex justify-between items-end border-b border-crack-electric/10 pb-2">
                <span className="text-xs text-crack-cyan/60 uppercase">Access_Tokens</span>
                <span className="text-sm text-crack-neon">ENCRYPTED</span>
              </div>
            </div>
          </div>

          {/* ─── Right Column ─── */}
          <div className="md:col-span-8 space-y-6">
            {/* Identity Matrix */}
            <div className="border border-crack-electric/50 bg-crack-dark/60 p-8 relative">
              <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
              <h3 className="text-sm font-mono text-crack-cyan tracking-widest mb-8 flex items-center gap-2 uppercase">
                <Fingerprint className="w-4 h-4" /> Identity_Matrix
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <ProfileField
                  icon={UserIcon}
                  label="Public_Designation"
                  value={isEditing ? editForm.username : (p?.username || 'GUEST_USER')}
                  editable={isEditing}
                  onChange={(v) => setEditForm({ ...editForm, username: v })}
                />
                <ProfileField
                  icon={Mail}
                  label="Comm_Channel"
                  value={p?.email || 'OFFLINE'}
                  editable={false}
                />
                <ProfileField
                  icon={Globe}
                  label="Geographic_Origin"
                  value={isEditing ? (editForm.country || '') : (p?.country || '—')}
                  editable={isEditing}
                  onChange={(v) => setEditForm({ ...editForm, country: v })}
                />
                <ProfileField
                  icon={Shield}
                  label="Permission_Class"
                  value={isAdmin ? 'ROOT_ACCESS' : 'USER_ACCESS'}
                  editable={false}
                />
                <ProfileField
                  icon={Phone}
                  label="Comm_Frequency"
                  value={isEditing ? (editForm.phone_number || '') : (p?.phone_number || '—')}
                  editable={isEditing}
                  onChange={(v) => setEditForm({ ...editForm, phone_number: v })}
                />
                <ProfileField
                  icon={Users}
                  label="Bio_Classification"
                  value={isEditing ? (editForm.gender || '') : (p?.gender || '—')}
                  editable={isEditing}
                  onChange={(v) => setEditForm({ ...editForm, gender: v })}
                  placeholder="male | female | other"
                />
              </div>
            </div>

            {/* Enrollment & Health */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 font-mono">
              <div className="border border-crack-electric/30 bg-black/40 p-6">
                <div className="flex items-center gap-3 text-crack-cyan mb-4">
                  <Calendar className="w-5 h-5" />
                  <span className="text-[10px] tracking-[0.2em] uppercase">Enrollment_Date</span>
                </div>
                <p className="text-lg text-white font-orbitron tracking-widest">
                  {fmtDate(p?.created_at)}
                </p>
              </div>
              <div className="border border-crack-electric/30 bg-black/40 p-6">
                <div className="flex items-center gap-3 text-crack-cyan mb-4">
                  <Activity className="w-5 h-5" />
                  <span className="text-[10px] tracking-[0.2em] uppercase">Last_Update</span>
                </div>
                <p className="text-lg text-white font-orbitron tracking-widest">
                  {fmtDate(p?.updated_at)}
                </p>
              </div>
            </div>

            {/* ─── Change Password Panel ─── */}
            {showPwPanel && (
              <div className="border border-amber-500/40 bg-crack-dark/80 p-8 relative animate-in slide-in-from-top-4 duration-300">
                <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
                <h3 className="text-sm font-mono text-amber-400 tracking-widest mb-6 flex items-center gap-2 uppercase">
                  <Lock className="w-4 h-4" /> Password_Vault
                </h3>

                <div className="space-y-5">
                  {/* Current password */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-mono text-crack-cyan/40 tracking-widest uppercase">
                      Current_Passkey
                    </label>
                    <div className="relative">
                      <input
                        type={showCurrent ? 'text' : 'password'}
                        value={pwForm.current}
                        onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })}
                        className="w-full bg-crack-dark border border-crack-electric/40 p-2.5 pr-10 text-white font-mono text-sm focus:border-amber-400 outline-none transition"
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrent(!showCurrent)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-crack-cyan/40 hover:text-crack-cyan transition"
                      >
                        {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* New password */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-mono text-crack-cyan/40 tracking-widest uppercase">
                      New_Passkey
                    </label>
                    <div className="relative">
                      <input
                        type={showNew ? 'text' : 'password'}
                        value={pwForm.newPw}
                        onChange={(e) => setPwForm({ ...pwForm, newPw: e.target.value })}
                        className="w-full bg-crack-dark border border-crack-electric/40 p-2.5 pr-10 text-white font-mono text-sm focus:border-amber-400 outline-none transition"
                        placeholder="Min 8 chars, 1 upper, 1 number, 1 symbol"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNew(!showNew)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-crack-cyan/40 hover:text-crack-cyan transition"
                      >
                        {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Confirm password */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-mono text-crack-cyan/40 tracking-widest uppercase">
                      Confirm_Passkey
                    </label>
                    <input
                      type="password"
                      value={pwForm.confirm}
                      onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
                      className="w-full bg-crack-dark border border-crack-electric/40 p-2.5 text-white font-mono text-sm focus:border-amber-400 outline-none transition"
                      placeholder="Re-enter new passkey"
                    />
                    {pwForm.confirm && pwForm.newPw !== pwForm.confirm && (
                      <p className="text-[10px] text-red-400 font-mono tracking-wider">
                        ⚠ PASSKEY_MISMATCH
                      </p>
                    )}
                  </div>

                  <CyberButton
                    onClick={handleChangePassword}
                    isLoading={changingPw}
                    disabled={!pwForm.current || !pwForm.newPw || !pwForm.confirm}
                    className="w-full justify-center mt-2"
                  >
                    <Lock className="w-4 h-4" />
                    EXECUTE_PASSKEY_ROTATION
                  </CyberButton>
                </div>
              </div>
            )}

            {/* Admin badge */}
            {isAdmin && (
              <div className="border border-amber-500/30 bg-amber-950/20 p-5 flex items-center gap-4 font-mono animate-in fade-in duration-500">
                <Crown className="w-6 h-6 text-amber-400 shrink-0" />
                <div>
                  <p className="text-amber-400 text-xs uppercase tracking-[0.2em]">
                    Administrator_Privileges_Active
                  </p>
                  <p className="text-amber-400/50 text-[10px] mt-1 tracking-wider">
                    Full system access • User management • Data control
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

/* ─── reusable field component ───────────────────────────────────── */
interface ProfileFieldProps {
  icon: React.FC<React.SVGProps<SVGSVGElement> & { className?: string }>;
  label: string;
  value: string;
  editable: boolean;
  onChange?: (v: string) => void;
  placeholder?: string;
}

const ProfileField: React.FC<ProfileFieldProps> = ({
  icon: Icon,
  label,
  value,
  editable,
  onChange,
  placeholder,
}) => (
  <div className="space-y-2">
    <div className="flex items-center gap-2 text-[10px] font-mono text-crack-cyan/40 tracking-widest uppercase">
      <Icon className="w-3 h-3" />
      {label}
    </div>
    {editable ? (
      <input
        type="text"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-crack-dark border border-crack-cyan/50 p-2 text-white font-mono text-sm focus:border-crack-neon outline-none shadow-[0_0_5px_rgba(0,180,216,0.1)] transition"
      />
    ) : (
      <div className="p-2 border border-crack-electric/20 bg-black/20 text-white font-mono text-sm tracking-wide">
        {value}
      </div>
    )}
  </div>
);

export default Profile;
