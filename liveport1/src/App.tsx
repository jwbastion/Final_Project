import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/Login';
import SignupPage from './pages/Signup';
import Layout from './pages/Layout';
import SurveyFlow from './pages/Survey/SurveyFlow'; 
import Mainpage from './pages/Mainpage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 로그인/회원가입은 레이아웃 없이 보여줌 */}
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* 나머지 페이지는 Layout(헤더 포함) 사용 */}
        <Route element={<Layout />}>
          <Route path="/survey" element={<SurveyFlow />} />
          <Route path="/main" element={<Mainpage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
