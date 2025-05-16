import React, { useRef } from 'react';
import html2pdf from 'html2pdf.js';
import Detail from './Detail';

type Props = {
  listingId: number;
  onClose?: () => void;
};

export default function DetailModalContent({ listingId, onClose }: Props) {
  // listingId로 DB에서 상세정보를 fetch하거나, props로 데이터 전달받아 렌더링
  // 예시: const { data, isLoading } = useQuery(['listingDetail', listingId], fetchListingDetail);
  const sampleData = {
    detailInfo: {
      '주소(지번)': '서울특별시 영등포구 영등포동6가 66-11',
      '주소(도로명)': '영신로 40길 20',
      '보증금/월세(만원)': '4685/56',
      '면적': '33㎡',
      '해당층': '10층',
      '방종류': '투룸',
      '근처 지하철역': '영등포시장역',
      '건축연도': '2021년',
      '비고': '개별난방, 도시가스',
    },
  };

  const contentRef = useRef<HTMLDivElement>(null);

  const convertToPdf = () => {
    if (contentRef.current) {  // null이 아닐 때만 실행
      const opt = {
        margin: [10, 15, 10, 15], // 상, 우, 하, 좌 (mm)
        filename: 'report.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      };
      html2pdf().set(opt).from(contentRef.current).save();
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 9999,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
      onClick={onClose}
    >
      <div
        style={{
          position: 'relative',
          width: '90%',
          maxWidth: 900,
          maxHeight: '90vh',
          background: '#fff',
          borderRadius: 8,
          boxShadow: '0 2px 16px rgba(0,0,0,0.2)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* 닫기 버튼 */}
        <button
          onClick={onClose}
          aria-label="닫기"
          style={{
            position: 'absolute',
            top: 16,
            right: 16,
            width: 36,
            height: 36,
            border: 'none',
            borderRadius: '50%',
            background: '#f5f5f5',
            fontSize: 22,
            cursor: 'pointer',
            zIndex: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            transition: 'background 0.2s',
          }}
        >
          ×
        </button>

        {/* 모달 헤더 (필요시) */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid #eee',
          fontWeight: 700,
          fontSize: 20,
        }}>
          매물 상세 정보
        </div>

        {/* 보고서 내용(스크롤 영역) */}
        <div
          ref={contentRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            position: 'relative',
          }}
        >
          <Detail {...sampleData} />
        </div>
      </div>
    </div>
  );
}