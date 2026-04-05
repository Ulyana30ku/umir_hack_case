import { useState, useRef, useEffect } from 'react';

function VoiceInput({ onTranscript, disabled = false }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);
  const interimRef = useRef('');

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech Recognition API не поддерживается');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setIsListening(true);
      interimRef.current = '';
    };

    recognition.onresult = (event) => {
      let interim = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPart = event.results[i][0].transcript;
        
        if (event.results[i].isFinal) {
          setTranscript((prev) => prev + transcriptPart);
        } else {
          interim += transcriptPart;
        }
      }

      interimRef.current = interim;
    };

    recognition.onerror = (event) => {
      console.error('Ошибка распознавания:', event.error);
    };

    recognition.onend = () => {
      setIsListening(false);
      const fullTranscript = transcript + interimRef.current;
      if (fullTranscript.trim()) {
        onTranscript(fullTranscript);
      }
      setTranscript('');
      interimRef.current = '';
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognition) {
        recognition.abort();
      }
    };
  }, [transcript, onTranscript]);

  const handleVoiceClick = () => {
    if (!recognitionRef.current) {
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      setTranscript('');
      interimRef.current = '';
      recognitionRef.current.start();
    }
  };

  return (
    <button
      type="button"
      className={`voice-button ${isListening ? 'listening' : ''}`}
      onClick={handleVoiceClick}
      disabled={disabled}
      title={isListening ? 'Остановить запись' : 'Начать запись голоса'}
      aria-label="Голосовой ввод"
    >
      <span className="voice-circle" />
      {isListening && <span className="listening-dot" />}
    </button>
  );
}

export default VoiceInput;
