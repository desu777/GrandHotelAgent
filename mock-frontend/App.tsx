
import React, { useState, useRef, useEffect, useCallback } from 'react';
import TopBar from './components/TopBar';
import InputArea from './components/InputArea';
import VoiceOverlay from './components/VoiceOverlay';
import { MarkdownMessage } from './components/MarkdownMessage';
import { Message, ChatModel } from './types';
import { sendMessageToGemini, resetSession } from './services/geminiService';
import { logger } from './services/logger';
import { Loader2 } from 'lucide-react';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentModel, setCurrentModel] = useState<string>(ChatModel.CONCIERGE);
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceModeOpen, setIsVoiceModeOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const isLandingPage = messages.length === 0;

  const handleNewSession = () => {
    resetSession();
    setMessages([]);
  };

  // Handler for voice mode responses
  const handleVoiceReply = useCallback((text: string) => {
    const botMsg: Message = {
      id: crypto.randomUUID(),
      role: 'model',
      text,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, botMsg]);
    logger.info('App', 'Voice reply added to messages', { textLength: text.length });
  }, []);

  const handleSendMessage = async (text: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: text,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
        const responseText = await sendMessageToGemini(text);
        const botMsg: Message = {
            id: (Date.now() + 1).toString(),
            role: 'model',
            text: responseText,
            timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
        logger.error('App', 'Unexpected error in handleSendMessage', { error: e });
    } finally {
        setIsLoading(false);
    }
  };

  // Pure Typographic Suggestion Card
  const SuggestionCard = ({ title, subtitle, onClick }: { title: string, subtitle: string, onClick: () => void }) => (
    <button 
      onClick={onClick}
      className="flex flex-col items-start justify-center bg-[#262626] hover:bg-[#303030] p-5 rounded-xl transition-all duration-300 border border-transparent hover:border-[#404040] w-full text-left group h-full"
    >
      <span className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors tracking-wide">{title}</span>
      <span className="text-xs text-gray-500 mt-1 font-light leading-relaxed">{subtitle}</span>
    </button>
  );

  return (
    <div className="flex h-screen w-screen bg-[#212121] text-[#ececec] overflow-hidden relative font-sans selection:bg-white/20">
      
      {/* Voice Mode Overlay */}
      <VoiceOverlay
        isOpen={isVoiceModeOpen}
        onClose={() => setIsVoiceModeOpen(false)}
        onNewMessage={handleVoiceReply}
      />

      {/* Top Navigation */}
      <TopBar currentModel={currentModel} onNewSession={handleNewSession} />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center w-full h-full relative z-10">
        
        {isLandingPage ? (
          <div className="flex-1 flex flex-col items-center justify-center w-full max-w-4xl px-6 animate-in fade-in duration-700">
            {/* The Greeting Text - Ultra Clean */}
            <div className="mb-16 text-center">
                <h1 className="text-3xl font-light text-white mb-4 tracking-tight">
                  Witaj w <span className="font-medium">Grand Hotel</span>.
                </h1>
                <p className="text-lg text-gray-500 font-light max-w-md mx-auto leading-relaxed">
                  Twój osobisty konsjerż jest gotowy, aby spełnić Twoje życzenia.
                </p>
            </div>

            {/* Quick Actions / Suggestions Grid - No Icons, just typography */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-4xl mb-12">
               <SuggestionCard 
                  title="Rezerwacja pobytu" 
                  subtitle="Apartamenty i pokoje"
                  onClick={() => handleSendMessage("Chciałbym sprawdzić dostępność apartamentów na ten weekend.")}
               />
               <SuggestionCard 
                  title="Restauracja Grand" 
                  subtitle="Kolacje i śniadania"
                  onClick={() => handleSendMessage("Chciałbym zarezerwować stolik na kolację.")}
               />
               <SuggestionCard 
                  title="Wellness & SPA" 
                  subtitle="Relaks i zabiegi"
                  onClick={() => handleSendMessage("Jakie zabiegi SPA są dostępne?")}
               />
               <SuggestionCard 
                  title="Concierge" 
                  subtitle="Transport i atrakcje"
                  onClick={() => handleSendMessage("Potrzebuję transportu z lotniska.")}
               />
            </div>
          </div>
        ) : (
          <div className="flex flex-col w-full h-full pt-24 pb-4 px-4 max-w-3xl mx-auto">
             {/* Chat History View */}
             <div className="flex-1 overflow-y-auto space-y-8 scrollbar-hide mb-4 pr-2">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.role === 'model' && (
                             // No icon for bot, just text aligned left, cleaner look
                             <div className="hidden sm:block w-8 flex-shrink-0" /> 
                        )}
                        <div className={`max-w-[85%] text-lg font-light leading-relaxed ${
                            msg.role === 'user'
                            ? 'bg-[#303030] text-gray-100 px-6 py-4 rounded-3xl rounded-tr-sm'
                            : 'text-gray-200 px-0 py-1'
                        }`}>
                            {msg.role === 'model' ? (
                                <MarkdownMessage content={msg.text} />
                            ) : (
                                msg.text
                            )}
                        </div>
                    </div>
                ))}
                
                {/* Thinking / Loading State - Minimal text only */}
                {isLoading && (
                   <div className="flex justify-start w-full animate-in fade-in slide-in-from-bottom-2 duration-300 pl-0 sm:pl-8">
                      <div className="flex items-center gap-3">
                          <Loader2 size={16} className="text-gray-500 animate-spin" />
                          <span className="text-gray-500 text-sm font-light tracking-wide">Przetwarzanie...</span>
                      </div>
                   </div>
                )}
                
                <div ref={messagesEndRef} />
             </div>
          </div>
        )}

        {/* Input Area (Always Visible) */}
        <div className="w-full max-w-4xl px-4 pb-6 z-20">
             <InputArea 
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                onVoiceModeClick={() => setIsVoiceModeOpen(true)}
             />
        </div>

      </main>

    </div>
  );
};

export default App;
