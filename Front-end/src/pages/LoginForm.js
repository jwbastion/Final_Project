import React, { useState } from 'react';
import './LoginForm.css'; // 아래 CSS를 별도 파일로 저장
import { useNavigate, Link } from 'react-router-dom';

export default function LoginForm() {
  const navigate = useNavigate();
  const [userId, setId] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('로그인 정보:', { userId, password });
    navigate('/survey');
  };

  return (
    <div className="login-page">
      {/* 헤더 */}
      <header className="header">
        <div
          className="logo"
          style={{ cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          🏡 살아보고서
        </div>
      </header>
      {/* 로그인 폼 */}
      <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>로그인</h2>
        <label>
          아이디
          <input
            type="text"
            value={userId}
            onChange={(e) => setId(e.target.value)}
            required
          />
        </label>
        <label>
          비밀번호
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••"
          />
        </label>
        <button type="submit">로그인</button>

        {/* 회원가입 버튼 스타일 */}
        <Link to="/signup" className="signup-button">
          회원가입
        </Link>
      </form>
    </div>
  </div>
  );
}