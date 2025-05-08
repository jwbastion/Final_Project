import React, { useEffect, useState } from 'react';
import Section from './Section'; // 새로 만든 Section.tsx import

interface SurveyData {
  searchPlace: string;
  address: string;
  lat: number;
  lng: number;
  monthlyRent: string;
  deposit: string;
  maintenanceFee: string;
}


const MainHome: React.FC = () => {
  const [survey, setSurvey] = useState<SurveyData | null>(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/survey/latest')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then((data: SurveyData) => setSurvey(data))
      .catch(console.error);
  }, []);

  const surveyItems = survey
    ? [
        `검색장소: ${survey.searchPlace}`,
        `주소: ${survey.address}`,
        `위도: ${survey.lat}`,
        `경도: ${survey.lng}`,
        `월세: ${survey.monthlyRent}`,
        `보증금: ${survey.deposit}`,
        `관리비: ${survey.maintenanceFee}`,
      ]
    : [];

  const chatbotPrefs: string[] = [];
  const distanceRecs = ['A형 - 거리 기반 매물 1', 'C형 - 거리 기반 매물 1'];
  const budgetRecs = ['B형 - 예산 기반 매물 1', 'D형 - 예산 기반 매물 1'];

  return (
    <>
      <Section title="사용자 유형" emoji="📋" items={surveyItems} />
      <Section title="챗봇 추천 매물" emoji="🤖" items={chatbotPrefs} />
      <Section title="거리 기반 추천 매물" emoji="📍" items={distanceRecs} />
      <Section title="예산 기반 추천 매물" emoji="💰" items={budgetRecs} />
    </>
  );
};

export default MainHome;

