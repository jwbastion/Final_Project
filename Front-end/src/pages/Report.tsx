import React from 'react';

// 각 데이터 타입 정의
interface InfrastructureItem {
  category: string;
  description: string;
}

interface TimelineItem {
  time: string;
  activity: string;
  description: string;
}

interface ReportProps {
  summaryInfo: string[];
  detailInfo: Record<string, string | number>;
  infrastructure: InfrastructureItem[];
  timeline: TimelineItem[];
}

export default function Report({
  summaryInfo,
  detailInfo,
  infrastructure,
  timeline,
}: ReportProps) {
  return (
    <div>
      {/* 매물 분석 요약정보 */}
      <section style={{ marginBottom: 32, breakInside: 'avoid', pageBreakInside: 'avoid' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>매물 분석 요약정보</h2>
        <ul>
          {summaryInfo.map((item, idx) => (
            <li key={idx} style={{ fontSize: 15, marginBottom: 8 }}>{item}</li>
          ))}
        </ul>
      </section>

      {/* 상세 매물 정보 */}
      <section style={{ marginBottom: 32, breakInside: 'avoid', pageBreakInside: 'avoid' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>상세 매물 정보</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 15 }}>
          <tbody>
            {Object.entries(detailInfo).map(([key, value]) => (
              <tr key={key} style={{ breakInside: 'avoid', pageBreakInside: 'avoid' }}>
                <th style={{ textAlign: 'left', padding: 8, background: '#f5f5f5', width: 160 }}>{key}</th>
                {/* value를 string으로 변환하여 안전하게 렌더링 */}
                <td style={{ padding: 8 }}>{String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* 인프라 분석 */}
      <section style={{ marginBottom: 32, breakInside: 'avoid', pageBreakInside: 'avoid' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>주변 생활시설/인프라 분석</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 15 }}>
          <thead>
            <tr>
              <th style={{ padding: 8, background: '#f5f5f5' }}>지표</th>
              <th style={{ padding: 8, background: '#f5f5f5' }}>설명</th>
            </tr>
          </thead>
          <tbody>
            {infrastructure.map((item, idx) => (
              <tr key={idx} style={{ breakInside: 'avoid', pageBreakInside: 'avoid' }}>
                <td style={{ padding: 8 }}>{item.category}</td>
                <td style={{ padding: 8 }}>{item.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* 타임라인 */}
      <section style={{ marginBottom: 0, breakInside: 'avoid', pageBreakInside: 'avoid' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>타임라인 정보</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 15 }}>
          <thead>
            <tr>
              <th style={{ padding: 8, background: '#f5f5f5' }}>시간대</th>
              <th style={{ padding: 8, background: '#f5f5f5' }}>활동</th>
              <th style={{ padding: 8, background: '#f5f5f5' }}>설명</th>
            </tr>
          </thead>
          <tbody>
            {timeline.map((item, idx) => (
              <tr key={idx} style={{ breakInside: 'avoid', pageBreakInside: 'avoid' }}>
                <td style={{ padding: 8 }}>{item.time}</td>
                <td style={{ padding: 8 }}>{item.activity}</td>
                <td style={{ padding: 8 }}>{item.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}