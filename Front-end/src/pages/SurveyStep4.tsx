import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../assets/styles/survey-step4.css';

const SurveyStep4: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="step4-container">
      <div className="step4-card">
        <div className="step4-icon">🎉</div>
        <div className="step4-title">설문이 완료되었습니다!</div>
        <div className="step4-text">
          제출된 응답을 바탕으로 사용자의 유형을 분석 중입니다.<br />
          잠시만 기다려 주세요.
        </div>
        <button className="step4-button" onClick={() => navigate('/main')}>
          메인으로 돌아가기
        </button>
      </div>
    </div>
  );
};

export default SurveyStep4;