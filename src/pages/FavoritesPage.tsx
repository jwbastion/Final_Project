import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../assets/styles/MainPage.css';

const FavoritesPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const sidebarMenus = [
    { label: '홈', path: '/main' },
    { label: '관심 목록', path: '/main/favorites' },
    { label: '프로필', path: '/main/profile' },
    { label: '로그아웃', path: '/' },
  ];

  const favoriteItems = ['찜한 매물 1', '찜한 매물 2', '찜한 매물 3'];

  return (
    <div className="mp-root">
      <aside className="mp-sidebar">
        <div className="mp-sidebar-logo">🏠 LIVEPORT</div>
        <nav>
          <ul className="mp-sidebar-menu">
            {sidebarMenus.map(menu => (
              <li key={menu.label}>
                <button
                  className={`mp-sidebar-link${location.pathname === menu.path ? ' active' : ''}`}
                  onClick={() => navigate(menu.path)}
                >
                  {menu.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <main className="mp-main">
        <h2 className="mp-section-title">⭐ 찜한 매물</h2>
        <div className="mp-grid">
          {favoriteItems.map((item, idx) => (
            <div key={idx} className="mp-card">
              {item}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default FavoritesPage;