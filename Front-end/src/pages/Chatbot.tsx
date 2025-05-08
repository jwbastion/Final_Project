import React, { useEffect, useState } from 'react';
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
}

const Chatbot: React.FC = () => {
  const { nickname } = useOutletContext<OutletContextType>();
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'ai', text: '안녕하세요! 챗봇 분석을 시작합니다.' }
  ]);
  const [input, setInput] = useState('');
  const [profileImage, setProfileImage] = useState<string>('');

  useEffect(() => {
    // 프로필 사진 localStorage에서 가져오기 (Profile 업로드 시 저장했다고 가정)
    const storedImage = localStorage.getItem('profileImage');
    if (storedImage) {
      setProfileImage(storedImage);
    }
  }, []);

  const handleSend = () => {
    if (!input.trim()) return;

    // 1. 사용자 입력 추가
    const userMessage: Message = { sender: 'user', text: input };

    // 2. AI 응답 추가 (간단한 더미 답변)
    const aiMessage: Message = { sender: 'ai', text: `AI 답변: "${input}"에 대해 응답합니다.` };

    // 3. 메세지 추가 (user → ai 순서)
    setMessages(prev => [...prev, userMessage, aiMessage]);

    // 4. 입력창 초기화
    setInput('');
  };

  return (
    <div className="chatbot-container">
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
                  <span> {nickname}</span>
                </>
              )}
            </div>
            <div className={`chatbot-message ${msg.sender}`}>
              {msg.text}
            </div>
          </div>
        ))}
      </div>

      <div className="chatbot-input-area">
        <input
          type="text"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend}>전송</button>
      </div>
    </div>
  );
};

export default Chatbot;
