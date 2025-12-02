
import React, { useState, useRef, useEffect } from 'react';
import { Plus, ArrowUp, Headphones, Mic } from 'lucide-react';

interface InputAreaProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  onVoiceModeClick: () => void;
}

const InputArea: React.FC<InputAreaProps> = ({ onSendMessage, isLoading, onVoiceModeClick }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        onSendMessage(input);
        setInput('');
      }
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4">
      <div className={`bg-[#303030] rounded-[26px] p-3 relative shadow-2xl border border-[#424242]/50 transition-colors ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}>
        
        {/* Input Wrapper */}
        <div className="flex flex-col min-h-[52px]">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="W czym mogę pomóc?"
            className="w-full bg-transparent text-[#ececec] placeholder-gray-500 resize-none outline-none text-lg px-2 py-3 max-h-[200px] overflow-y-auto scrollbar-hide disabled:cursor-not-allowed font-light"
            rows={1}
          />
        </div>

        {/* Bottom Toolbar inside the capsule */}
        <div className="flex items-center justify-between mt-2 pl-1">
          
          <div className="flex items-center gap-3">
            {/* Attachment Button - Minimal */}
            <button className="text-gray-500 hover:text-gray-300 transition-colors p-1 rounded-full hover:bg-[#424242]" title="Dodaj plik">
              <Plus size={20} strokeWidth={1.5} />
            </button>
          </div>

          <div className="flex items-center gap-1">
            {/* Voice Mode Trigger (Siri-like) */}
            <button 
                onClick={onVoiceModeClick}
                className="text-gray-400 hover:text-white transition-all p-3 rounded-full hover:bg-[#424242] group"
                title="Tryb Rozmowy"
            >
              <Headphones size={22} strokeWidth={1.5} className="group-hover:stroke-white" />
            </button>

            {/* Standard Mic (Dictation) - Optional, distinct from Voice Mode */}
            {/* <button className="text-gray-400 hover:text-white transition-colors p-3 rounded-full hover:bg-[#424242]">
               <Mic size={20} strokeWidth={1.5} />
            </button> */}

            {/* Send Button */}
            <button 
                onClick={() => { if(input.trim()) { onSendMessage(input); setInput(''); } }}
                disabled={!input.trim()}
                className={`p-2 rounded-full transition-all flex items-center justify-center w-10 h-10 ml-1 ${input.trim() ? 'bg-white text-black hover:opacity-90 shadow-md' : 'bg-[#424242] text-gray-500 cursor-default'}`}
            >
              <ArrowUp size={20} strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>
      
      {/* Footer / Disclaimer - Minimal */}
      <div className="text-center mt-4">
        <p className="text-[10px] uppercase tracking-widest text-gray-600">Grand Hotel Concierge AI</p>
      </div>
    </div>
  );
};

export default InputArea;
