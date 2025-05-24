import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Chatbot from './pages/Chatbot';
import FavoritesPage from './pages/FavoritesPage';
import LoginPage from './pages/Login';
import MainHome from './pages/MainHome';
import MainPage from './pages/Mainpage';
import ProfilePage from './pages/Profile';
import PropertyDetailPage from './pages/PropertyDetailPage'; // 추가
import SignupPage from './pages/Signup';
import SurveyPage from './pages/Survey';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="/property/:propertyId" element={<PropertyDetailPage />} /> {/* 추가 */}
        
        {/* MainPage는 레이아웃 역할을 하며 자식 라우트들을 Outlet으로 렌더링 */}
        <Route path="/main" element={<MainPage />}>
          {/* 메인 페이지의 기본 경로 */}
          <Route index element={<MainHome />} />
          {/* 채팅 페이지 경로 수정 */}
          <Route path="chatbot" element={<Chatbot />} />
          {/* 아래 경로들 수정: /main/ 접두사 제거 */}
          <Route path="favorites" element={<FavoritesPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;