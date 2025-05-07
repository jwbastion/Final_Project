import axios from 'axios';
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import sideImage from '../assets/images/ex4.gif'; // 실제 이미지 경로
import '../assets/styles/login.css'; // 경로를 실제 위치에 맞게 조정
import { useNavigate } from 'react-router-dom';


const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // 로그인 처리 로직
    try {
        const response = await axios.post('http://localhost:5000/login', { email, password });
        if (response.data.success) {
          alert('로그인 성공!');
          navigate('/survey');
        }
      } catch (error) {
        alert('로그인 실패: 이메일 또는 비밀번호가 잘못되었습니다.');
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
};

export default LoginPage;

