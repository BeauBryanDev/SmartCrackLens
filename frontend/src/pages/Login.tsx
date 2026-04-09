import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Terminal, AlertCircle, KeyRound, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { CyberButton } from '../components/CyberButton';


export const Login : React.FC = ()  => {

    const navigate =  useNavigate();
    const location = useLocation();
    const { login, isLoading, error } =  useAuth();

    const [ email, setEmail ]  = useState('');
    const [ password , setPassword ] =  useState('');
    const [ systemMessage , setSystemMessage ] = useState< string | null> ( null );

    // Catch message passed from Registration Portal 

    useEffect( ()  => {
        
        if ( location.state?.message ) {

            setSystemMessage( location.state.message ) ;
            // Clear state in order to persits on refresh
            window.history.replaceState( {}, document.title ) ; 
            
        }
    }, [ location] );

    const handleSubmit = async ( e: React.FormEvent ) => { 

        e.preventDefault();
        setSystemMessage( null ) ;// clear former system messages on new attempt

        const success = await login( email, password );

        if ( success )  {

            navigate('/dashboard');

        }
    };

    return  (

        <div className="min-h-[80vh] flex items-center justify-center py-12">
      <div className="w-full max-w-md bg-crack-dark/80 backdrop-blur-md border border-crack-neon/40 shadow-[0_0_30px_rgba(0,119,182,0.15)] p-8 relative overflow-hidden">
        
        {/* Decorative HUD Elements */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-crack-cyan to-transparent opacity-50"></div>
        <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-crack-cyan"></div>
        <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-crack-cyan"></div>
        <div className="absolute top-1/2 right-4 transform -translate-y-1/2 w-px h-32 bg-gradient-to-b from-transparent via-crack-cyan/30 to-transparent"></div>

        <div className="text-center mb-8 relative z-10">
          <div className="mx-auto w-16 h-16 bg-crack-deep/50 border border-crack-electric rounded-full flex items-center justify-center mb-4 shadow-[inset_0_0_15px_rgba(0,119,182,0.4)]">
            <KeyRound className="w-8 h-8 text-crack-cyan" />
          </div>
          <h1 className="text-2xl font-orbitron font-bold text-white tracking-[0.2em] uppercase">
            System <span className="text-crack-cyan">Access</span>
          </h1>
          <p className="text-crack-cyan/60 font-mono text-sm mt-2">
            AWAITING OPERATOR CREDENTIALS
          </p>
        </div>

        {/* Success Message (e.g., from Registration) */}
        {systemMessage && (
          <div className="mb-6 p-4 border border-green-500/50 bg-green-500/10 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <p className="text-green-400 font-mono text-sm">{systemMessage}</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 border border-red-500/50 bg-red-500/10 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5 animate-pulse" />
            <p className="text-red-400 font-mono text-sm uppercase">ERROR: {error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
          
          <div className="space-y-2">
            <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
              Sys_Identifier (Email)
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-3 text-white font-mono focus:outline-none focus:border-crack-neon focus:shadow-[0_0_10px_rgba(0,119,182,0.3)] transition-all"
              placeholder="admin@smartcracklens.net"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                Access_Key
              </label>
              <Link 
                to="/forgot-password" 
                className="text-crack-cyan/50 text-[10px] font-mono hover:text-crack-neon transition-colors"
              >
                FORGOTTEN PROTOCOL?
              </Link>
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-crack-deep/50 border border-crack-electric/50 px-4 py-3 text-white font-mono focus:outline-none focus:border-crack-neon focus:shadow-[0_0_10px_rgba(0,119,182,0.3)] transition-all tracking-widest"
              placeholder="••••••••"
            />
          </div>

          <div className="pt-2 flex flex-col gap-4">
            <CyberButton type="submit" isLoading={isLoading} className="w-full">
              AUTHENTICATE
            </CyberButton>
            
            <div className="text-center space-y-2">
              <div>
                <span className="text-crack-cyan/50 font-mono text-xs">NO ASSIGNED CREDENTIALS? </span>
                <Link
                  to="/register"
                  className="text-crack-cyan font-mono text-xs hover:text-crack-neon hover:underline transition-colors ml-1"
                >
                  REQUEST ACCESS
                </Link>
              </div>
              <div>
                <Link
                  to="/"
                  className="text-crack-cyan/40 font-mono text-xs hover:text-crack-neon hover:underline transition-colors"
                >
                  ← RETURN HOME
                </Link>
              </div>
            </div>
          </div>

        </form>
      </div>
    </div>
  );

}

export default Login ; 

