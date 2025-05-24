// src/services/api.ts

// API 기본 URL
const API_BASE_URL = 'http://localhost:5000/api';

// 인증이 필요한 API 요청 함수
export const apiAuthRequest = async (endpoint: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('token');
  
  if (!token) {
    throw new Error('인증 토큰이 없습니다. 로그인이 필요합니다.');
  }
  
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  // 401 오류 처리
  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/'; // 로그인 페이지로 리다이렉트
    throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
  }
  
  // 기타 오류 처리
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.error || '서버 오류가 발생했습니다.');
  }
  
  return response.json();
};

// 인증이 필요없는 API 요청 함수
export const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const headers = {
    ...options.headers,
    'Content-Type': 'application/json',
  };
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.error || '서버 오류가 발생했습니다.');
  }
  
  return response.json();
};

// 로그인 함수
export const login = async (email: string, password: string) => {
  return apiRequest('/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
};

// 설문 저장 함수
export const saveSurvey = async (surveyData: any) => {
  return apiAuthRequest('/survey', {
    method: 'POST',
    body: JSON.stringify(surveyData),
  });
};

// 설문 조회 함수
export const getSurvey = async () => {
  return apiAuthRequest('/survey');
};