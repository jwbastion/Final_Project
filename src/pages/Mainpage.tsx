import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../assets/styles/MainPage.css';

interface SectionProps {
  title: string;
  emoji: string;
  items: string[];
}

/** 공통 섹션 컴포넌트 */
const Section: React.FC<SectionProps> = ({ title, emoji, items }) => (
  <section className="mp-section">
    <h2 className="mp-section-title">
      <span className="mp-section-emoji">{emoji}</span>
      {title}
    </h2>
    {items.length > 0 ? (
      <div className="mp-grid">
        {items.map((item, idx) => (
          <div key={idx} className="mp-card">
            {item}
          </div>
        ))}
      </div>
    ) : (
      <div className="mp-no-items">등록된 내역이 없습니다.</div>
    )}
  </section>
);

const MainPage: React.FC = () => {
  const navigate = useNavigate();

  // 사이드바 메뉴 정의
  const sidebarMenus = [
    { label: '홈',       onClick: () => navigate('/main') },
    { label: '관심 목록', onClick: () => navigate('/main/favorites') },
    { label: '프로필',   onClick: () => navigate('/main/profile') },
    { label: '로그아웃', onClick: () => navigate('/') },
  ];

  // 각 섹션 데이터
  const userTypes     = ['A형 - 사용자 유형 1', 'A형 - 사용자 유형 2', 'B형 - 사용자 유형 3', 'B형 - 사용자 유형 4'];
  const chatbotPrefs  = ['A형 - 추천 성향 1',     'A형 - 추천 성향 2',     'C형 - 추천 성향 3'];
  const distanceRecs  = ['A형 - 거리 기반 매물 1', 'C형 - 거리 기반 매물 1'];
  const budgetRecs    = ['B형 - 예산 기반 매물 1', 'D형 - 예산 기반 매물 1'];

  return (
    <div className="mp-root">
      {/* 사이드바 */}
      <aside className="mp-sidebar">
        <div className="mp-sidebar-logo">LIVEPORT</div>
        <nav>
          <ul className="mp-sidebar-menu">
            {sidebarMenus.map(menu => (
              <li key={menu.label}>
                <button
                  type="button"
                  className="mp-sidebar-link"
                  onClick={menu.onClick}
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
        <Section title="나의 사용자 유형"   emoji="👤" items={userTypes} />
        <Section title="챗봇 추천 성향"     emoji="🤖" items={chatbotPrefs} />
        <Section title="거리 기반 추천 매물" emoji="📍" items={distanceRecs} />
        <Section title="예산 기반 추천 매물" emoji="💰" items={budgetRecs} />
      </main>
    </div>
  );
};

export default MainPage;