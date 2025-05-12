import React, { useRef } from 'react';
import html2pdf from 'html2pdf.js';
import ReactMarkdown from 'react-markdown';

type Props = {
  listingId: number;
};

export default function FavoriteModalContent({ listingId }: Props) {
  // listingId로 DB에서 상세정보를 fetch하거나, props로 데이터 전달받아 렌더링
  // 예시: const { data, isLoading } = useQuery(['listingDetail', listingId], fetchListingDetail);

  // 임시: 준비중입니다
  const report = `
# 안녕하세요!

여기는 **React**에서 마크다운을 렌더링하는 예시입니다.
- 리스트 아이템 1
- 리스트 아이템 2

\`\`\`js
console.log('코드 블록 예시');
\`\`\`
`;

const contentRef = useRef(null);
const convertToPdf = () => {
  const content = contentRef.current;
  if (content) {  // null이 아닐 때만 실행
    const opt = {
      margin: [10, 15, 10, 15], // 상, 우, 하, 좌 (mm)
      filename: 'report.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
    };

    html2pdf()
      .set(opt)
      .from(content)
      .save();
  }
};

  return (
    <div>
      <div ref={contentRef} style={{ fontSize: '1.1rem', fontWeight: 500 }}>
        <ReactMarkdown>{report}</ReactMarkdown>
      </div>
      <button
        onClick={convertToPdf}
        style={{
          backgroundColor: '#1976d2',
          color: '#fff',
          padding: '8px 16px',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontWeight: 500
        }}
      >
        PDF로 저장
      </button>
    </div>
  );
}