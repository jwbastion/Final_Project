import axios from 'axios';
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import sideImage from '../assets/images/Map.gif'; // 실제 이미지 경로
import '../assets/styles/login.css'; // 경로를 실제 위치에 맞게 조정

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 에러 메시지 초기화
    setError('');
    
    try {
        // 경로 수정: /user/login → /api/login
        const response = await axios.post('http://localhost:5000/api/login', { 
          email, 
          password 
        });
        
        console.log('로그인 응답:', response.data);
        
        if (response.data.token) {
          // JWT 토큰 저장
          localStorage.setItem("token", response.data.token);
          
          // 사용자 정보 저장
          localStorage.setItem("nickname", response.data.user?.nickname || '사용자');
          localStorage.setItem("email", response.data.user?.email || email);
          localStorage.setItem("user_uuid", response.data.user?.uuid || '');

          alert('로그인 성공!');
          navigate('/survey');
        } else {
          // 기존 로그인 로직 (token이 없는 경우를 위한 예비 처리)
          const userData = response.data;
          localStorage.setItem("email", userData.email);
          localStorage.setItem("password", userData.password);
          localStorage.setItem("nickname", userData.nickname);

          alert('로그인 성공!');
          navigate('/survey');
        }
      } catch (error: any) {
        console.error('로그인 실패:', error);
        
        if (error.response) {
          // 서버 응답이 있는 경우
          setError(`로그인 실패: ${error.response.data.message || error.response.data.error || '이메일 또는 비밀번호가 잘못되었습니다.'}`);
        } else if (error.request) {
          // 요청은 보냈지만 응답이 없는 경우
          setError('서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.');
        } else {
          // 요청 설정 중 오류 발생
          setError(`오류가 발생했습니다: ${error.message}`);
        }
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
          
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}
          
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
            <span>계정이 없으신가요? </span>
            <Link to="/signup">회원가입</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;