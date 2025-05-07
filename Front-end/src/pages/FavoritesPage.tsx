import React, { useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import '../assets/styles/MainPage.css';

interface OutletContextType {
  favorites: string[];
  setFavorites: React.Dispatch<React.SetStateAction<string[]>>;
}

const FavoritesPage: React.FC = () => {
  const { favorites, setFavorites } = useOutletContext<OutletContextType>();
  const trackRef = useRef<HTMLDivElement>(null);

  const scrollByCard = (dir: 'left' | 'right') => {
    if (!trackRef.current) return;
    const cardWidth = 300;
    const gap = 20;
    const distance = dir === 'right' ? cardWidth + gap : -(cardWidth + gap);
    trackRef.current.scrollBy({ left: distance, behavior: 'smooth' });
  };

  const removeFavorite = (item: string) => {
    setFavorites(prev => prev.filter(fav => fav !== item));
  };

  return (
    <section className="mp-section">
      <h2 className="mp-section-title">⭐ 찜한 매물</h2>

      <div className="mp-carousel">
        <button className="carousel-arrow left" onClick={() => scrollByCard('left')}>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
          </svg>
        </button>

        <div className="mp-carousel-track" ref={trackRef}>
          {favorites.length > 0 ? (
            favorites.map((item, idx) => (
              <div key={idx} className="mp-card">
                {item}
                <div
                  className="heart-icon"
                  onClick={() => removeFavorite(item)}
                  title="관심 목록에서 제거"
                >
                  ❌
                </div>
              </div>
            ))
          ) : (
            <div className="mp-card-empty">관심 등록된 매물이 없습니다.</div>
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

export default FavoritesPage;
