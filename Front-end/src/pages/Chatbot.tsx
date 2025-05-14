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

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      const aiMessage: Message = {
        sender: 'ai',
        text: data.success ? data.response : (data.message || '응답을 처리하지 못했습니다.')
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      setMessages(prev => [...prev, { sender: 'ai', text: '서버와 연결할 수 없습니다.' }]);
    }

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
