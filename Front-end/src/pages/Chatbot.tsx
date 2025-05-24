import React, { useEffect, useState, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import '../assets/styles/Chatbot.css';

interface OutletContextType {
  favorites: string[];
  setFavorites: React.Dispatch<React.SetStateAction<string[]>>;
  nickname: string;
}

interface Message {
  sender: 'user' | 'ai';
  text: string;
  timestamp?: string;
}

const Chatbot: React.FC = () => {
  const { nickname } = useOutletContext<OutletContextType>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [profileImage, setProfileImage] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 스크롤을 항상 최신 메시지로 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 초기화 로직
  useEffect(() => {
    // 프로필 사진 localStorage에서 가져오기
    const storedImage = localStorage.getItem('profileImage');
    if (storedImage) {
      setProfileImage(storedImage);
    }

    // 로그인 여부 확인
    const token = localStorage.getItem('token');
    if (!token) {
      console.warn('로그인 상태가 아닙니다.');
      setError('로그인이 필요합니다. 로그인 후 이용해주세요.');
      return;
    }

    // 초기화되지 않았을 때만 실행
    if (!initialized) {
      // 초기 메시지 - 첫 번째 챗봇 메시지(월세 질문) 설정
      setMessages([
        { 
          sender: 'ai', 
          text: '안녕하세요! 부동산 매물 추천 AI입니다. 원하시는 조건을 알려주시면 최적의 매물을 추천해드릴게요.\n\n먼저, 희망하시는 월세는 얼마인가요? (만원 단위)', 
          timestamp: new Date().toLocaleString() 
        }
      ]);
      
      setInitialized(true);
    }
  }, [initialized]);

  // 대화 초기화 기능
  const resetConversation = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        setError('로그인이 필요합니다.');
        return;
      }

      // 서버에 대화 초기화 요청
      const response = await fetch('/api/chatbot/reset', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        // UI 초기화
        setMessages([{ 
          sender: 'ai', 
          text: '안녕하세요! 부동산 매물 추천 AI입니다. 원하시는 조건을 알려주시면 최적의 매물을 추천해드릴게요.\n\n먼저, 희망하시는 월세는 얼마인가요? (만원 단위)', 
          timestamp: new Date().toLocaleString() 
        }]);
        setInitialized(true);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || '초기화 실패');
      }
    } catch (error) {
      console.error('대화 초기화 실패:', error);
      setError('대화 초기화에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  // 메시지 전송 및 응답 처리
  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { 
      sender: 'user', 
      text: input,
      timestamp: new Date().toLocaleString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('로그인이 필요합니다.');
        setLoading(false);
        return;
      }

      // 백엔드 API 호출 - 상대 경로 사용 (프록시 설정 필요)
      const response = await fetch('/api/chatbot/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message: input }),
      });

      console.log('API 응답 상태:', response.status);
      
      if (response.status === 401) {
        setError('인증이 만료되었습니다. 다시 로그인해주세요.');
        setLoading(false);
        return;
      }
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('서버 응답 에러:', errorText);
        throw new Error(`서버 오류: ${response.status}, 상세: ${errorText}`);
      }

      const data = await response.json();
      
      // 응답 처리
      if (data.success) {
        const aiMessage: Message = {
          sender: 'ai',
          text: data.response,
          timestamp: new Date().toLocaleString()
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error(data.message || '응답을 처리하지 못했습니다.');
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error);

      // error를 Error 타입으로 안전하게 변환
      const errorMessage = error instanceof Error ? error.message : '잠시 후 다시 시도해주세요.';
      
      setMessages(prev => [...prev, { 
        sender: 'ai', 
        text: `서버와 연결할 수 없습니다. ${errorMessage}`,
        timestamp: new Date().toLocaleString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      {error && (
        <div className="error-banner">
          <p>{error}</p>
          <button onClick={() => setError(null)}>닫기</button>
        </div>
      )}
      
      <div className="chatbot-reset">
        <button onClick={resetConversation} disabled={loading}>
          대화 초기화
        </button>
      </div>
      
      <div className="chatbot-messages">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chatbot-message-wrapper ${msg.sender}`}
          >
            <div className="sender-header">
              {msg.sender === 'ai' ? (
                <>
                  <img src="/chatbot.png" alt="AI" className="sender-icon" />
                  <span> AI-Bot</span>
                </>
              ) : (
                <>
                  <img
                    src={profileImage || '/profile.jpg'}
                    alt="사용자"
                    className="sender-icon2"
                  />
                  <span> {nickname || '사용자'}</span>
                </>
              )}
              {msg.timestamp && <span className="message-timestamp">{msg.timestamp}</span>}
            </div>
            <div className={`chatbot-message ${msg.sender}`}>
              {msg.text.split('\n').map((line, i) => (
                <React.Fragment key={i}>
                  {line}
                  <br />
                </React.Fragment>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chatbot-message-wrapper ai">
            <div className="sender-header">
              <img src="/chatbot.png" alt="AI" className="sender-icon" />
              <span> AI-Bot</span>
            </div>
            <div className="chatbot-message ai typing-indicator">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chatbot-input-area">
        <input
          type="text"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !loading && handleSend()}
          disabled={loading || !!error}
        />
        <button onClick={handleSend} disabled={loading || !!error || !input.trim()}>
          {loading ? '전송 중...' : '전송'}
        </button>
      </div>
    </div>
  );
};

export default Chatbot;