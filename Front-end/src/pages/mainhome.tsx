import React, { useEffect, useState } from 'react';
import Section from './section'; // 새로 만든 Section.tsx import

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

useEffect(() => {
const email = localStorage.getItem('email');
fetch(`http://localhost:5000/api/survey/latest?email=${email}`)
    .then(res => res.ok ? res.json() : Promise.reject("서버 오류"))
    .then((data: SurveyData) => setSurvey(data))
    .catch(console.error);
}, []);

const surveyItems = survey
? [
    `검색 장소: ${survey.preferred_area}`,
    `${survey.address}`,
    <>
    위도: {survey.latitude} <br /> 경도: {survey.longitude}
    </>,
    `월세: ${survey.monthly}만원`,
    `보증금: ${survey.budget}만원`,
    `관리비: ${survey.maintenance_fee}만원`,
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
