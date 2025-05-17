import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface DetailProps {
  detailInfo: Record<string, string | number>;
}

export default function Report({
  detailInfo,
}: DetailProps) {
  // 위도/경도 기본값 설정 (?? 뒤에는 detailInfo에서 받아온 정보가 없을 때 대체할 값을 작성)
  const lat = Number(detailInfo.lat ?? 37.5225);
  const lng = Number(detailInfo.lng ?? 126.9057);
  const address = detailInfo['주소(지번)'] ?? '서울특별시 영등포구 영등포동6가 66-11';

  return (
    <div>
      {/* 상세 매물 정보 */}
      <section style={{ marginBottom: 32, breakInside: 'avoid', pageBreakInside: 'avoid', textAlign: 'left' }}>
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

      {/* 매물 위치 지도 섹션 */}
      <section style={{ marginBottom: 32, breakInside: 'avoid', pageBreakInside: 'avoid' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>매물 위치</h2>
        <div style={{ width: '100%', height: 300, borderRadius: 8, overflow: 'hidden' }}>
          <MapContainer
            center={[lat, lng]}
            zoom={16}
            style={{ width: '100%', height: '100%' }}
            scrollWheelZoom={false}
            dragging={false}
            doubleClickZoom={false}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker position={[lat, lng]}>
              <Popup>{address}</Popup>
            </Marker>
          </MapContainer>
        </div>
      </section>
    </div>
  );
}