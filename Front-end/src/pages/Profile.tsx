import React, { useEffect, useState } from 'react';
import '../assets/styles/Profile.css';

interface SurveyData {
  searchPlace: string;
  address: string;
  lat: number;
  lng: number;
  monthlyRent: string;
  deposit: string;
  maintenanceFee: string;
}

const ProfilePage: React.FC = () => {
  const [email, setEmail] = useState<string>('');
  const [nickname, setNickname] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [survey, setSurvey] = useState<SurveyData | null>(null);
  const [profileImage, setProfileImage] = useState<string>(''); // 이미지 URL

  useEffect(() => {
    // 이메일, 닉네임, 비밀번호는 localStorage 기준 (로그인할 때 저장했다고 가정)
    const storedEmail = localStorage.getItem('email') || '';
    const storedNickname = localStorage.getItem('nickname') || '';
    const storedPassword = localStorage.getItem('password') || '';
    const storedProfileImage = localStorage.getItem('profileImage') || '';

    setEmail(storedEmail);
    setNickname(storedNickname);
    setPassword(storedPassword);
    setProfileImage(storedProfileImage);

    // 설문조사 정보 불러오기
    fetch('http://localhost:5000/api/survey/latest')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then((data: SurveyData) => setSurvey(data))
      .catch(console.error);
  }, []);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        setProfileImage(base64String);
        localStorage.setItem('profileImage', base64String); // localStorage 저장
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="profile-image-container">
          <img
            src={profileImage || '/profile.jpg'} // 기본 이미지 제공
            alt="프로필"
            className="profile-image"
          />
          <input
            type="file"
            accept="image/*"
            id="upload"
            style={{ display: 'none' }}
            onChange={handleImageChange}
          />
          <label htmlFor="upload" className="upload-button">사진 변경</label>
        </div>

        <div className="profile-info">
          <div className="profile-field">
            <span className="label">이메일</span>
            <span className="value">{email}</span>
          </div>

          <div className="profile-field">
            <span className="label">닉네임</span>
            <span className="value">{nickname}</span>
          </div>

          <div className="profile-field">
            <span className="label">비밀번호</span>
            <span className="value">{"*".repeat(password.length)}</span>
          </div>

          <div className="profile-field survey-field">
            <span className="label">설문조사 내용</span>
            {survey ? (
              <ul className="survey-list">
                <li>검색장소: {survey.searchPlace}</li>
                <li>주소: {survey.address}</li>
                <li>위도: {survey.lat}</li>
                <li>경도: {survey.lng}</li>
                <li>월세: {survey.monthlyRent}</li>
                <li>보증금: {survey.deposit}</li>
                <li>관리비: {survey.maintenanceFee}</li>
              </ul>
            ) : (
              <span>설문조사 기록이 없습니다.</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;

