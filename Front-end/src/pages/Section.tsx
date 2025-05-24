import React, { useRef } from 'react';
import { useNavigate } from 'react-router-dom';

interface SectionProps {
  title: string;
  emoji: string;
  items: any[]; // React.ReactNode[]에서 any[]로 변경
  favorites: string[]; // 추가
  setFavorites: React.Dispatch<React.SetStateAction<string[]>>;
}

const Section: React.FC<SectionProps> = ({ title, emoji, items, favorites, setFavorites }) => {
  const navigate = useNavigate();
  const trackRef = useRef<HTMLDivElement>(null);

  const nickname = localStorage.getItem("nickname") || "사용자";

  const scrollByCard = (dir: 'left' | 'right') => {
    if (!trackRef.current) return;
    const cardWidth = 300;
    const gap = 20;
    const distance = dir === 'right' ? cardWidth + gap : -(cardWidth + gap);
    trackRef.current.scrollBy({ left: distance, behavior: 'smooth' });
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
                onClick={() => {
                  if (title === "사용자 유형") {
                    navigate('/main/chatbot');
                  } else if (typeof item === 'object' && item.data) {
                    // 매물 상세 페이지로 이동
                    const propertyId = item.data.property_id || item.data.id || item.id;
                    if (propertyId) {
                      navigate(`/property/${propertyId}`);
                    } else {
                      console.log('매물 상세 정보:', item.data);
                    }
                  }
                }}
              >
                {/* 기존 item 렌더링 + 줄바꿈 처리 추가 */}
                {typeof item === 'string' ? (
                  item.split('\n').map((line: string, i: number) => (
                    <React.Fragment key={i}>
                      {line}
                      {i < item.split('\n').length - 1 && <br />}
                    </React.Fragment>
                  ))
                ) : typeof item === 'object' && item?.content ? (
                  item.content.split('\n').map((line: string, i: number) => (
                    <React.Fragment key={i}>
                      {line}
                      {i < item.content.split('\n').length - 1 && <br />}
                    </React.Fragment>
                  ))
                ) : (
                  item
                )}

                {/* 하트 아이콘 */}
                {title !== "사용자 유형" && (
                  <div
                    className="heart-icon"
                    onClick={(e) => {
                      e.stopPropagation();

                      if (typeof item === 'object' && item?.data && item?.addToFavorites) {
                        const propertyId = String(item.data.property_id || item.data.id || item.id);
                        if (propertyId) {
                          item.addToFavorites(propertyId); // MainHome.tsx의 함수 호출
                          setFavorites(prev => [...new Set([...prev, propertyId])]); // 즉시 UI 반영
                        }
                      }
                    }}
                  >
                    {
                      favorites.includes(
                        typeof item === 'object' && item.data
                          ? item.data.property_id || item.data.id || item.id
                          : typeof item === 'string'
                            ? item
                            : ''
                      )
                        ? '❤️'
                        : '🤍'
                    }
                  </div>
                )}
              </div>
            ))} {/* 이 부분이 빠져있었음 */}

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