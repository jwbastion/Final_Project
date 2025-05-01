import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import sideImage from '../assets/images/Jfw2.gif';
import '../assets/styles/login.css'; // 로그인 화면 스타일 재사용

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (form.password !== form.confirmPassword) {
      alert('비밀번호가 일치하지 않습니다.');
      return;
    }

    console.log('회원가입 데이터:', form);
    // 서버로 회원가입 정보 전송하는 코드 위치
    navigate('/'); // 가입 후 로그인 화면으로 이동
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
              <label htmlFor="signup-email" className="form-label">
                이메일
                <input
                  name="email"
                  className="form-control"
                  value={form.email}
                  onChange={handleChange}
                  required
                />
              </label>
            </div>
            <div className="mb-3">
              <label htmlFor="signup-password" className="form-label">
                비밀번호
                <input
                  name="password"
                  type="password"
                  className="form-control"
                  value={form.password}
                  onChange={handleChange}
                  required
                />
              </label>
            </div>
            <div className="mb-3">
              <label htmlFor="signup-password-confirm" className="form-label">
                비밀번호 확인
                <input
                  name="confirmPassword"
                  type="password"
                  className="form-control"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  required
                />
                </label>
            </div>
            <button type="submit" className="btn btn-primary w-100">회원가입</button>
          </form>
        </div>
      </div>
    </div>
  );
}