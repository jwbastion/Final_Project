import React, { useEffect, useState } from 'react';
import Section from './Section';

interface SurveyData {
  email: string;
  nickname: string;
  preferred_area: string;
  address: string;
  latitude: number;
  longitude: number;
  monthly: number;
  budget: number;
  maintenance_fee: number;
}

const MainHome: React.FC = () => {
  const [survey, setSurvey] = useState<SurveyData | null>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [favorites, setFavorites] = useState<string[]>([]);
  useEffect(() => {
    const email = localStorage.getItem('email');
    fetch(`http://localhost:5000/api/survey/latest?email=${email}`)
      .then(res => res.ok ? res.json() : Promise.reject("서버 오류"))
      .then((data: SurveyData) => {
        console.log("API 응답:", data);
        console.log("위경도:", data.latitude, data.longitude);
        setSurvey(data);
      })
      .catch(console.error);
  }, []);

  // 추천 데이터 가져오기
  useEffect(() => {
    const token = localStorage.getItem('token');
    console.log('토큰 확인:', token);
    
    if (token) {
      console.log('추천 API 호출 시도...');
      fetch('http://localhost:5000/api/recommendations/all', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      .then(res => {
        console.log('추천 API 응답 상태:', res.status);
        return res.ok ? res.json() : Promise.reject(`HTTP ${res.status}`);
      })
      .then(data => {
        console.log('추천 데이터:', data);
        setRecommendations(data.recommendations);
      })
      .catch(err => console.error('추천 API 오류:', err));
    }
  }, []);

  useEffect(() => {
    const fetchFavorites = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5000/api/chatbot/favorites/list', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();
        if (data.success) {
          // 서버에서 받은 관심 매물의 property_id 목록을 state로 저장
          const ids = data.favorites.map((fav: any) => String(fav.property_id));
          setFavorites(ids);
        } else {
          console.error('관심 목록 불러오기 실패:', data.message);
        }
      } catch (err) {
        console.error('관심 목록 불러오기 중 오류:', err);
      }
    };

    fetchFavorites();
  }, []);

  // 관심 매물 추가 함수
  const addToFavorites = async (propertyId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/chatbot/favorites', {
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
        setFavorites(prev => [...new Set([...prev, propertyId])]);
      } else {
        alert(data.message || '관심 매물 추가에 실패했습니다.');
      }
    } catch (error) {
      console.error('관심 매물 추가 오류:', error);
      alert('관심 매물 추가 중 오류가 발생했습니다.');
    }
  };

  // 깔끔한 포맷팅 함수 (추천 텍스트 제거)
  const formatPropertyClean = (item: any, idx: number) => {
    const propertyId = item.property_id || item.id || `${item.address}-${idx}`;

    return {
      content: `${idx + 1}. ${item.address}\n\n🚉 ${item.station} • ${item.time_info}\n\n💸 월세 ${item.rent}만 | 보증금 ${item.deposit}만 | 관리비 ${item.maint}만`,
      data: item,
      id: propertyId,
      addToFavorites: addToFavorites
    };
  };

  const surveyItems = survey
    ? [
        <div key="survey-data">
                <tr>
                  <td className="survey-label">주소</td>
                  <td className="survey-value">{survey.address}</td>
                </tr>
                <tr>
                  <td className="survey-label">위도</td>
                  <td className="survey-value">{survey.latitude}</td>
                </tr>
                <tr>
                  <td className="survey-label">경도</td>
                  <td className="survey-value">{survey.longitude}</td>
                </tr>
                <tr>
                  <td className="survey-label">월세</td>
                  <td className="survey-value">{survey.monthly?.toLocaleString()}만원</td>
                </tr>
                <tr>
                  <td className="survey-label">보증금</td>
                  <td className="survey-value">{survey.budget?.toLocaleString()}만원</td>
                </tr>
                <tr>
                  <td className="survey-label">관리비</td>
                  <td className="survey-value">{survey.maintenance_fee?.toLocaleString()}만원</td>
                </tr>
        </div>
      ]
    : [];

  // 추천 데이터를 객체로 포맷팅
  const chatbotPrefs = recommendations?.chatbot?.length 
    ? recommendations.chatbot.slice(0, 10).map(formatPropertyClean)
    : [{ content: '🤖 챗봇 대화 완료 후 맞춤 추천을 받아보세요!', data: null, id: 'no-chatbot' }];

  const distanceRecs = recommendations?.location_based?.length
    ? recommendations.location_based.slice(0, 10).map(formatPropertyClean)
    : [{ content: '📍 현재 위치 기반 추천 매물을 준비중입니다.', data: null, id: 'no-location' }];

  const budgetRecs = recommendations?.budget_based?.length
    ? recommendations.budget_based.slice(0, 10).map(formatPropertyClean)
    : [{ content: '💰 예산 맞춤 추천 매물을 준비중입니다.', data: null, id: 'no-budget' }];

  return (
    <>
      <Section title="사용자 유형" emoji="📋" items={surveyItems} favorites={favorites} setFavorites={setFavorites} />
      <Section title="챗봇 추천 매물" emoji="🤖" items={chatbotPrefs} favorites={favorites} setFavorites={setFavorites} />
      <Section title="거리 기반 추천 매물" emoji="📍" items={distanceRecs} favorites={favorites} setFavorites={setFavorites} />
      <Section title="예산 기반 추천 매물" emoji="💰" items={budgetRecs} favorites={favorites} setFavorites={setFavorites} />
    </>
  );
};

export default MainHome;