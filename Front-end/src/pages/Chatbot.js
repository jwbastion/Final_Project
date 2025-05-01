import React, { useState } from 'react';
import '../assets/styles/Chatbot.css';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: '안녕하세요! 무엇을 도와드릴까요?' }
  ]);
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() === '') return;

    // 사용자 입력 추가
    setMessages((prev) => [...prev, { sender: 'user', text: input }]);

    // 예시 챗봇 응답 추가 (간단한 답변)
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: '답변 준비 중입니다...' }
      ]);
    }, 500);

    setInput('');
  };

  return (
    <div className="chatbot-container">
      <div className="chatbox">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지를 입력하세요..."
        />
        <button type="submit">전송</button>
      </form>
    </div>
  );
}