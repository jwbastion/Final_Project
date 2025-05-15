import React from 'react';

// 각 데이터 타입 정의
interface InfrastructureItem {
  category: string;
  icon?: string;
  time?: string;
}

interface TimelineItem {
  time: string;
  activity: string;
  description: string;
}

interface ReportProps {
  infrastructure: InfrastructureItem[];
  timeline: TimelineItem[];
}

export default function Report({
  infrastructure,
  timeline,
}: ReportProps) {
  return (
    <div>
      {/* 매물 분석 요약 */}
      <section
        style={{
          marginBottom: 32,
          padding: 20,
          borderRadius: 8,
          lineHeight: 1.6,
          textAlign: 'left',
        }}
      >
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>
          🏠 (닉네임)님 매물 분석 요약
        </h2>
        <ul style={{ paddingLeft: 20, marginBottom: 16 }}>
          <li><strong>역세권 중심 생활</strong>을 선호하며, 지하철 도보 10분 이내 매물에 높은 관심.</li>
          <li><strong>카페·마트·공원 등 라이프 인프라</strong>가 잘 갖춰진 지역을 선호.</li>
          <li><strong>편의점·약국·병원 등 생활 편의시설</strong>과의 거리를 중요한 판단 요소.</li>
          <li>단순한 가격보다 <strong>예산 대비 생활 효율</strong>을 더 중시하는 경향.</li>
        </ul>
        <p style={{ fontSize: 15 }}>
          👉 위 조건에 따라 분석한 결과, <strong>이 매물은 <span style={{ color: '#f44336' }}>89%</span>의 높은 일치도</strong>를 보여 실제 거주 만족도가 높을 것으로 기대됩니다.
        </p>
      </section>

      {/* 주변 생활시설 */}
      <section
        style={{
          marginBottom: 32,
          padding: 20,
          borderRadius: 8,
          lineHeight: 1.6,
          textAlign: 'left',
        }}
      >
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>🏙️ 주변 생활시설</h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: 12,
          }}
        >
          {infrastructure.map((item, idx) => (
            <div
              key={idx}
              style={{
                background: '#f5f5f5',
                borderRadius: 8,
                padding: 12,
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 24, marginBottom: 6 }}>{item.icon ?? '📍'}</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{item.category}</div>
              <div style={{ fontSize: 13, color: '#666' }}>{item.time ?? ''}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 타임라인 */}
      <section
        style={{
          marginBottom: 32,
          padding: 20,
          borderRadius: 8,
          lineHeight: 1.6,
          textAlign: 'left',
        }}
      >
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 12 }}>
          ⏱️ 타임라인 정보
        </h2>
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