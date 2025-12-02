import React, { useEffect, useState, useRef, useCallback } from 'react';
import { X, Mic, MicOff, ChevronDown } from 'lucide-react';
import { sendVoiceToAgent } from '../services/geminiService';
import { logger } from '../services/logger';

interface VoiceOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onNewMessage?: (text: string) => void;
}

type Phase = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

const VoiceOverlay: React.FC<VoiceOverlayProps> = ({
  isOpen,
  onClose,
  onNewMessage,
}) => {
  const [phase, setPhase] = useState<Phase>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  // Cleanup function
  const cleanup = useCallback(() => {
    // Stop recording
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;

    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Stop audio playback
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current = null;
    }

    // Revoke audio URL
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    audioChunksRef.current = [];
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setErrorMessage(null);
      setPhase('idle');

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Determine best supported MIME type
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/mp4';

      logger.debug('voice-overlay', 'Starting recording', { mimeType });

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        logger.info('voice-overlay', 'Recording stopped', {
          blobSize: audioBlob.size,
          mimeType,
        });

        if (audioBlob.size < 1000) {
          logger.warn('voice-overlay', 'Recording too short, skipping');
          setPhase('listening');
          startRecording();
          return;
        }

        // Process the audio
        setPhase('processing');
        try {
          const response = await sendVoiceToAgent(audioBlob);

          // Notify parent about new message
          if (onNewMessage && response.text) {
            onNewMessage(response.text);
          }

          // Play audio response
          if (response.audioUrl) {
            audioUrlRef.current = response.audioUrl;
            setPhase('speaking');

            const audio = new Audio(response.audioUrl);
            audioElementRef.current = audio;

            audio.onended = () => {
              logger.debug('voice-overlay', 'Audio playback ended');
              // Restart listening after playback
              setPhase('listening');
              startRecording();
            };

            audio.onerror = () => {
              logger.error('voice-overlay', 'Audio playback error');
              setPhase('listening');
              startRecording();
            };

            audio.play().catch((e) => {
              logger.error('voice-overlay', 'Failed to play audio', {
                error: e.message,
              });
              setPhase('listening');
              startRecording();
            });
          } else {
            // No audio response - go back to listening
            logger.info('voice-overlay', 'No audio in response, resuming listening');
            setPhase('listening');
            startRecording();
          }
        } catch (e) {
          logger.error('voice-overlay', 'Voice API error', {
            error: e instanceof Error ? e.message : String(e),
          });
          setErrorMessage('Wystąpił błąd połączenia. Spróbuj ponownie.');
          setPhase('error');
        }
      };

      mediaRecorder.start();
      setPhase('listening');
    } catch (e) {
      logger.error('voice-overlay', 'Failed to start recording', {
        error: e instanceof Error ? e.message : String(e),
      });
      setErrorMessage(
        'Nie udało się uzyskać dostępu do mikrofonu. Sprawdź uprawnienia.'
      );
      setPhase('error');
    }
  }, [onNewMessage]);

  // Stop recording and send
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      // Stop stream tracks to release microphone
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    }
  }, []);

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (streamRef.current) {
      const audioTrack = streamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = isMuted;
        setIsMuted(!isMuted);
      }
    }
  }, [isMuted]);

  // Handle close
  const handleClose = useCallback(() => {
    cleanup();
    setPhase('idle');
    setErrorMessage(null);
    onClose();
  }, [cleanup, onClose]);

  // Effect: Start recording when overlay opens
  useEffect(() => {
    if (isOpen) {
      startRecording();
    }
    return () => {
      cleanup();
    };
  }, [isOpen, startRecording, cleanup]);

  if (!isOpen) return null;

  // Generate bars for the visualizer
  const bars = Array.from({ length: 24 });

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-between bg-[#050505]/95 backdrop-blur-3xl animate-in fade-in duration-500">
      {/* CSS for specific waveform animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        @keyframes waveform-listen {
          0%, 100% { height: 10%; opacity: 0.3; }
          50% { height: 40%; opacity: 0.8; }
        }
        @keyframes waveform-speak {
          0%, 100% { height: 20%; transform: scaleY(1); }
          50% { height: 80%; transform: scaleY(1.2); }
        }
        @keyframes pulse-ring {
            0% { transform: scale(0.8); opacity: 0; }
            50% { opacity: 0.5; }
            100% { transform: scale(1.5); opacity: 0; }
        }
        .bar-listen {
            animation: waveform-listen 1.2s ease-in-out infinite;
        }
        .bar-speak {
            animation: waveform-speak 0.8s ease-in-out infinite;
        }
      `}</style>

      {/* Top Bar - Drag Indicator & Close */}
      <div className="w-full pt-12 px-6 flex justify-between items-start">
        <div className="flex-1 flex justify-center">
          <button
            onClick={handleClose}
            className="w-12 h-1 bg-white/20 rounded-full hover:bg-white/40 transition-colors"
          />
        </div>
        <button
          onClick={handleClose}
          className="absolute right-6 top-10 p-2 text-white/30 hover:text-white transition-colors rounded-full hover:bg-white/10"
        >
          <ChevronDown size={32} strokeWidth={1} />
        </button>
      </div>

      {/* CENTER VISUALIZER */}
      <div className="flex-1 flex flex-col items-center justify-center w-full max-w-2xl relative">
        {/* Glow effect behind */}
        <div
          className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-white/5 blur-[100px] rounded-full transition-all duration-1000
            ${phase === 'speaking' ? 'bg-white/10 scale-150' : 'scale-100'}
        `}
        />

        {/* The Waveform Container */}
        <div className="flex items-center justify-center gap-[6px] h-64 w-full">
          {phase === 'processing' ? (
            // Processing State: Rotating Orb / Loading
            <div className="relative">
              <div className="w-16 h-16 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              </div>
            </div>
          ) : phase === 'error' ? (
            // Error State
            <div className="text-red-400 text-center px-8">
              <div className="text-4xl mb-4">⚠️</div>
              <p>{errorMessage}</p>
            </div>
          ) : phase === 'idle' ? (
            // Idle State
            <div className="text-white/50 text-center">
              <div className="w-12 h-12 border-2 border-white/30 border-t-white/60 rounded-full animate-spin mx-auto mb-4" />
              <p>Uruchamiam mikrofon...</p>
            </div>
          ) : (
            // Listening or Speaking State: Bars
            bars.map((_, i) => {
              // Calculate delay for wave effect
              const center = bars.length / 2;
              const dist = Math.abs(i - center);
              const delay = phase === 'speaking' ? dist * 0.05 : Math.random();

              return (
                <div
                  key={i}
                  className={`w-1.5 bg-white rounded-full transition-all duration-500 shadow-[0_0_15px_rgba(255,255,255,0.3)]
                    ${phase === 'listening' ? 'bar-listen' : 'bar-speak'}
                    ${isMuted && phase === 'listening' ? 'opacity-30' : ''}
                  `}
                  style={{
                    animationDelay: `${delay}s`,
                    height: phase === 'listening' ? '15%' : '30%',
                  }}
                />
              );
            })
          )}
        </div>

        {/* Status Text */}
        <div className="mt-8 text-center h-12">
          <span
            className={`text-2xl font-light tracking-wide text-white transition-opacity duration-500 ${phase === 'processing' ? 'animate-pulse' : ''}`}
          >
            {phase === 'idle' && 'Przygotowuję...'}
            {phase === 'listening' && (isMuted ? 'Wyciszony' : 'Słucham...')}
            {phase === 'processing' && 'Analizuję...'}
            {phase === 'speaking' && 'Grand Concierge'}
            {phase === 'error' && 'Błąd'}
          </span>
        </div>
      </div>

      {/* BOTTOM CONTROLS */}
      <div className="w-full pb-16 px-8 flex justify-center items-center gap-10">
        {/* Mute Button */}
        <button
          onClick={toggleMute}
          disabled={phase !== 'listening'}
          className={`p-6 rounded-full transition-all duration-300 border backdrop-blur-md group
            ${isMuted ? 'bg-white text-black border-white' : 'bg-white/5 border-white/10 text-white hover:bg-white/10'}
            ${phase !== 'listening' ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {isMuted ? (
            <MicOff size={28} strokeWidth={1.5} />
          ) : (
            <Mic size={28} strokeWidth={1.5} />
          )}
        </button>

        {/* Stop/Send Button (replaces End Call when listening) */}
        {phase === 'listening' ? (
          <button
            onClick={stopRecording}
            className="p-6 rounded-full bg-green-500/20 border border-green-500/50 text-green-400 hover:bg-green-500/30 hover:scale-105 transition-all duration-300 backdrop-blur-md"
            title="Wyślij nagranie"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        ) : null}

        {/* End Call Button */}
        <button
          onClick={handleClose}
          className="p-6 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 hover:scale-105 transition-all duration-300 backdrop-blur-md"
        >
          <X size={28} strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
};

export default VoiceOverlay;
