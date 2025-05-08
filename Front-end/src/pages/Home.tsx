import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const handleAdd = (e: React.MouseEvent, idx: number) => {
    // 실제 관심목록 추가 로직 구현
    e.stopPropagation(); // 카드 클릭 이벤트 방지
    alert(`관심목록에 추가했습니다.`);
  };
  const navigate = useNavigate();

  type Listing = {
    address: string;
    price: string;
    area: string;
    floor: string;
    type: string;
  };

  const userTypes: string[] = [
    'A형 - 사용자 유형 1',
    'A형 - 사용자 유형 2',
    'B형 - 사용자 유형 3',
    'B형 - 사용자 유형 4',
  ];

  const chatbotProfiles: string[] = [];

  const chatbotHistory: Listing[] = [
    {
      address: '강남구 역삼동',
      price: '1000/50',
      area: '20.09㎡',
      floor: '2층',
      type: '원룸',
    },
    {
      address: '강남구 논현동',
      price: '1000/70',
      area: '32.9㎡',
      floor: '반지층',
      type: '투룸',
    },
  ];

  const distanceRecs: Listing[] = [
    {
      address: '강남구 논현동',
      price: '1000/70',
      area: '32.9㎡',
      floor: '반지층',
      type: '투룸',
    },
  ];

  const budgetRecs: Listing[] = [];

  // 사용자 유형/성향 섹션 렌더링 함수
  const renderTypeSection = (
    title: string,
    emoji: string,
    items: string[],
    showButton?: boolean
  ) => (
    <div className="section" key={title}>
      <div className="section-header">
        <span className="section-title">
          <span style={{ marginRight: 6 }}>{emoji}</span>
          {title}
        </span>
        {showButton && (
          <button
            className="recommend-button"
            onClick={() => navigate('/survey')}
          >
            <span role="img" aria-label="설문">📄</span> 사용자 유형 설문 다시 하기
          </button>
        )}
      </div>

      <div className="scroll-card-list">
        {items.length === 0 ? (
          <div className="no-result">추천 결과가 없습니다.</div>
        ) : (
          items.map((item, idx) => (
            <div
              className="user-type-card"
              key={idx}
              tabIndex={0}
              onClick={() => navigate(`/main/chatbot`)}
              style={{ cursor: 'pointer' }}
            >
              {item}
            </div>
          ))
        )}
      </div>
    </div>
  );

  // 매물 카드 리스트 섹션 렌더링 함수
  const renderListingSection = (title: string, listings: Listing[]) => (
    <div className="section" key={title}>
      <div className="section-title">{title}</div>
      <div className="scroll-card-list">
        {listings.length === 0 ? (
          <div className="no-result">추천 결과가 없습니다.</div>
        ) : (
          listings.map((listing, idx) => (
            <div
              className="listing-card"
              key={idx}
              tabIndex={0}
              onClick={() => navigate(`/listing/${idx}`)}
              style={{ cursor: 'pointer' }}
            >
              <button
              className="remove-btn"
              onClick={(e) => handleAdd(e, idx)}
              aria-label="관심목록에 추가"
              type="button"
              >
                +
              </button>
              <div className="listing-address">{listing.address}</div>
              <div className="listing-price">{listing.price}</div>
              <div style={{ fontSize: '0.95rem', color: '#555', textAlign: 'center' }}>
                {listing.area} · {listing.floor} · {listing.type}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  return (
    <div className="main-content">
      <div className="content">
        {renderTypeSection(
          '사용자 유형 (거리+예산 기반)',
          '📄',
          userTypes,
          true // 버튼 표시
        )}
        {renderTypeSection(
          '챗봇 추천 성향',
          '🤖',
          chatbotProfiles,
          false // 버튼 미표시
        )}
        {renderListingSection('챗봇 추천 매물', chatbotHistory)}
        {renderListingSection('거리 기반 추천', distanceRecs)}
        {renderListingSection('예산 기반 추천', budgetRecs)}
      </div>
    </div>
  );
}