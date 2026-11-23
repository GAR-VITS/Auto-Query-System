/**
 * Web Speech API Integration for Voice Query Input
 * Handles feature detection, en-IN default, silence timeout, and interim transcripts.
 */

export interface SpeechCallbacks {
  onInterim: (text: string) => void;
  onFinal: (text: string) => void;
  onError: (errorMsg: string) => void;
  onStateChange: (listening: boolean) => void;
}

export function isSpeechSupported(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(
    (window as any).SpeechRecognition ||
    (window as any).webkitSpeechRecognition
  );
}

export class SpeechHandler {
  private recognition: any = null;
  private silenceTimer: any = null;
  private isListening = false;
  private callbacks: SpeechCallbacks;
  public lang: string = 'en-IN';

  constructor(callbacks: SpeechCallbacks, lang = 'en-IN') {
    this.callbacks = callbacks;
    this.lang = lang;
    this.init();
  }

  private init() {
    if (!isSpeechSupported()) return;

    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    this.recognition = new SpeechRec();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = this.lang;

    this.recognition.onstart = () => {
      this.isListening = true;
      this.callbacks.onStateChange(true);
      this.resetSilenceTimer();
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.callbacks.onStateChange(false);
      this.clearSilenceTimer();
    };

    this.recognition.onerror = (event: any) => {
      this.clearSilenceTimer();
      let msg = 'Voice recognition error.';
      if (event.error === 'not-allowed') {
        msg = 'Microphone permission denied. Please allow microphone access in your browser.';
      } else if (event.error === 'no-speech') {
        msg = 'No speech was detected. Please try again.';
      }
      this.callbacks.onError(msg);
      this.callbacks.onStateChange(false);
    };

    this.recognition.onresult = (event: any) => {
      this.resetSilenceTimer();
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      if (interim) {
        this.callbacks.onInterim(interim);
      }
      if (final) {
        this.callbacks.onFinal(final.trim());
      }
    };
  }

  private resetSilenceTimer() {
    this.clearSilenceTimer();
    // Auto-stop after 2 seconds of silence
    this.silenceTimer = setTimeout(() => {
      this.stop();
    }, 2000);
  }

  private clearSilenceTimer() {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
  }

  public start() {
    if (!this.recognition) {
      this.callbacks.onError('Web Speech API is not supported in this browser. Please use Chrome or Edge.');
      return;
    }
    try {
      this.recognition.lang = this.lang;
      this.recognition.start();
    } catch (e: any) {
      console.warn('Speech start warning', e);
    }
  }

  public stop() {
    this.clearSilenceTimer();
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (e) {
        // Ignore
      }
    }
  }

  public setLanguage(lang: string) {
    this.lang = lang;
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }
}
