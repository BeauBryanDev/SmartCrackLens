import React from 'react';
import { Loader2 } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';


export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface CyberButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  isLoading?: boolean;
}

export const CyberButton: React.FC<CyberButtonProps> = ({ 

  children, 
  variant = 'primary', 
  isLoading = false, 
  className, 
  disabled,
  ...props 
}) => {
  const baseStyles = "relative px-6 py-2 uppercase tracking-widest font-bold transition-all duration-300 flex items-center justify-center gap-2 overflow-hidden";
  
  const variants = {
    primary: "bg-crack-dark border border-crack-cyan text-crack-cyan hover:bg-crack-cyan hover:text-crack-dark shadow-neon-border",
    secondary: "bg-transparent border border-crack-electric text-crack-electric hover:border-crack-neon hover:text-crack-neon",
    danger: "bg-transparent border border-red-500 text-red-500 hover:bg-red-500 hover:text-white shadow-[0_0_10px_rgba(239,68,68,0.5)]",
    ghost: "bg-transparent text-crack-cyan hover:bg-crack-deep/50 hover:text-white border border-transparent"
  };

  return (
    <button 
      className={cn(
        baseStyles, 
        variants[variant], 
        (disabled || isLoading) && "opacity-50 cursor-not-allowed hover:bg-transparent hover:text-crack-cyan",
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {/* Scanline overlay effect */}
      <div className="absolute inset-0 bg-scanline opacity-20 pointer-events-none"></div>
      
      {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
      <span className="relative z-10">{children}</span>
    </button>
  );
};