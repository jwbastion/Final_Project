import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const navigate = useNavigate();

  const userTypes = [
    'A형 - 사용자 유형 1',
    'A형 - 사용자 유형 2',
    'B형 - 사용자 유형 3',
    'B형 - 사용자 유형 4',
  ];

  const chatbotProfiles = [
    'A형 - 챗봇 추천 성향 1',
    'A형 - 챗봇 추천 성향 2',
    'C형 - 챗봇 추천 성향 3',
  ];

  const chatbotHistory = [
    'A형 - 챗봇 추천 매물 1',
    'A형 - 챗봇 추천 매물 2',
    'D형 - 챗봇 추천 매물 1',
  ];

  const distanceRecs = [
    'A형 - 거리 기반 매물 1',
    'C형 - 거리 기반 매물 1',
  ];

  const budgetRecs = [
    'B형 - 예산 기반 매물 1',
    'D형 - 예산 기반 매물 1',
  ];

  const renderSection = (title, emoji, items) => (
    <div className="section">
      <h3 className="section-title">{emoji} {title}</h3>
      <div className="card-grid">
        {items.map((item, index) => (
          <div className="card" key={index}>
            {item}
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <section className="content">
      {renderSection('사용자 유형 (거리+예산 기반)', '📋', userTypes)}
      <div className="center-button">
        <button className="recommend-button" onClick={() => navigate('/main/survey')}>📄 나에게 맞는 추천 다시 받기</button>
      </div>

      {renderSection('챗봇 기반 사용자 성향 (인프라/라이프스타일 기반)', '🤖', chatbotProfiles)}
      <div className="center-button">
        <button className="recommend-button" onClick={() => navigate('/main/chatbot')}>🤖 나에게 맞는 추천 다시 받기</button>
      </div>

      {renderSection('챗봇 추천 이력', '🤖', chatbotHistory)}
      {renderSection('거리 기반 추천 매물', '🧊', distanceRecs)}
      {renderSection('예산 기반 추천 매물', '💰', budgetRecs)}
    </section>
  );
}