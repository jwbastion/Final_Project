// src/pages/SurveyStep2.tsx
import React from 'react';
import '../assets/styles/survey.css';

interface Props {
  data: {
    query: string;
    address: string;
    lat: number;
    lng: number;
  };
  onNext: () => void;
  onBack: () => void;
}

const SurveyStep2: React.FC<Props> = ({ data, onNext, onBack }) => {
  return (
    <div className="step2-container">
      <h3>선호지역 확인</h3>
      <br></br>
      <div className="info-grid">
        <div className="info-card">
          <div className="info-label">검색어</div>
          <div className="info-value">{data.query || '-'}</div>
        </div>
        <div className="info-card">
          <div className="info-label">주소</div>
          <div className="info-value">{data.address}</div>
        </div>
        <div className="info-card">
          <div className="info-label">위도</div>
          <div className="info-value">{data.lat.toFixed(6)}</div>
        </div>
        <div className="info-card">
          <div className="info-label">경도</div>
          <div className="info-value">{data.lng.toFixed(6)}</div>
        </div>
      </div>
      <br></br> <br></br> <br></br>
      <div className="step2-btn-group">
        <button type="button" className="btn btn-secondary" onClick={onBack}>
          위치 다시 검색하기
        </button>
      <button type="button" className="btn btn-primary" onClick={onNext}>
        이 지역으로 선택합니다.
      </button>
    </div>
    </div>
  );
};

export default SurveyStep2;
