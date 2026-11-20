import React from 'react';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

export default function AppLayout({
  activeTab,
  setActiveTab,
  activeUser,
  setActiveUser,
  sessionId,
  setSessionId,
  isDark,
  setIsDark,
  children,
}) {
  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'dark bg-navy-950' : 'bg-slate-900'} text-slate-100`}>
      <Navbar
        activeUser={activeUser}
        setActiveUser={setActiveUser}
        sessionId={sessionId}
        setSessionId={setSessionId}
        isDark={isDark}
        setIsDark={setIsDark}
      />
      <div className="flex-1 flex">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
