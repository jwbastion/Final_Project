import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Chatbot from './pages/chatbot';
import FavoritesPage from './pages/favoritespage';
import LoginPage from './pages/Login';
import MainHome from './pages/mainhome';
import MainPage from './pages/Mainpage';
import ProfilePage from './pages/profile';
import SignupPage from './pages/Signup';
import SurveyPage from './pages/Survey/SurveyFlow';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/survey" element={<SurveyPage />} />

        {/* 1) MainPage는 Sidebar 없이 */}
        <Route path="/main"    element={<MainPage />} >
          <Route index element={<MainHome />} />
          <Route path="chatbot" element={<Chatbot />} />
          <Route path="/main/favorites" element={<FavoritesPage />} />
          <Route path="/main/profile" element={<ProfilePage />} />
          </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;