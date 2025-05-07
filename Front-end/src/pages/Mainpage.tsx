import React, { useRef, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import '../assets/styles/MainPage.css';

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

/** 공통 섹션 컴포넌트 */
const Section: React.FC<SectionProps> = ({ title, emoji, items }) => {
  // 각 카드별 즐겨찾기 상태
  const trackRef = useRef<HTMLDivElement>(null);

  const scrollByCard = (dir: 'left' | 'right') => {
    if (!trackRef.current) return;
    const cardWidth = 300;      // 카드 고정 너비
    const gap       = 20;       // 카드 간격
    const distance = dir === 'right'
      ? cardWidth + gap
      : - (cardWidth + gap);
    trackRef.current.scrollBy({ left: distance, behavior: 'smooth' });
  };

  return (
    <section className="mp-section">
      <h2 className="mp-section-title">
        <span className="mp-section-emoji">{emoji}</span> {title}
      </h2>
      <div className="mp-carousel">
        <button className="carousel-arrow left" onClick={()=>scrollByCard('left')}>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
          </svg>
        </button>
        <div className="mp-carousel-track" ref={trackRef}>
          {items.map((item, idx) => (
            <div key={idx} className="mp-card">
              {item}
            </div>
          ))}
        </div>
        <button className="carousel-arrow right" onClick={()=>scrollByCard('right')}>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z"/>
          </svg>
        </button>
      </div>
    </section>
  );
};

const MainPage: React.FC = () => {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const [favorites, setFavorites] = useState<string[]>([]); // 찜한 목록 저장

  const sidebarMenus = [
    { label: '홈', path: '/main' },
    { label: '관심 목록', path: '/main/favorites' },
    { label: '프로필', path: '/main/profile' },
    { label: '로그아웃', path: '/' },
  ];

  return (
    <div className="mp-root">
      {/* 사이드바 */}
      <aside className="mp-sidebar">
        <div className="mp-sidebar-logo">🏠 LIVEPORT</div>
        <nav>
          <ul className="mp-sidebar-menu">
            {sidebarMenus.map(menu => (
              <li key={menu.label}>
                <button
                  type="button"
                  className={`mp-sidebar-link${pathname === menu.path ? ' active' : ''}`}
                  onClick={() => navigate(menu.path)}
                >
                  {menu.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* 오른쪽 페이지 교체 영역 */}
      <main className="mp-main">
        <Outlet context={{favorites, setFavorites}}/>
      </main>
    </div>
  );
};

export default MainPage;
