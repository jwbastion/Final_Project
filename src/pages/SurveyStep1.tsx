import type { LatLngExpression, LeafletMouseEvent } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import React, { useState } from 'react';
import { MapContainer, Marker, TileLayer, useMap, useMapEvents, } from 'react-leaflet';

interface Props {
  onNext: (data: {
    query: string;
    address: string;
    lat: number;
    lng: number;
  }) => void;
}

// 지도를 새로운 중심으로 옮기는 컴포넌트
function Recenter({ center }: { center: LatLngExpression }) {
  const map = useMap();
  map.setView(center);    // map.fitBounds([[center]]) 대신 setView 사용
  return null;
}

const SurveyStep1: React.FC<Props> = ({ onNext }) => {
  const [query, setQuery] = useState('');
  const [position, setPosition] = useState<[number, number] | null>(null);
  const [address, setAddress] = useState('');

  // 지도 클릭해서 좌표·주소 가져오기
  function LocationMarker() {
    useMapEvents({
      click(e: LeafletMouseEvent) {
        const { lat, lng } = e.latlng;
        setPosition([lat, lng]);
        fetch(`https://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lng}` +
          `&lang=ko&apiKey=${import.meta.env.VITE_GEOAPIFY_API_KEY}`)
          .then(r => r.json())
          .then(json => {
            const p = json.features?.[0]?.properties || {};
            // 시/군/구 추출
            const city = p.city || p.county || p.region || '';
            const district = p.district || '';
            // 도로명+번지 조합
            const road = p.street || '';
            const num  = p.housenumber || '';
            // "시 도로명 번지" 형식
            const roadAddr = city
              + ' ' + district + (road ? ` ${road}${num ? ` ${num}` : ''}` : '');
            setAddress(roadAddr);
          });
        },
    });
    return position ? <Marker position={position} /> : null;
  }

  const handleSearch = () => {
    if (!query) return;
    fetch(`https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(
        query
      )}` +
      `&lang=ko&apiKey=${import.meta.env.VITE_GEOAPIFY_API_KEY}&limit=1`)
      .then(r => r.json())
      .then(json => {
        const feat = json.features?.[0];
        if (feat) {
          const [lng, lat] = feat.geometry.coordinates;
          setPosition([lat, lng]);
          const p = feat.properties || {};
          const city = p.city || p.county || p.region || '';
          const district = p.district || '';
          const road = p.street || '';
          const num  = p.housenumber || '';
          const roadAddr = city
            + ' ' + district + (road ? ` ${road}${num ? ` ${num}` : ''}` : '');
          setAddress(roadAddr);
        } else {
          alert('검색 결과가 없습니다.');
        }
      });
  };

  const handleSelect = () => {
    if (!position) return;
    const [lat, lng] = position;
    onNext({ query, address, lat, lng });
  };

  return (
    <div className="step1-container">
      <br></br>
      <p>선호 지역을 검색하거나 지도에서 선택하세요.</p>
      <div className="search-bar mb-3">
        <input
          type="text"
          className="form-control"
          placeholder="회사, 학교 또는 지하철역 검색"
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button className="btn btn-secondary ms-2 text-nowrap" onClick={handleSearch}>
          검색
        </button>
      </div>
      <div className="survey-map-wrapper">
      <MapContainer
        center={[37.5665,126.978] as [number, number]}
        zoom={13}
        style={{ height: 400, width: '100%' }}
      >
        {position && <Recenter center={position} />}
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <LocationMarker />
      </MapContainer>
      </div>
      <div className="text-center mt-3">
        <button
          className="btn btn-primary"
          disabled={!position}
          onClick={handleSelect}
        >
          다음
        </button>
      </div>
    </div>
  );
};

export default SurveyStep1;
