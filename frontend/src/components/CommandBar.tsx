import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Mic, MicOff, Square } from 'lucide-react';
import { SpeechHandler, isSpeechSupported } from '../lib/speech';
import { useQueryStore } from '../store/query';

interface CommandBarProps {
  onSend: (text: string, isVoice?: boolean) => void;
  isStreaming: boolean;
  docked?: boolean;
  onCancel?: () => void;
  placeholder?: string;
}

export const CommandBar: React.FC<CommandBarProps> = ({
  onSend,
  isStreaming,
  docked = false,
  onCancel,
  placeholder = 'Ask a question or propose an action...',
}) => {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [speechError, setSpeechError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const speechRef = useRef<SpeechHandler | null>(null);
  const { cancelRequest } = useQueryStore();

  const handleStop = () => {
    if (onCancel) onCancel();
    else cancelRequest();
  };

  useEffect(() => {
    // Initialize speech recognition
    if (isSpeechSupported()) {
      speechRef.current = new SpeechHandler({
        onInterim: (text) => setInterimText(text),
        onFinal: (text) => {
          setInput((prev) => (prev ? `${prev} ${text}` : text));
          setInterimText('');
        },
        onError: (err) => {
          setSpeechError(err);
          setTimeout(() => setSpeechError(null), 4000);
        },
        onStateChange: (listening) => setIsListening(listening),
      });
    }

    // Keyboard shortcut '/' to focus
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== textareaRef.current) {
        e.preventDefault();
        textareaRef.current?.focus();
      }
      if (e.key === 'Escape' && isStreaming) {
        handleStop();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      speechRef.current?.stop();
    };
  }, [isStreaming]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming) return;
    const textToSend = input.trim();
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    onSend(textToSend, isListening);
    if (isListening) {
      speechRef.current?.stop();
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  const toggleVoice = () => {
    if (!speechRef.current) return;
    if (isListening) {
      speechRef.current.stop();
    } else {
      speechRef.current.start();
    }
  };

  return (
    <div
      className={`w-full transition-all duration-200 ${
        docked
          ? 'max-w-[720px] mx-auto'
          : 'max-w-[720px] mx-auto'
      }`}
    >
      <div className="relative rounded-2xl border border-line bg-surface p-2 shadow-sm focus-within:border-accent transition-colors">
        <form onSubmit={handleSubmit} className="flex flex-col">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleTextareaInput}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder={
              isListening ? 'Listening (speak in English or Indian accents)...' : placeholder
            }
            disabled={isStreaming}
            className="w-full resize-none bg-transparent px-3 py-2 text-sm text-ink placeholder:text-ink-3 focus:outline-none font-sans leading-relaxed"
          />

          {interimText && (
            <div className="px-3 pb-2 text-xs italic text-ink-3 font-sans">
              "{interimText}"
            </div>
          )}

          <div className="flex items-center justify-between border-t border-line/60 pt-2 px-1">
            {/* Left helper info */}
            <div className="flex items-center gap-2">
              <span className="hidden sm:inline-block font-mono text-[10px] uppercase text-ink-3">
                Press Enter ↵ to ask
              </span>
              {speechError && (
                <span className="text-[11px] text-err font-mono">{speechError}</span>
              )}
            </div>

            {/* Right controls: Mic & Submit */}
            <div className="flex items-center gap-1.5">
              {isSpeechSupported() && (
                <button
                  type="button"
                  onClick={toggleVoice}
                  disabled={isStreaming}
                  className={`p-1.5 rounded-full transition-all cursor-pointer ${
                    isListening
                      ? 'bg-err text-white animate-pulse'
                      : 'text-ink-3 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5'
                  }`}
                  title={isListening ? 'Stop listening' : 'Speak query'}
                >
                  {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
              )}

              {isStreaming ? (
                <button
                  type="button"
                  onClick={handleStop}
                  className="p-1.5 rounded-full bg-black/10 dark:bg-white/10 text-ink hover:bg-black/20 dark:hover:bg-white/20 transition-all cursor-pointer"
                  title="Stop query stream"
                >
                  <Square className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleSubmit()}
                  disabled={!input.trim()}
                  className="p-1.5 rounded-full bg-accent text-white hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
                  title="Send query"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
