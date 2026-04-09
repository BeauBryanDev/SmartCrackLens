import React from 'react';


export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-crack-neon/20 bg-crack-dark py-6 mt-auto">
      <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="text-crack-cyan/60 font-mono text-xs">
          <p> SYSTEM.STATUS: OPTIMAL</p>
          <p> ENGINE: ONNX_CV_CORE_v1</p>
        </div>
        
        <div className="text-center md:text-right font-orbitron text-xs text-crack-cyan/40">
          <p>© 2026 SMARTCRACKLENS PROJECT.</p>
          <p className="tracking-widest mt-1">ALL SYSTEMS NOMINAL.</p>
        </div>
      </div>
    </footer>
  );
};