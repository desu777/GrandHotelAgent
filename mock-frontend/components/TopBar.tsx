
import React from 'react';
import { Menu } from 'lucide-react';
import { ChatModel } from '../types';

interface TopBarProps {
  currentModel: string;
}

const TopBar: React.FC<TopBarProps> = ({ currentModel }) => {
  return (
    <div className="fixed top-0 left-0 w-full p-4 flex justify-between items-center z-50 pointer-events-none">
      
      {/* Left - Minimal branding */}
      <div className="pointer-events-auto opacity-70 hover:opacity-100 transition-opacity">
        <span className="text-gray-400 font-light text-sm tracking-widest uppercase">Grand Concierge</span>
      </div>

      {/* Right - Menu only */}
      <div className="flex items-center gap-4 pointer-events-auto">
         <button className="text-gray-400 hover:text-white transition-colors">
            <Menu size={20} strokeWidth={1.5} />
         </button>
      </div>
    </div>
  );
};

export default TopBar;
