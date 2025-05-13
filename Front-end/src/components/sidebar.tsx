import { useLocation, useNavigate } from 'react-router-dom';
import '@/assets/styles/MainPage.css';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const menus = [
    { label: '홈',       path: '/main' },
    { label: '관심 목록', path: '/main/favorites' },
    { label: '프로필',   path: '/main/profile' },
    { label: '로그아웃', path: '/' },
  ];

  return (
    <aside className="mp-sidebar">
      <div className="mp-sidebar-logo">🏠 LIVEPORT</div>
      <nav>
        <ul className="mp-sidebar-menu">
          {menus.map(menu => {
            const active = location.pathname === menu.path;
            return (
              <li key={menu.label}>
                <button
                  type="button"
                  className={`mp-sidebar-link${active ? ' active' : ''}`}
                  onClick={() => navigate(menu.path)}
                >
                  {menu.label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}