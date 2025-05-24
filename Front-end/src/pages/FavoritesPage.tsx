import React, { useRef, useEffect, useState } from 'react';
import '../assets/styles/MainPage.css';

interface FavoriteProperty {
  id: number;
  property_id: string;
  address: string;
  station: string;
  rent: number;
  deposit: number;
  maint: number;
  floor: string;
  heating_type: string;
  parking: boolean;
  facilities: string;
  view: string;
  time_info: string;
  infra_score: number;
  created_at: string;
}

const FavoritesPage: React.FC = () => {
  const trackRef = useRef<HTMLDivElement>(null);
  const [dbFavorites, setDbFavorites] = useState<FavoriteProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 데이터베이스에서 관심 매물 가져오기
  useEffect(() => {
    const fetchFavorites = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        
        if (!token) {
          setError('로그인이 필요합니다.');
          setLoading(false);
          return;
        }

        const response = await fetch('http://localhost:5000/api/chatbot/favorites', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
          setDbFavorites(data.favorites);
        } else {
          throw new Error(data.message || '관심 매물을 가져오는 데 실패했습니다.');
        }
      } catch (error) {
        console.error('관심 매물 가져오기 실패:', error);
        setError(error instanceof Error ? error.message : '관심 매물을 가져오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchFavorites();
  }, []);

  const scrollByCard = (dir: 'left' | 'right') => {
    if (!trackRef.current) return;
    const cardWidth = 300;
    const gap = 20;
    const distance = dir === 'right' ? cardWidth + gap : -(cardWidth + gap);
    trackRef.current.scrollBy({ left: distance, behavior: 'smooth' });
  };

  // 관심 매물 삭제
  const removeFavorite = async (favoriteId: number, _propertyId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/chatbot/favorites/${favoriteId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (data.success) {
        // UI에서 제거
        setDbFavorites(prev => prev.filter(fav => fav.id !== favoriteId));
        alert('관심 매물에서 제거되었습니다.');
      } else {
        alert(data.message || '관심 매물 삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('관심 매물 삭제 오류:', error);
      alert('관심 매물 삭제 중 오류가 발생했습니다.');
    }
  };

  // 매물 정보 포맷팅
  const formatFavoriteProperty = (property: FavoriteProperty) => {
    return `📍 ${property.address}

  💰 월세 ${property.rent}만원
  💎 보증금 ${property.deposit}만원
  🏠 관리비 ${property.maint}만원`;
  };

  if (loading) {
    return (
      <section className="mp-section">
        <h2 className="mp-section-title">⭐ 찜한 매물</h2>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <p>관심 매물을 불러오는 중...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="mp-section">
        <h2 className="mp-section-title">⭐ 찜한 매물</h2>
        <div style={{ textAlign: 'center', padding: '50px', color: 'red' }}>
          <p>오류: {error}</p>
          <button onClick={() => window.location.reload()}>다시 시도</button>
        </div>
      </section>
    );
  }

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
          {dbFavorites.length > 0 ? (
            dbFavorites.map((property) => (
              <div key={property.id} className="mp-card" style={{ position: 'relative' }}>
                {/* 매물 정보를 줄바꿈으로 표시 */}
                {formatFavoriteProperty(property).split('\n').map((line: string, i: number) => (
                  <React.Fragment key={i}>
                    {line}
                    {i < formatFavoriteProperty(property).split('\n').length - 1 && <br />}
                  </React.Fragment>
                ))}
                
                {/* 삭제 버튼 */}
                <div
                  className="heart-icon"
                  onClick={() => removeFavorite(property.id, property.property_id)}
                  title="관심 목록에서 제거"
                  style={{ cursor: 'pointer' }}
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