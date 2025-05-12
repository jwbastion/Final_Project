- react에서 pdf 추출하기 -

1. powershell 환경에서 'npm install html2pdf.js' 실행(html2pdf.js 설치)
2. src 폴더 내의 types 폴더에 html2pdf.d.ts 파일 추가
3. pdf에 저장할 페이지를 구현한 tsx(js) 파일에 아래 내용들 추가(opt와 button style은 자유롭게 설정 가능)

import { useRef } from 'react';
import html2pdf from 'html2pdf.js';

const PdfConverter = () => { // return문이 들어있는 const(혹은 function)문
  const contentRef = useRef(null);

  const convertToPdf = () => {
    if (contentRef.current) {
      const opt = {
        margin: [10, 15, 10, 15], // 상, 우, 하, 좌 (mm)
        filename: 'my_file.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      };

      html2pdf()
        .set(opt)
        .from(contentRef.current)
        .save();
    }
  };

  return (
    <div>
      <div ref={contentRef}>
        {/* PDF로 변환할 내용 */}
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
};