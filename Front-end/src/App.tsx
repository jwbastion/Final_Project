import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './pages/Layout';
import LoginPage from './pages/Login';
import SignupPage from './pages/Signup';
import Survey from './pages/Survey';
import Chatbot from './pages/Chatbot';
import Home from './pages/Home';
import Favorite from './pages/Favorite';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 로그인/회원가입 */}
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* 설문 */}
        <Route path="survey" element={<Survey />} />
        
        {/* 메인 페이지(헤더와 사이드바 적용) */}
        <Route path="/main" element={<Layout />}>
          <Route path="" element={<Home />} />
          <Route path="survey" element={<Survey />} />
          <Route path="chatbot" element={<Chatbot />} />
          <Route path="favorite" element={<Favorite />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;