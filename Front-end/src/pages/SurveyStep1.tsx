import type { LatLngExpression, LeafletMouseEvent } from 'leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import React, { useState } from 'react';
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

interface Props {
  onNext: (data: {
    query: string;
    address: string;
    lat: number;
    lng: number;
  }) => void;
}

function Recenter({ center }: { center: LatLngExpression }) {
  const map = useMap();
  map.setView(center);
  return null;
}

// Leaflet 기본 마커 이미지 경로 재설정
delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const SurveyStep1: React.FC<Props> = ({ onNext }) => {
  const [query, setQuery] = useState('');
  const [position, setPosition] = useState<[number, number] | null>(null);
  const [address, setAddress] = useState('');

  function LocationMarker() {
    useMapEvents({
      click(e: LeafletMouseEvent) {
        const { lat, lng } = e.latlng;
        setPosition([lat, lng]);
        fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&accept-language=ko`
        )
          .then((r) => r.json())
          .then((json) => {
            const addressObj = json.address || {};
            const city = addressObj.city || addressObj.town || addressObj.county || addressObj.state || '';
            const district = addressObj.suburb || addressObj.village || addressObj.neighbourhood || '';
            const road = addressObj.road || '';
            const houseNumber = addressObj.house_number || '';
            const roadAddr =
              city +
              (district ? ` ${district}` : '') +
              (road ? ` ${road}` : '') +
              (houseNumber ? ` ${houseNumber}` : '');
            setAddress(roadAddr.trim() || json.display_name || '');
          });
      },
    });
    return position ? <Marker position={position} /> : null;
  }

  const handleSearch = () => {
    if (!query) return;
    fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        query
      )}&accept-language=ko&limit=1`
    )
      .then((r) => r.json())
      .then((json) => {
        const feat = json[0];
        if (feat) {
          const lat = parseFloat(feat.lat);
          const lng = parseFloat(feat.lon);
          setPosition([lat, lng]);
          setAddress(feat.display_name || '');
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
      <p>선호 지역을 검색하거나 지도에서 선택하세요.</p>
      <div className="search-bar">
        <div className="search-input-wrapper">
          <input
            className="form-control"
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="지역명 또는 주소 입력"
          />
        </div>
        <div className="search-btn-wrapper">
          <button className="btn" onClick={handleSearch}>검색</button>
        </div>
      </div>
      <div className="survey-map-wrapper">
        <MapContainer
          center={position || [37.5665, 126.978]}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <LocationMarker />
          {position && <Recenter center={position} />}
        </MapContainer>
      </div>
      {position && (
        <div className="text-center">
          <div className="selected-address">
            <b>선택된 주소:</b> {address}
          </div>
          <button className="btn btn-primary" onClick={handleSelect}>다음</button>
        </div>
      )}
    </div>
  );
};

export default SurveyStep1;