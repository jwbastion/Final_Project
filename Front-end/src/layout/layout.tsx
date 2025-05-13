import { Outlet } from 'react-router-dom';
import '../assets/styles/MainPage.css';
import Sidebar from '../components/sidebar';

export default function Layout() {
  return (
    <div className="mp-root">
      <Sidebar />
      <main className="mp-main">
        <Outlet />
      </main>
    </div>
  );
}