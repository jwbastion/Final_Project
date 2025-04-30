import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './pages/Layout';
import LoginForm from './pages/LoginForm';
import Signup from './pages/Signup';
import Survey from './pages/Survey';
import Chatbot from './pages/Chatbot';
import Home from './pages/Home';
import Favorite from './pages/Favorite';

function App() {
  return (
    <Router>
      <Routes>
        {/* 로그인/회원가입 */}
        <Route path="/" element={<LoginForm />} />
        <Route path="/signup" element={<Signup />} />

        {/* 로그인 이후(헤더와 사이드바 적용) */}
        <Route path="/main" element={<Layout />}>
          <Route path="" element={<Home />} />
          <Route path="survey" element={<Survey />} />
          <Route path="chatbot" element={<Chatbot />} />
          <Route path="favorite" element={<Favorite />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;