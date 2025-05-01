import React, { useState } from 'react';

const BudgetSurveyPage = () => {
  const [budget, setBudget] = useState({
    rent: '',
    deposit: '',
    maintenance: ''
  });

  const handleSelect = (type, value) => {
    setBudget((prev) => ({ ...prev, [type]: value }));
  };

  const handleSubmit = () => {
    console.log('선택된 예산:', budget);
    // TODO: API 전송 또는 다음 페이지 이동
  };

  // 버튼 스타일
  const getButtonStyle = (selected, value) => ({
    margin: '5px',
    padding: '10px 20px',
    border: '1px solid #ccc',
    borderRadius: '6px',
    backgroundColor: selected === value ? '#4CAF50' : '#f2f2f2',
    color: selected === value ? 'white' : 'black',
    cursor: 'pointer'
  });

  return (
    <div style={{ padding: '30px', maxWidth: '500px', margin: '0 auto', border: '1px solid #ccc', borderRadius: '10px' }}>
      <h2>💬 나의 예산을 선택해주세요</h2>
      <p style={{ color: '#555' }}>선택한 위치 정보가 없습니다.</p>

      {/* 월세 */}
      <div style={{ marginBottom: '25px' }}>
        <p><b>1</b> 월세는 어느 정도까지 괜찮으신가요? (만원)</p>
        {['30 이하', '30~50', '50~70', '70 이상'].map((value) => (
          <button
            key={value}
            style={getButtonStyle(budget.rent, value)}
            onClick={() => handleSelect('rent', value)}
          >
            {value}
          </button>
        ))}
      </div>

      {/* 보증금 */}
      <div style={{ marginBottom: '25px' }}>
        <p><b>2</b> 보증금은 어느 정도까지 괜찮으신가요? (만원)</p>
        {['500 이하', '500~1000', '1000~2000', '2000 이상'].map((value) => (
          <button
            key={value}
            style={getButtonStyle(budget.deposit, value)}
            onClick={() => handleSelect('deposit', value)}
          >
            {value}
          </button>
        ))}
      </div>

      {/* 관리비 */}
      <div style={{ marginBottom: '25px' }}>
        <p><b>3</b> 관리비는 어느 정도까지 괜찮으신가요? (만원)</p>
        {['5 이하', '5~10', '10 이상'].map((value) => (
          <button
            key={value}
            style={getButtonStyle(budget.maintenance, value)}
            onClick={() => handleSelect('maintenance', value)}
          >
            {value}
          </button>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        style={{
          marginTop: '20px',
          padding: '12px 24px',
          backgroundColor: '#2196F3',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer'
        }}
      >
        다음으로
      </button>
    </div>
  );
};

export default BudgetSurveyPage;
