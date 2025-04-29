import React from 'react';
import './MainPage.css';
import { useNavigate } from 'react-router-dom';

export default function MainPage() {
  const navigate = useNavigate();

  return (
    <div className="main-page">
      {/* 헤더 */}
      <header className="header">
        <div
          className="logo"
          style={{ cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          🏡 살아보고서
        </div>
        <div className="auth-buttons">
          <button onClick={() => navigate('/login')}>로그인</button>
          <button onClick={() => navigate('/signup')}>회원가입</button>
        </div>
      </header>

      {/* 본문 */}
      <div className="main-content">
        {/* 사이드 메뉴 */}
        <aside className="sidebar">
          <ul>
            <li style={{ cursor: 'pointer' }} onClick={() => navigate('/survey')}>설문</li>
            <li style={{ cursor: 'pointer' }} onClick={() => navigate('/chatbot')}>챗봇</li>
          </ul>
        </aside>

        {/* 본 내용 */}
        <section className="content">
          메인 페이지 입니다.
        </section>
      </div>
    </div>
  );
}
