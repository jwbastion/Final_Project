import React, { useRef } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';

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
  const navigate = useNavigate();
  const trackRef = useRef<HTMLDivElement>(null);
  const { favorites, setFavorites } = useOutletContext<OutletContextType>();

  const nickname = localStorage.getItem("nickname") || "사용자";

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

  const finalTitle = title === "사용자 유형" ? `${nickname}님의 유형` : title;

  return (
    <section className="mp-section">
      <h2 className="mp-section-title">
        <span className="mp-section-emoji">{emoji}</span> {finalTitle}
      </h2>

      <div className="mp-carousel">
        <button className="carousel-arrow left" onClick={() => scrollByCard('left')}>
          <svg viewBox="0 0 24 24" width="30" height="30">
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
                  style={{ position: 'relative', cursor: title === "사용자 유형" ? 'pointer' : 'default' }}
                  onClick={() => title === "사용자 유형" && navigate('/main/chatbot')}
                >
                  {item}
                    <div
                      className="heart-icon"
                      onClick={(e) => {
                        e.stopPropagation();  // 카드 클릭 막지 않게
                        toggleFavorite(item);
                      }}
                    >
                      {favorites.includes(item) ? '❤️' : '🤍'}
                    </div>
                </div>
              ))}

              {/* 사용자 유형이면 추가로 "다시 설문하러 가기" 카드 */}
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
          <svg viewBox="0 0 24 24" width="30" height="30">
            <path fill="currentColor" d="M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z" />
          </svg>
        </button>
      </div>
    </section>
  );
};

export default Section;
