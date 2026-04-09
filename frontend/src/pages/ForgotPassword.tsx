import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, Mail, CheckCircle2 } from 'lucide-react';
import { CyberButton } from '../components/CyberButton';


export const ForgotPassword: React.FC = () => {
    const [email, setEmail] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);
  
    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      setIsSubmitting(true);
  
      // MOCK NETWORK DELAY (1.5 seconds)
      // TODO: Replace with actual authService.requestPasswordReset(email) later
      setTimeout(() => {
        setIsSubmitting(false);
        setIsSubmitted(true);
      }, 1500);
    };
  
    return (
      <div className="min-h-[80vh] flex items-center justify-center py-12">
        <div className="w-full max-w-md bg-crack-dark/80 backdrop-blur-md border border-crack-neon/40 shadow-[0_0_30px_rgba(0,119,182,0.15)] p-8 relative overflow-hidden">
          
          {/* Decorative HUD Elements */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-crack-electric to-transparent opacity-50"></div>
          <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-crack-electric"></div>
          <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-crack-electric"></div>
  
          <div className="text-center mb-8 relative z-10">
            <div className="mx-auto w-16 h-16 bg-crack-deep/50 border border-crack-electric rounded-full flex items-center justify-center mb-4 shadow-[inset_0_0_15px_rgba(0,119,182,0.4)]">
              <ShieldAlert className="w-8 h-8 text-crack-cyan animate-pulse" />
            </div>
            <h1 className="text-2xl font-orbitron font-bold text-white tracking-[0.2em] uppercase">
              Recovery <span className="text-crack-cyan">Protocol</span>
            </h1>
            <p className="text-crack-cyan/60 font-mono text-sm mt-2">
              OVERRIDE ACCESS CREDENTIALS
            </p>
          </div>
  
          {isSubmitted ? (
            // SUCCESS STATE
            <div className="space-y-6 animate-in fade-in duration-500">
              <div className="p-4 border border-green-500/50 bg-green-500/10 flex flex-col items-center text-center gap-3">
                <CheckCircle2 className="w-10 h-10 text-green-500" />
                <p className="text-green-400 font-mono text-sm uppercase">
                  TRANSMISSION SUCCESSFUL
                </p>
                <p className="text-crack-cyan/70 font-mono text-xs">
                  If the identifier <strong className="text-white">{email}</strong> exists in our database, a cryptographic override link has been dispatched to your comms channel.
                </p>
              </div>
              
              <Link to="/login" className="block">
                <CyberButton variant="secondary" className="w-full">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  RETURN TO UPLINK
                </CyberButton>
              </Link>
            </div>
          ) : (
            // FORM STATE
            <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
              <div className="space-y-2">
                <label className="block text-crack-cyan text-xs font-mono tracking-widest uppercase">
                  Sys_Identifier (Email)
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="w-4 h-4 text-crack-cyan/50" />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full bg-crack-deep/50 border border-crack-electric/50 pl-10 pr-4 py-3 text-white font-mono focus:outline-none focus:border-crack-neon focus:shadow-[0_0_10px_rgba(0,119,182,0.3)] transition-all"
                    placeholder="admin@smartcracklens.net"
                  />
                </div>
                <p className="text-[10px] text-crack-cyan/40 font-mono mt-2">
                  Enter your registered email to receive a temporary decryption token.
                </p>
              </div>
  
              <div className="pt-2 flex flex-col gap-4">
                <CyberButton type="submit" isLoading={isSubmitting} className="w-full">
                  TRANSMIT_OVERRIDE_REQUEST
                </CyberButton>
                
                <Link 
                  to="/login" 
                  className="flex items-center justify-center gap-2 text-crack-cyan/50 font-mono text-xs hover:text-crack-neon transition-colors mt-2"
                >
                  <ArrowLeft className="w-3 h-3" />
                  ABORT PROTOCOL
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    );
  };
  
  export default ForgotPassword;

