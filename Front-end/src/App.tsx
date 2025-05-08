import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Chatbot from './pages/Chatbot';
import FavoritesPage from './pages/FavoritesPage';
import LoginPage from './pages/Login';
import MainHome from './pages/MainHome';
import MainPage from './pages/Mainpage';
import ProfilePage from './pages/Profile';
import SignupPage from './pages/Signup';
import SurveyPage from './pages/Survey';

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