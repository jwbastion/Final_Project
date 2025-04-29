import React, { useState } from 'react';
import './Signup.css'; // 아래 스타일 참고
import { useNavigate } from 'react-router-dom';

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    nickname: '',
    gender: '',
    birth: ''
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
    <div className="signup-page">
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
      {/* 회원가입 폼 */}
      <div className="signup-container">
        <form className="signup-form" onSubmit={handleSubmit}>
          <h2>회원가입</h2>
          <label>
            아이디
            <input name="username" value={form.username} onChange={handleChange} required />
          </label>
          <label>
            비밀번호
            <input name="password" type="password" value={form.password} onChange={handleChange} required />
          </label>
          <label>
            비밀번호 확인
            <input name="confirmPassword" type="password" value={form.confirmPassword} onChange={handleChange} required />
          </label>
          <label>
            닉네임
            <input name="nickname" value={form.nickname} onChange={handleChange} required />
          </label>
          <label>
            성별
            <select name="gender" value={form.gender} onChange={handleChange} required>
              <option value="">선택</option>
              <option value="male">남성</option>
              <option value="female">여성</option>
            </select>
          </label>
          <label>
            생년월일
            <input name="birth" type="date" value={form.birth} onChange={handleChange} required />
          </label>
          <button type="submit">회원가입</button>
        </form>
      </div>
    </div>
  );
}