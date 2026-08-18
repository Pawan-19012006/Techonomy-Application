import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { useAuth } from '../../contexts/AuthContext';
import { CompetitionLockOverlay } from '../common/CompetitionLockOverlay';

export const AppLayout: React.FC = () => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { isSessionExpired } = useAuth();

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#090D16] text-slate-900 dark:text-slate-100 flex flex-col transition-colors relative">
      
      {/* Full-Screen Competition Lock Screen Overlay when session expires */}
      {isSessionExpired && <CompetitionLockOverlay />}

      {/* Mobile Drawer */}
      <Sidebar
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      {/* Main Page Area Header */}
      <Navbar onToggleMobileSidebar={() => setMobileSidebarOpen((prev) => !prev)} />
      
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1500px] w-full mx-auto space-y-8">
        <Outlet />
      </main>
    </div>
  );
};
