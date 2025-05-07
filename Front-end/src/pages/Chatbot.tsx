import React, { useState } from 'react';
import '../assets/styles/Chatbot.css';

interface Message {
  sender: 'user' | 'ai';
  text: string;
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'ai', text: '안녕하세요! 챗봇 분석을 시작합니다.' }
  ]);
  const [input, setInput] = useState('');

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
            className={`chatbot-message ${msg.sender}`}
          >
            {msg.text}
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
