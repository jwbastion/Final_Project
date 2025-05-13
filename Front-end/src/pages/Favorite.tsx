import FavoriteModalContent from './FavoriteModalContent';
import React, { useState } from 'react';

const listings = [
  {
    address: '영등포구 영등포동6가',
    price: '4685/56',
    area: '33㎡',
    floor: '10층',
    type: '투룸',
  },
];

export default function Favorite() {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  const handleRemove = (e: React.MouseEvent, idx: number) => {
    e.stopPropagation(); // 카드 클릭 이벤트 방지
    alert(`관심목록에서 삭제했습니다.`);
  };

  // 카드 클릭 시 모달 오픈
  const handleCardClick = (idx: number) => {
    setSelectedIdx(idx);
    setModalOpen(true);
  };

  // 모달 닫기
  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedIdx(null);
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
              <div
                className="listing-card"
                key={idx}
                onClick={() => handleCardClick(idx)}
                style={{ cursor: 'pointer', position: 'relative' }}
              >
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

          {/* 모달 구현 */}
          {modalOpen && selectedIdx !== null && (
            <div
              className="modal-overlay"
              style={{
                position: 'fixed',
                top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000
              }}
              onClick={handleCloseModal}
            >
              <div
                className="modal-content"
                style={{
                  background: '#fff',
                  padding: '32px 40px',
                  borderRadius: '12px',
                  minWidth: '280px',
                  textAlign: 'center',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                  position: 'relative'
                }}
                onClick={e => e.stopPropagation()} // 모달 내부 클릭 시 닫기 방지
              >
                <button
                  onClick={handleCloseModal}
                  style={{
                    position: 'absolute',
                    top: 12,
                    right: 16,
                    background: 'none',
                    border: 'none',
                    fontSize: '1.5rem',
                    color: '#888',
                    cursor: 'pointer'
                  }}
                >×</button>
                <FavoriteModalContent listingId={selectedIdx} onClose={handleCloseModal} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}