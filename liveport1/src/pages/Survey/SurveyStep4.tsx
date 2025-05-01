import React from 'react';
import { useNavigate } from 'react-router-dom';
import './survey-step4.css';

const SurveyStep4: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="step4-container">
      <div className="step4-card">
        <div className="step4-icon">🎉</div>
        <h3 className="step4-title">설문 제출 완료!</h3>
        <p className="step4-text">
          제출된 응답을 바탕으로 사용자의 유형을<br/>
          분석 중입니다. 잠시만 기다려 주세요.
        </p>
        <button
          type="button"
          className="step4-button"
          onClick={() => navigate('/main')}
        >
          분석결과 보러가기
        </button>
      </div>
    </div>
  );
};

export default SurveyStep4;

