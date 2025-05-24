import axios from 'axios';

const API_URL = 'http://localhost:5000/api'; // 백엔드 API 서버 URL

// 토큰 가져오기 함수
const getAuthToken = () => {
  return localStorage.getItem('token');
};

// 채팅 메시지 전송
export const sendChatMessage = async (message: string) => {
  try {
    const response = await axios.post(
      `${API_URL}/chat/message`,
      { message },
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('메시지 전송 중 오류:', error);
    throw error;
  }
};

// 채팅 이력 조회
export const getChatHistory = async (limit = 20) => {
  try {
    const response = await axios.get(
      `${API_URL}/chat/history?limit=${limit}`,
      {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('채팅 이력 조회 중 오류:', error);
    throw error;
  }
};