import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';

interface SurveyData {
  searchPlace: string;
  address: string;
  lat: number;
  lng: number;
  monthlyRent: string;
  deposit: string;
  maintenanceFee: string;
}

interface SectionProps {
  title: string;
  emoji: string;
  items: string[];
}

interface OutletContextType {
    favorites: string[];
    setFavorites: React.Dispatch<React.SetStateAction<string[]>>;
  }

const Section: React.FC<SectionProps> = ({ title, emoji, items }) => {
  const trackRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const {favorites, setFavorites} = useOutletContext<OutletContextType>();

  const scrollByCard = (dir: 'left' | 'right') => {
    if (!trackRef.current) return;
    const cardWidth = 300;
    const gap = 20;
    const distance = dir === 'right' ? cardWidth + gap : -(cardWidth + gap);
    trackRef.current.scrollBy({ left: distance, behavior: 'smooth' });
  };

  const toggleFavorite = (item: string) => {
    setFavorites(prev => 
      prev.includes(item) ? prev.filter(fav => fav !== item) : [...prev, item]
    );
  };

  return (
    <section className="mp-section">
      <h2 className="mp-section-title">
        <span className="mp-section-emoji">{emoji}</span> {title}
      </h2>
      <div className="mp-carousel">
        <button className="carousel-arrow left" onClick={() => scrollByCard('left')}>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
          </svg>
        </button>
        <div className="mp-carousel-track" ref={trackRef}>
        {items.length > 0 ? (
            <>
              {items.map((item, idx) => (
                <div
                  key={idx}
                  className="mp-card"
                  onClick={() => title === "사용자 유형" && navigate('/main/chatbot')}
                >
                  {item}
                  {title === "사용자 유형" && (
                    <div
                      className="heart-icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(item);
                      }}
                    >
                      {favorites.includes(item) ? '❤️' : '🤍'}
                    </div>
                  )}
                </div>
              ))}
              {/* 사용자 유형이면 추가로 "다시 설문하러 가기" 카드 넣기 */}
              {title === "사용자 유형" && (
                <div
                  className="mp-card survey-restart-card"
                  onClick={() => navigate('/survey')}
                  style={{ cursor: 'pointer', fontWeight: 'bold' }}
                >
                  다시 설문하러 가기 ➡️
                </div>
              )}
            </>
          ) : (
            <div className="mp-card-empty">매물이 존재하지 않습니다.</div>
          )}
        </div>
        
        <button className="carousel-arrow right" onClick={() => scrollByCard('right')}>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z" />
          </svg>
        </button>
      </div>
    </section>
  );
};

const MainHome: React.FC = () => {
  const [survey, setSurvey] = useState<SurveyData | null>(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/survey/latest')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then((data: SurveyData) => setSurvey(data))
      .catch(console.error);
  }, []);

  const surveyItems = survey
    ? [
        `검색장소: ${survey.searchPlace}`,
        `주소: ${survey.address}`,
        `위도: ${survey.lat}`,
        `경도: ${survey.lng}`,
        `월세: ${survey.monthlyRent}`,
        `보증금: ${survey.deposit}`,
        `관리비: ${survey.maintenanceFee}`,
      ]
    : [];

  const chatbotPrefs: string[] = [];
  const distanceRecs = ['A형 - 거리 기반 매물 1', 'C형 - 거리 기반 매물 1'];
  const budgetRecs = ['B형 - 예산 기반 매물 1', 'D형 - 예산 기반 매물 1'];

  return (
    <>
      <Section title="사용자 유형" emoji="📋" items={surveyItems} />
      <Section title="챗봇 추천 성향" emoji="🤖" items={chatbotPrefs} />
      <Section title="거리 기반 추천 매물" emoji="📍" items={distanceRecs} />
      <Section title="예산 기반 추천 매물" emoji="💰" items={budgetRecs} />
    </>
  );
};

export default MainHome;
