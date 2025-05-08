import React from 'react';

const listings = [
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

export default function Favorite() {
  const handleRemove = (e: React.MouseEvent, idx: number) => {
    e.stopPropagation(); // 카드 클릭 이벤트 방지
    alert(`관심목록에서 삭제했습니다.`);
  };

  return (
    <div className="main-content">
      <div className="section">
        <div className="section-title">⭐ 관심 목록</div>
        <div className="scroll-card-list">
          {listings.length === 0 ? (
            <div className="no-result">관심 목록이 비어 있습니다.</div>
          ) : (
            listings.map((item, idx) => (
              <div className="listing-card" key={idx}>
                <button
                  className="remove-btn"
                  onClick={(e) => handleRemove(e, idx)}
                  aria-label="관심목록에서 삭제"
                  type="button"
                >
                  ×
                </button>
                <div className="listing-address">{item.address}</div>
                <div className="listing-price">{item.price}</div>
                <div style={{ fontSize: '0.95rem', color: '#555', textAlign: 'center' }}>
                  {item.area} · {item.floor} · {item.type}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}