import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import '../assets/styles/MainPage.css';

export default function Layout() {
  const navigate = useNavigate();

  return (
    <div className="main-page">
      {/* 사이드바 영역 */}
      <aside className="sidebar">
        <div className="sidebar-logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/main')}>
          🏡 LIVEPORT
        </div>
        <ul>
          <li style={{ cursor: 'pointer' }} onClick={() => navigate('/main/favorite')}>⭐ 관심 목록</li>
          <li style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>🚪 로그아웃</li>
        </ul>
      </aside>

      {/* 본문 영역: 여기에 각 페이지가 렌더링됨 */}
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}