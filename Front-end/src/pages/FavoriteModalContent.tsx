import React, { useRef } from 'react';
import html2pdf from 'html2pdf.js';
import Report from './Report';

type Props = {
  listingId: number;
  onClose?: () => void;
};

export default function FavoriteModalContent({ listingId, onClose }: Props) {
  // listingId로 DB에서 상세정보를 fetch하거나, props로 데이터 전달받아 렌더링
  // 예시: const { data, isLoading } = useQuery(['listingDetail', listingId], fetchListingDetail);
  const sampleData = {
    summaryInfo: [
      '역세권 중심 생활을 선호, 지하철 도보 10분 이내 매물에 높은 관심',
      '카페·마트·공원 등 라이프 인프라가 잘 갖춰진 지역 선호',
      '편의점·약국·병원 등 생활 편의시설과의 거리 중요',
      '예산 대비 생활 효율 중시',
      '분석 결과: 이 매물은 89%의 높은 일치도를 보여 실제 거주 만족도가 높을 것으로 기대',
    ],
    detailInfo: {
      '주소(지번)': '서울특별시 영등포구 영등포동 6가 66-11',
      '주소(도로명)': '영신로 40길 20',
      '보증금/월세(만원)': '4685/56',
      '면적': '33㎡',
      '해당층': '10층',
      '방종류': '투룸',
      '근처 지하철역': '영등포시장역',
      '건축연도': '2021년',
      '비고': '개별난방, 도시가스',
    },
    infrastructure: [
      { category: '교통', description: '5호선 영등포시장역 5~10분, 1호선/2호선 도보 접근 가능' },
      { category: '편의', description: 'CU/GS25, 다이소, 이마트, 홈플러스, 신세계백화점, 타임스퀘어 등 인접' },
      { category: '안전', description: '도보권 경찰서, CCTV 다수 설치' },
      { category: '건강', description: '다양한 의원·병원 인접' },
      { category: '녹지', description: '어린이공원, 영등포공원, 문래근린공원, 여의도 한강공원' },
      { category: '생활', description: '우체국, 은행, 대형마트 등 도보권' },
      { category: '놀이', description: '코인노래방, PC방, CGV, 롯데시네마 등 문화시설' },
      { category: '운동', description: '헬스장, 요가, 필라테스 등 일부, 당구장·볼링장 등 다양' },
    ],
    timeline: [
      { time: '07:30', activity: '기상·출근준비', description: '지하철 5호선 영등포시장역 도보 6분, 강남까지 30분 소요' },
      { time: '08:30', activity: '출근 이동', description: '도보+지하철 통합 경로 시각화' },
      { time: '12:00', activity: '점심 식사', description: '500m 이내 식당 148곳, 혼밥 가능 카페 70곳' },
      { time: '18:00', activity: '퇴근 후 운동', description: '도보 7분 거리 헬스장 3곳, 공원 2곳' },
      { time: '20:00', activity: '여가', description: '독립서점/카페거리 밀도 시각화' },
      { time: '22:00', activity: '귀가', description: '도보 10분 생활권 내 편의점 12개, 안전한 귀갓길 밝기 높음' },
    ],
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
          매물 추천 보고서
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
          <Report {...sampleData} />
        </div>

        {/* PDF 저장 버튼 영역 (가운데 정렬) */}
        <div
          style={{
            width: '100%',
            background: 'linear-gradient(180deg, transparent 40%, #fff 100%)',
            display: 'flex',
            justifyContent: 'center', // 가운데 정렬로 변경
            alignItems: 'center',
            padding: '16px 32px',
            borderTop: '1px solid #eee',
            position: 'sticky',
            bottom: 0,
            zIndex: 5,
          }}
        >
          <button
            onClick={convertToPdf}
            style={{
              padding: '12px 32px',
              background: '#1976d2',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              fontWeight: 600,
              fontSize: 16,
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
            }}
          >
            PDF 저장
          </button>
        </div>
      </div>
    </div>
  );
}