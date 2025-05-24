import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './RecommendationPage.css'; // CSS 파일을 별도로 만들거나 인라인 스타일 사용

interface Property {
  id: string;
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
  infra_score: number;
  time_info: string;
  lat: number;
  lng: number;
  total_score?: number;
}

const RecommendationPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [locationProps, setLocationProps] = useState<Property[]>([]);
  const [budgetProps, setBudgetProps] = useState<Property[]>([]);
  const [chatbotProps, setChatbotProps] = useState<Property[]>([]);
  const [selectedTab, setSelectedTab] = useState('combined');
  
  // 추천 정보 불러오기 (기존 코드와 동일)
  useEffect(() => {
    const fetchRecommendations = async () => {
      setLoading(true);
      try {
        // 1. 위치 기반 추천
        const locationResponse = await axios.get('/api/recommendations/location', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          params: {
            limit: 10
          }
        });
        
        if (locationResponse.data.success) {
          setLocationProps(locationResponse.data.properties);
        }
        
        // 2. 예산 기반 추천
        const budgetResponse = await axios.get('/api/recommendations/budget', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          params: {
            limit: 10
          }
        });
        
        if (budgetResponse.data.success) {
          setBudgetProps(budgetResponse.data.properties);
        }
        
        // 3. 챗봇 기반 추천
        const chatbotResponse = await axios.get('/api/recommendations/chatbot', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (chatbotResponse.data.success && chatbotResponse.data.has_recommendations) {
          setChatbotProps(chatbotResponse.data.combined || []);
        }
      } catch (error) {
        console.error('추천 정보 불러오기 실패:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchRecommendations();
  }, []);

  // 현재 탭에 따라 표시할 매물 선택 (기존 코드와 동일)
  const getCurrentProperties = () => {
    switch(selectedTab) {
      case 'location':
        return locationProps;
      case 'budget':
        return budgetProps;
      case 'chatbot':
        return chatbotProps;
      default:
        return [...chatbotProps].sort((a, b) => (b.total_score || 0) - (a.total_score || 0));
    }
  };

  // 관심 매물 추가 함수 (기존 코드와 동일)
  async function addToFavorites(propertyId: string) {
    try {
      const response = await axios.post('/api/favorites', {
        property_id: propertyId
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.data.success) {
        alert('관심 매물에 추가되었습니다.');
      }
    } catch (error) {
      console.error('관심 매물 추가 실패:', error);
      alert('관심 매물 추가에 실패했습니다.');
    }
  }

  return (
    <div className="recommendation-container">
      <h1 className="page-title">추천 매물</h1>
      
      <div className="tabs-container">
        <button 
          className={`tab-button ${selectedTab === 'combined' ? 'active' : ''}`} 
          onClick={() => setSelectedTab('combined')}
        >
          종합 추천
        </button>
        <button 
          className={`tab-button ${selectedTab === 'location' ? 'active' : ''}`} 
          onClick={() => setSelectedTab('location')}
        >
          위치 기반
        </button>
        <button 
          className={`tab-button ${selectedTab === 'budget' ? 'active' : ''}`} 
          onClick={() => setSelectedTab('budget')}
        >
          예산 기반
        </button>
        <button 
          className={`tab-button ${selectedTab === 'chatbot' ? 'active' : ''}`} 
          onClick={() => setSelectedTab('chatbot')}
        >
          챗봇 추천
        </button>
      </div>
      
      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>추천 매물을 불러오는 중...</p>
        </div>
      ) : (
        <div className="property-grid">
          {getCurrentProperties().length > 0 ? (
            getCurrentProperties().map(property => (
              <PropertyCard 
                key={property.id} 
                property={property} 
                onAddToFavorites={addToFavorites}
              />
            ))
          ) : (
            <div className="no-results">
              <p>해당 카테고리에 추천 매물이 없습니다.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 개선된 매물 카드 컴포넌트
const PropertyCard: React.FC<{
  property: Property;
  onAddToFavorites: (id: string) => void;
}> = ({ property, onAddToFavorites }) => {
  return (
    <div className="property-card">
      <div className="property-image">
        {/* 여기에 매물 이미지를 넣을 수 있습니다. API에서 이미지 URL을 제공한다면 사용하세요. */}
        <div className="property-placeholder-image">
          {/* 이미지가 없을 경우 대체 이미지 표시 */}
          <span className="location-icon">📍</span>
        </div>
        <div className="property-score">
          {property.total_score ? (
            <span>{property.total_score.toFixed(1)}</span>
          ) : (
            <span>{property.infra_score.toFixed(1)}</span>
          )}
        </div>
      </div>
      
      <div className="property-content">
        <div className="property-header">
          <h3 className="property-title">{property.address}</h3>
          <div className="property-station">{property.station}</div>
        </div>
        
        <div className="property-pricing">
          <div className="price-item">
            <span className="price-label">보증금</span>
            <span className="price-value">{property.deposit}만원</span>
          </div>
          <div className="price-item">
            <span className="price-label">월세</span>
            <span className="price-value">{property.rent}만원</span>
          </div>
          <div className="price-item">
            <span className="price-label">관리비</span>
            <span className="price-value">{property.maint}만원</span>
          </div>
        </div>
        
        <div className="property-details">
          <div className="detail-item">
            <span className="detail-icon">🏢</span>
            <span>{property.floor}</span>
          </div>
          <div className="detail-item">
            <span className="detail-icon">🔥</span>
            <span>{property.heating_type}</span>
          </div>
          <div className="detail-item">
            <span className="detail-icon">🚗</span>
            <span>{property.parking ? '주차가능' : '주차불가'}</span>
          </div>
        </div>
        
        <div className="property-time">
          <span className="time-icon">🕒</span>
          <span>{property.time_info}</span>
        </div>
        
        <div className="property-facilities">
          <span className="facilities-icon">🛋️</span>
          <span>{property.facilities}</span>
        </div>
      </div>
      
      <div className="property-actions">
        <button 
          className="favorite-button" 
          onClick={() => onAddToFavorites(property.id)}
        >
          <span className="heart-icon">❤️</span>
          <span>관심 매물</span>
        </button>
        <button className="details-button">
          <span>상세 보기</span>
        </button>
      </div>
    </div>
  );
};

export default RecommendationPage;