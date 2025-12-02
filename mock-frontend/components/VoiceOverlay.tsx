
import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';

interface VoiceOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

const VoiceOverlay: React.FC<VoiceOverlayProps> = ({ isOpen, onClose }) => {
  const [phase, setPhase] = useState<'listening' | 'processing' | 'speaking'>('listening');
  
  // Simulate phase changes for the demo
  useEffect(() => {
    if (!isOpen) return;
    
    const interval = setInterval(() => {
      setPhase(prev => {
        if (prev === 'listening') return 'processing';
        if (prev === 'processing') return 'speaking';
        return 'listening';
      });
    }, 4000);

    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-black/90 backdrop-blur-xl animate-in fade-in duration-500">
      
      {/* Close Button */}
      <button 
        onClick={onClose}
        className="absolute top-6 right-6 p-4 text-white/50 hover:text-white transition-colors rounded-full hover:bg-white/10"
      >
        <X size={24} strokeWidth={1.5} />
      </button>

      {/* Main Orb Animation */}
      <div className="relative flex items-center justify-center h-64 w-64">
        {/* Core */}
        <div className={`absolute w-32 h-32 bg-white rounded-full blur-2xl transition-all duration-1000 ${
            phase === 'listening' ? 'opacity-20 scale-100' : 
            phase === 'processing' ? 'opacity-40 scale-90' : 'opacity-60 scale-110'
        }`} />
        
        {/* Inner Glow */}
        <div className={`absolute w-48 h-48 rounded-full border border-white/10 transition-all duration-1000 ${
             phase === 'speaking' ? 'scale-125 opacity-100 border-white/30' : 'scale-100 opacity-20'
        }`} />

        {/* Outer Ripple */}
        <div className={`absolute w-full h-full rounded-full border border-white/5 transition-all duration-[2000ms] ${
             phase === 'listening' ? 'scale-110 opacity-30 animate-pulse' : 'scale-100 opacity-0'
        }`} />
        
        {/* Center Indicator */}
        <div className="z-10 text-white font-light text-2xl tracking-widest uppercase opacity-80 mix-blend-difference">
            {phase === 'listening' && "Słucham"}
            {phase === 'processing' && "Myślę"}
            {phase === 'speaking' && "Mówię"}
        </div>
      </div>

      {/* Subtext */}
      <div className="mt-12 text-center space-y-2">
        <h2 className="text-2xl font-light text-white">Grand Concierge Live</h2>
        <p className="text-white/40 font-light text-sm">Mów swobodnie, jestem tutaj.</p>
      </div>

      {/* Bottom Controls */}
      <div className="absolute bottom-12 flex gap-8">
         <div className="h-16 w-16 rounded-full bg-white flex items-center justify-center cursor-pointer hover:scale-105 transition-transform">
            <div className="w-4 h-4 bg-black rounded-sm" onClick={onClose}></div>
         </div>
      </div>
    </div>
  );
};

export default VoiceOverlay;
