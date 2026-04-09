import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Terminal, AlertCircle, ShieldCheck } from 'lucide-react';
import { authService } from '../services/authService';
import { UserCreate }  from  '../types'
import { CyberButton } from '../components/CyberButton';

export const Register: React.FC = () => {
    
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState<UserCreate>({
    email: '',
    username: '',
    password: '',
    confirm_password: '',
    gender: 'male',
    phone_number: '', 
    country: 'Colombia' 
  });


  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // FastAPI backend will handle the 
      // password matching logic and throw a 400/422 if does not match
      await authService.register(formData);
      
      // If successful, redirect to the login portal so they can authenticate
      navigate('/login', { state: { message: 'SYSTEM_INITIALIZED. PLEASE_AUTHENTICATE.' } });
    } catch (err: any) {
      console.error('[HUD_REGISTRY_ERROR]: Payload rejected by server.', err);
      // Extract the detail array or string from FastAPI's validation error
      const errorMessage = err.response?.data?.detail;
      
      if (Array.isArray(errorMessage)) {
        // Pydantic validation errors come as an array
        setError(errorMessage.map(e => e.msg).join(' | '));
      } else if (typeof errorMessage === 'string') {
        // Custom HTTPExceptions
        setError(errorMessage);
      } else {
        setError('REGISTRY_FAILED: Unknown server error.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (

    <div className="min-h-[80vh] flex items-center justify-center py-12">
      <div className="w-full max-w-2xl bg-crack-dark/80 backdrop-blur-md border border-crack-neon/40 shadow-[0_0_30px_rgba(0,119,182,0.15)] p-8 relative overflow-hidden">
        
        {/* Decorative HUD Elements */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-crack-cyan to-transparent opacity-50"></div>
        <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-crack-cyan"></div>
        <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-crack-cyan"></div>

        <div className="text-center mb-8">
          <Terminal className="w-10 h-10 text-crack-cyan mx-auto mb-2 animate-pulse" />
          <h1 className="text-2xl font-orbitron font-bold text-white tracking-[0.2em] uppercase">
            Initialize <span className="text-crack-cyan">System.User</span>
          </h1>
          <p className="text-crack-cyan/60 font-mono text-sm mt-2">
            ENTER CREDENTIALS TO ACCESS IN  SYSREM  </p> 
        </div>

        {error && (
          <div className="mb-6 p-4 border border-red-500/50 bg-red-500/10 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-red-400 font-mono text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* EMAIL */}
            <div className="space-y-2">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Email_Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-2 text-white font-mono focus:outline-none focus:border-crack-neon focus:shadow-[0_0_10px_rgba(0,119,182,0.3)] transition-all"
                placeholder="user@network.com"
              />
            </div>

            {/* USERNAME */}
            <div className="space-y-2">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Sys_Username
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-2 text-white font-mono focus:outline-none focus:border-crack-neon focus:shadow-[0_0_10px_rgba(0,119,182,0.3)] transition-all"
                placeholder="operator_01"
              />
            </div>

            {/* PASSWORD */}
            <div className="space-y-2">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Access_Key
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-2 text-white font-mono focus:outline-none focus:border-crack-neon focus:shadow-[0_0_10px_rgba(0,119,182,0.3)] transition-all"
                placeholder="••••••••"
              />
            </div>

            {/* CONFIRM PASSWORD */}
            <div className="space-y-2">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Verify_Key
              </label>
              <div className="relative">
                <input
                  type="password"
                  name="confirm_password"
                  value={formData.confirm_password}
                  onChange={handleChange}
                  required
                  className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-2 text-white font-mono focus:outline-none focus:border-crack-neon focus:shadow-[0_0_10px_rgba(0,119,182,0.3)] transition-all"
                  placeholder="••••••••"
                />
                {/* Visual feedback icon */}
                {formData.password && formData.confirm_password && formData.password === formData.confirm_password && (
                  <ShieldCheck className="absolute right-3 top-2.5 w-5 h-5 text-green-500/80" />
                )}
              </div>
            </div>

            {/* GENDER */}
            <div className="space-y-2">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Identity_Class
              </label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-2 text-white font-mono focus:outline-none focus:border-crack-neon appearance-none cursor-pointer"
              >
                <option value="male">MALE</option>
                <option value="female">FEMALE</option>
                <option value="other">OTHER</option>
              </select>
            </div>

            {/* PHONE NUMBER */}
            <div className="space-y-2">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Comms_Link
              </label>
              <input
                type="text"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-2 text-white font-mono focus:outline-none focus:border-crack-neon transition-all"
                placeholder="+57 XXXXX..."
              />
            </div>

            {/* COUNTRY */}
            <div className="space-y-2">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Sector_Region
              </label>
              <input
                type="text"
                name="country"
                value={formData.country}
                onChange={handleChange}
                className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-2 text-white font-mono focus:outline-none focus:border-crack-neon transition-all"
                placeholder="Country Name"
              />
            </div>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                to="/"
                className="text-crack-cyan/50 font-mono text-sm hover:text-crack-neon hover:underline transition-colors"
              >
                RETURN HOME
              </Link>
              <Link
                to="/login"
                className="text-crack-cyan/70 font-mono text-sm hover:text-crack-neon hover:underline transition-colors"
              >
                ALREADY REGISTERED? UPLINK HERE.
              </Link>
            </div>

            <CyberButton type="submit" isLoading={isLoading} className="w-full sm:w-auto">
              EXECUTE_INIT
            </CyberButton>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;