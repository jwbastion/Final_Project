// src/pages/SurveyStep3.tsx
import React, { useState } from 'react';
import '@/assets/styles/survey-step3.css';

interface Props{
  data: {
    query: string;
    address: string;
    lat: number;
    lng: number;
  };
  onNext: () => void;
}

const extractNumericValue = (str: string): number => {
  if (str.includes("상관없음")) return 0;

  // 모든 숫자 추출 (쉼표 제거 후)
  const numbers = str.replace(/,/g, "").match(/\d+/g);
  if (!numbers || numbers.length === 0) return 0;

  const parsedNumbers = numbers.map(num => parseInt(num, 10));
  return Math.max(...parsedNumbers); // 첫 번째 숫자만
};

const extractCityDistrict = (address: string): string => {
  // 시/도 + 시/군/구 추출
  const match = address.match(/^([가-힣]+)\s([가-힣]+(?:시|군|구))/);
  return match ? `${match[1]} ${match[2]}` : '';
};

const SurveyStep3: React.FC<Props> = ({data, onNext}) => {
  const [monthlyRent, setMonthlyRent] = useState<string>('');
  const [deposit, setDeposit] = useState<string>('');
  const [maintenanceFee, setMaintenanceFee] = useState<string>('');

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

  // 세 개 모두 선택되었을 때만 활성화
  const isFinishEnabled =
    monthlyRent !== '' && deposit !== '' && maintenanceFee !== '';
  
  const handleFinish = () => {
    localStorage.setItem("preferred_area", data.query);
    localStorage.setItem("address", extractCityDistrict(data.address));
    localStorage.setItem("latitude", `${data.lat}`);
    localStorage.setItem("longitude", `${data.lng}`);
    localStorage.setItem("budget", extractNumericValue(deposit).toString());
    localStorage.setItem("monthly", extractNumericValue(monthlyRent).toString());
    localStorage.setItem("maintenance_fee", extractNumericValue(maintenanceFee).toString());
    onNext();
  };

  return (
    <div className="step3-container">
      <div className="survey3-header">
        <h2>나의 예산을 선택해주세요</h2>
      </div>

      <div className="survey-question">
        <span className="question-label">
          1️⃣ 월세는 어느 정도까지 괜찮으신가요?
        </span>
        <div className="survey-options">
          {rentOptions.map(option => (
            <button
              key={option}
              type="button"
              className={
                `survey-option${monthlyRent === option ? ' selected' : ''}`
              }
              onClick={() => setMonthlyRent(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="survey-question">
        <span className="question-label">
          2️⃣ 보증금은 어느 정도까지 괜찮으신가요?
        </span>
        <div className="survey-options">
          {depositOptions.map(option => (
            <button
              key={option}
              type="button"
              className={`survey-option${deposit === option ? ' selected' : ''}`}
              onClick={() => setDeposit(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="survey-question">
        <span className="question-label">
          3️⃣ 관리비는 어느 정도까지 괜찮으신가요?
        </span>
        <div className="survey-options">
          {feeOptions.map(option => (
            <button
              key={option}
              type="button"
              className={
                `survey-option${maintenanceFee === option ? ' selected' : ''}`
              }
              onClick={() => setMaintenanceFee(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
      {/* 하단 중앙 "설문 종료" 버튼 */}
      <div className="survey-finish-container">
        <button
          type="button"
          className="survey-finish-button"
          disabled={!isFinishEnabled}
          onClick={handleFinish}
        >
          설문 종료
        </button>
      </div>
    </div>
  );
};

export default SurveyStep3;