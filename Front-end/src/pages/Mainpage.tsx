import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
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
  const {pathname} = useLocation();

  // 사이드바 메뉴 정의
  const sidebarMenus = [
    { label: '홈', path: '/main' },
    { label: '관심 목록', path: '/main/favorites' },
    { label: '프로필', path: '/main/profile' },
    { label: '로그아웃', path: '/' },
  ];

  const [survey, setSurvey] = useState<SurveyData | null>(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/survey/latest')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then((data: SurveyData) => setSurvey(data))
      .catch(console.error);
  }, []);

  // “나의 설문 응답”용 배열(label + value)
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

  // 각 섹션 데이터
  const chatbotPrefs  = ['A형 - 추천 성향 1',     'A형 - 추천 성향 2',     'C형 - 추천 성향 3'];
  const distanceRecs  = ['A형 - 거리 기반 매물 1', 'C형 - 거리 기반 매물 1'];
  const budgetRecs    = ['B형 - 예산 기반 매물 1', 'D형 - 예산 기반 매물 1'];

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

      {/* 메인 콘텐츠 */}
      <main className="mp-main">
      <Section title="사용자 유형"    emoji="📋" items={surveyItems}/>
        <Section title="챗봇 추천 성향"     emoji="🤖" items={chatbotPrefs} />
        <Section title="거리 기반 추천 매물" emoji="📍" items={distanceRecs} />
        <Section title="예산 기반 추천 매물" emoji="💰" items={budgetRecs} />
      </main>
    </div>
  );
};

export default MainPage;