import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../assets/styles/Survey.css';

export default function Survey() {
  const navigate = useNavigate();
  const [monthlyRent, setMonthlyRent] = useState('');
  const [deposit, setDeposit] = useState('');
  const [maintenanceFee, setMaintenanceFee] = useState('');

  // 월세: 3개씩
  const monthlyRentRows = [
    ['30만원 이하', '30~50만원', '50~70만원'],
    ['70~90만원', '90~100만원', '100만원 이상'],
  ];

  // 보증금: 2개씩 + '상관없음' 단독
  const depositRows = [
    ['500만원 이하', '500~1,000만원'],
    ['1,000~2,000만원', '2,000만원 이상'],
  ];
  const depositEtc = '상관없음';

  // 관리비: 3개씩 + '상관없음' 단독
  const maintenanceFeeRows = [
    ['5만원 이하', '5~10만원', '10만원 이상'],
  ];
  const maintenanceFeeEtc = '상관없음';

  const handleSubmit = (e) => {
    e.preventDefault();
    // 결과 전송 및 이동
    navigate('/main');
  };

  return (
    <div className="survey-container">
      <form className="survey-form" onSubmit={handleSubmit}>
        {/* 월세 */}
        <div className="survey-question">
          <h2>💬 나의 예산을 선택해주세요</h2>
          <div>1️⃣ 월세는 어느 정도까지 괜찮으신가요?</div>
          {monthlyRentRows.map((row, idx) => (
            <div className="survey-options row-3" key={idx}>
              {row.map(option => (
                <button
                  type="button"
                  className={`survey-option${monthlyRent === option ? ' selected' : ''}`}
                  key={option}
                  onClick={() => setMonthlyRent(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* 보증금 */}
        <div className="survey-question">
          <div>2️⃣ 보증금은 어느 정도까지 괜찮으신가요?</div>
          {depositRows.map((row, idx) => (
            <div className="survey-options row-2" key={idx}>
              {row.map(option => (
                <button
                  type="button"
                  className={`survey-option${deposit === option ? ' selected' : ''}`}
                  key={option}
                  onClick={() => setDeposit(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          ))}
          <div className="survey-options row-1">
            <button
              type="button"
              className={`survey-option${deposit === depositEtc ? ' selected' : ''}`}
              onClick={() => setDeposit(depositEtc)}
            >
              {depositEtc}
            </button>
          </div>
        </div>

        {/* 관리비 */}
        <div className="survey-question">
          <div>3️⃣ 관리비는 어느 정도까지 괜찮으신가요?</div>
          {maintenanceFeeRows.map((row, idx) => (
            <div className="survey-options row-3" key={idx}>
              {row.map(option => (
                <button
                  type="button"
                  className={`survey-option${maintenanceFee === option ? ' selected' : ''}`}
                  key={option}
                  onClick={() => setMaintenanceFee(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          ))}
          <div className="survey-options row-1">
            <button
              type="button"
              className={`survey-option${maintenanceFee === maintenanceFeeEtc ? ' selected' : ''}`}
              onClick={() => setMaintenanceFee(maintenanceFeeEtc)}
            >
              {maintenanceFeeEtc}
            </button>
          </div>
        </div>

        <button
          className="survey-submit"
          type="submit"
          disabled={!monthlyRent || !deposit || !maintenanceFee}
        >
          다음으로
        </button>
      </form>
    </div>
  );
}