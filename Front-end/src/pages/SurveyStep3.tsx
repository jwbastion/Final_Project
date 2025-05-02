import React, { useState } from 'react';
import '../assets/styles/survey-step3.css';

interface Props {
  onNext: () => void;
}

const SurveyStep3: React.FC<Props> = ({ onNext }) => {
  const [monthlyRent, setMonthlyRent] = useState('');
  const [deposit, setDeposit] = useState('');
  const [maintenanceFee, setMaintenanceFee] = useState('');

  const rentOptions = [
    '30만원 이하',
    '30~50만원',
    '50~70만원',
    '70~90만원',
    '90~100만원',
    '100만원 이상',
  ];
  const depositOptions = [
    '500만원 이하',
    '500~1,000만원',
    '1,000~2,000만원',
    '2,000만원 이상',
    '상관없음',
  ];
  const feeOptions = ['5만원 이하', '5~10만원', '10만원 이상', '상관없음'];

  const isFinishEnabled =
    monthlyRent !== '' && deposit !== '' && maintenanceFee !== '';

  return (
    <div className="step3-container">
      <div className="survey3-header">
        <h2>나의 예산을 선택해주세요</h2>
      </div>
      <div className="survey-question">
        <div className="question-label">1️⃣ 월세는 어느 정도까지 괜찮으신가요?</div>
        <div className="survey-options">
          {rentOptions.map(option => (
            <div
              key={option}
              className={`survey-option${monthlyRent === option ? ' selected' : ''}`}
              onClick={() => setMonthlyRent(option)}
            >
              {option}
            </div>
          ))}
        </div>
      </div>
      <div className="survey-question">
        <div className="question-label">2️⃣ 보증금은 어느 정도까지 괜찮으신가요?</div>
        <div className="survey-options">
          {depositOptions.map(option => (
            <div
              key={option}
              className={`survey-option${deposit === option ? ' selected' : ''}`}
              onClick={() => setDeposit(option)}
            >
              {option}
            </div>
          ))}
        </div>
      </div>
      <div className="survey-question">
        <div className="question-label">3️⃣ 관리비는 어느 정도까지 괜찮으신가요?</div>
        <div className="survey-options">
          {feeOptions.map(option => (
            <div
              key={option}
              className={`survey-option${maintenanceFee === option ? ' selected' : ''}`}
              onClick={() => setMaintenanceFee(option)}
            >
              {option}
            </div>
          ))}
        </div>
      </div>
      <div className="survey-finish-container">
        <button
          className="survey-finish-button"
          disabled={!isFinishEnabled}
          onClick={onNext}
        >
          설문 종료
        </button>
      </div>
    </div>
  );
};

export default SurveyStep3;