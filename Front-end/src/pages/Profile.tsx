import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../assets/styles/MainPage.css';

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const sidebarMenus = [
    { label: '홈', path: '/main' },
    { label: '관심 목록', path: '/main/favorites' },
    { label: '프로필', path: '/main/profile' },
    { label: '로그아웃', path: '/' },
  ];

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
        <h2 className="mp-section-title">🙋 내 프로필</h2>
        <div className="mp-card">
          <p><strong>이름:</strong> 홍길동</p>
          <p><strong>이메일:</strong> gil@example.com</p>
          <p><strong>가입일:</strong> 2024-01-01</p>
        </div>
      </main>
    </div>
  );
};

export default ProfilePage;
