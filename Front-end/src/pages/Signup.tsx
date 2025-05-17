import axios from 'axios';
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import sideImage from '../assets/images/ex4.gif';
import '../assets/styles/login.css'; // 기존 스타일 재사용

const SignupPage: React.FC = () => {
  const [nickname, setNickname] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const navigate = useNavigate();

  const validateEmail = (email: string) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateEmail(email)) {
        alert('유효한 이메일 주소를 입력해주세요.');
        return;
      }
    
    if (!nickname.trim()) {
      alert('닉네임을 입력해주세요.');
      return;
    }
      
    if (password.length < 8) {
        alert('비밀번호는 8자 이상이어야 합니다.');
        return;
    }

    if (password !== passwordConfirm) {
        alert('비밀번호가 일치하지 않습니다.');
        return;
    }
    // 회원가입 처리 로직
    try {
        await axios.post('http://localhost:5000/api/user/signup', { email, nickname, password });
        alert('회원가입 성공! 로그인 페이지로 이동합니다.');
        navigate('/');
      } catch (error) {
        alert('회원가입 실패: 이미 존재하는 계정입니다.');
      }
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
              <label htmlFor="signup-email" className="form-label">이메일</label>
              <input
                type="email"
                className="form-control"
                id="signup-email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label htmlFor="signup-nickname" className="form-label">닉네임</label>
              <input
                type="text"
                className="form-control"
                id="signup-nickname"
                value={nickname}
                onChange={e => setNickname(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label htmlFor="signup-password" className="form-label">비밀번호</label>
              <input
                type="password"
                className="form-control"
                id="signup-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label htmlFor="signup-password-confirm" className="form-label">비밀번호 확인</label>
              <input
                type="password"
                className="form-control"
                id="signup-password-confirm"
                value={passwordConfirm}
                onChange={e => setPasswordConfirm(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary w-100">회원가입</button>
          </form>
          <div className="text-center mt-3">
            <span>Already have an account? </span>
            <Link to="/">Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
