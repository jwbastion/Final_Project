import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import './MainPage.css';

export default function Layout() {
  const navigate = useNavigate();

  return (
    <div className="main-page">
      {/* 헤더 */}
      <header className="header">
        <div className="logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/main')}>
          🏡 살아보고서
        </div>
        <div className="auth-buttons">
          <button onClick={() => navigate('/')}>로그아웃</button>
        </div>
      </header>

      {/* 본문 */}
      <div className="main-content">
        {/* 사이드 메뉴 */}
        <aside className="sidebar">
          <ul>
            <li style={{ cursor: 'pointer' }} onClick={() => navigate('/main/favorite')}>⭐ 관심 목록</li>
            <li style={{ cursor: 'pointer' }}>🤖 채팅 이력</li>
            <li style={{ cursor: 'pointer' }}>⚙️ 설정</li>
          </ul>
        </aside>

        {/* 본문 영역: 여기에 각 페이지가 렌더링됨 */}
        <section className="content">
          <Outlet />
        </section>
      </div>
    </div>
  );
}