import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import sideImage from '../assets/images/Jfw2.gif'; // 이미지 경로
import '../assets/styles/login.css';

export default function LoginForm() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('로그인 정보:', { email, password });
    navigate('/main/survey'); // survey 페이지 최종 버전 받으면 '/survey'로 변경
  };

  return (
    <div className="login-bg">
      <div className="login-card">
        <div
          className="login-side-image"
          style={{ backgroundImage: `url(${sideImage})` }}
        />
        <div className="login-form-container">
          <div className="login-title">LIVEPORT</div>
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="email" className="form-label">이메일</label>
              <input
                type="email"
                className="form-control"
                id="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label htmlFor="password" className="form-label">비밀번호</label>
              <input
                type="password"
                className="form-control"
                id="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary w-100">로그인</button>
          </form>
          <div className="text-center mt-3">
            <span>Don't have an account? </span>
            <Link to="/signup">Signup</Link>
          </div>
        </div>
      </div>
    </div>
  );
}