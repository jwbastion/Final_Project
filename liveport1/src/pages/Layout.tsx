import React from 'react';
import { Outlet } from 'react-router-dom';
import "../MainPage.css";

export default function Layout() {
  return (
    <div className="main-page">
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
