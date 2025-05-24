import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

interface PropertyDetail {
  property_id: string;
  address: string;
  station: string;
  rent: number;
  deposit: number;
  maint: number;
  floor: string;
  heating_type: string;
  parking: boolean;
  facilities: string;
  view: string;
  lat: number;
  lng: number;
  infra_score: number;
  time_info: string;
  [key: string]: any;

}

const PropertyDetailPage: React.FC = () => {
  const { propertyId } = useParams<{ propertyId: string }>();
  const navigate = useNavigate();
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPropertyDetail = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');

        if (!token) {
          setError('로그인이 필요합니다.');
          return;
        }

        // 추천 테이블들에서 매물 정보 찾기
        const response = await fetch(`http://localhost:5000/api/recommendations/property/${propertyId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
          console.log('전체 property 데이터:', data.property);
          console.log('nearby_infra 데이터:', data.property.nearby_infra);
          setProperty(data.property);
        } else {
          throw new Error(data.message || '매물 정보를 가져오는 데 실패했습니다.');
        }
      } catch (error) {
        console.error('매물 상세 정보 가져오기 실패:', error);
        setError(error instanceof Error ? error.message : '매물 정보를 가져오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };

    if (propertyId) {
      fetchPropertyDetail();
    }
  }, [propertyId]);

  const addToFavorites = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/chatbot/favorites', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ property_id: propertyId })
      });

      const data = await response.json();
      if (data.success) {
        alert('관심 매물에 추가되었습니다!');
      } else {
        alert(data.message || '관심 매물 추가에 실패했습니다.');
      }
    } catch (error) {
      console.error('관심 매물 추가 오류:', error);
      alert('관심 매물 추가 중 오류가 발생했습니다.');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>매물 정보를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: 'red' }}>
        <p>오류: {error}</p>
        <button onClick={() => navigate(-1)}>뒤로 가기</button>
      </div>
    );
  }

  if (!property) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>매물 정보를 찾을 수 없습니다.</p>
        <button onClick={() => navigate(-1)}>뒤로 가기</button>
      </div>
    );
  }

  return (
    <div style={{
      padding: '20px',
      maxWidth: '1200px',  // 더 넓게
      margin: '0 auto',
      minHeight: '100vh',  // 전체 화면 높이
      boxSizing: 'border-box'
    }}>
      <div style={{ marginBottom: '20px' }}>
        <button onClick={() => navigate(-1)} style={{
          marginRight: '10px',
          padding: '10px 20px',
          backgroundColor: '#6c757d',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}>
          ← 뒤로 가기
        </button>
        <button onClick={addToFavorites} style={{
          backgroundColor: '#ff6b6b',
          color: 'white',
          border: 'none',
          padding: '10px 20px',
          borderRadius: '4px',
          cursor: 'pointer'
        }}>
          ❤️ 관심 매물 추가
        </button>
      </div>

      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        <h1 style={{ marginBottom: '20px', color: '#333' }}>{property.address} ({property.station})</h1>

        {/* 가격 정보 */}
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
          <h3>💰 가격 정보</h3>
          <p><strong>월세:</strong> {property.rent}만원 | <strong>보증금:</strong> {property.deposit}만원 | <strong>관리비:</strong> {property.maint}만원</p>
          <p><strong>교통:</strong> {property.time_info}</p>
        </div>

        {/* 점수 정보 */}
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
          <h3>⭐ 점수</h3>
          <p><strong>총점:</strong> {((property.infra_score || 0) + 4.5).toFixed(1)}/10.0 = 인프라({(property.infra_score || 0).toFixed(1)}/3.0) + 특성(4.5/7.0)</p>
        </div>

        
        {(() => {
          console.log('모든 property 속성들:', Object.keys(property));
          return null;
        })()}

        {/* 매물 상세 정보 */}
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f1f8e9', borderRadius: '8px' }}>
          <h3>🏠 매물 정보</h3>
          <p><strong>층수:</strong> {property.floor} | <strong>면적:</strong> {property.size || '정보없음'}평</p>
          <p><strong>난방:</strong> {property.heating_type} | <strong>방향:</strong> {property.view || '정보없음'}</p>
          <p><strong>주차:</strong> {property.parking ? '가능' : '불가능'} | <strong>엘리베이터:</strong> {property.elevator ? '있음' : '없음'}</p>
          <p><strong>타입:</strong> {property.type || '원룸'}</p>
          <p><strong>시설:</strong> {property.facilities || '정보없음'}</p>
        </div>

        {/* 주변 인프라 - 스크롤 및 반응형 개선 */}
        {property.nearby_infra && property.nearby_infra.length > 0 && (
          <div style={{
            marginBottom: '20px',
            padding: '15px',
            backgroundColor: '#fff3e0',
            borderRadius: '8px',
            maxHeight: '500px',  // 최대 높이 설정
            overflowY: 'auto',   // 세로 스크롤 가능
            border: '1px solid #e0e0e0'
          }}>
            <h3 style={{ marginBottom: '15px', position: 'sticky', top: '0', backgroundColor: '#fff3e0', paddingBottom: '10px' }}>
              📍 주변 인프라
            </h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '12px',
              maxWidth: '100%'
            }}>
              {property.nearby_infra.map((infra: any, index: number) => (
                <div key={index} style={{
                  padding: '12px',
                  backgroundColor: 'white',
                  borderRadius: '6px',
                  border: '1px solid #ddd',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                  wordBreak: 'break-word'  // 긴 텍스트 줄바꿈
                }}>
                  <div style={{ fontWeight: 'bold', color: '#2c3e50', marginBottom: '4px' }}>
                    {infra.type}
                  </div>
                  <div style={{ fontSize: '14px', color: '#34495e' }}>
                    {infra.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px' }}>
                    📏 {infra.distance}m
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );};

export default PropertyDetailPage;