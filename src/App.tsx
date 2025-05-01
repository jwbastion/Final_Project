import { BrowserRouter, Route, Routes } from 'react-router-dom';
import LoginPage from './pages/Login';
import MainPage from './pages/Mainpage';
import SignupPage from './pages/Signup';
import SurveyPage from './pages/Survey';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="/main" element={<MainPage />} />  {/* 메인 페이지 */}
      </Routes>
    </BrowserRouter>
  );
}

export default App;