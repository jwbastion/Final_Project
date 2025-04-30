import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Survey.css';

export default function Survey() {
  const navigate = useNavigate();

  const [monthlyRent, setMonthlyRent] = useState('');
  const [deposit, setDeposit] = useState('');
  const [maintenanceFee, setMaintenanceFee] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('설문 결과:', { monthlyRent, deposit, maintenanceFee });
    navigate('/main/chatbot');
  };

  return (
    <div className="survey-page">
      {/* 설문 */}
      <div className="survey-container">
        <h2>나의 예산을 선택해주세요</h2>

        <form onSubmit={handleSubmit} className="survey-form">
          <div className="survey-question">
            <span>1️⃣ 월세는 어느 정도까지 괜찮으신가요?</span>
            <div className="survey-options">
              {['30만원 이하', '30~50만원', '50~70만원', '70~90만원', '90~100만원', '100만원 이상'].map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`survey-option ${monthlyRent === option ? 'selected' : ''}`}
                  onClick={() => setMonthlyRent(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="survey-question">
            <span>2️⃣ 보증금은 어느 정도까지 괜찮으신가요?</span>
            <div className="survey-options">
              {['500만원 이하', '500~1,000만원', '1,000~2,000만원', '2,000만원 이상', '상관없음'].map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`survey-option ${deposit === option ? 'selected' : ''}`}
                  onClick={() => setDeposit(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="survey-question">
            <span>3️⃣ 관리비는 어느 정도까지 괜찮으신가요?</span>
            <div className="survey-options">
              {['5만원 이하', '5~10만원', '10만원 이상', '상관없음'].map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`survey-option ${maintenanceFee === option ? 'selected' : ''}`}
                  onClick={() => setMaintenanceFee(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            className="survey-submit"
            disabled={!monthlyRent || !deposit || !maintenanceFee}
          >
            다음으로
          </button>
        </form>
      </div>
    </div>
  );
}