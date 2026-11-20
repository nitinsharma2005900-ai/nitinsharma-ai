import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AppLayout from './layouts/AppLayout';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Documents from './pages/Documents';
import Analytics from './pages/Analytics';
import Memories from './pages/Memories';
import ApiDocs from './pages/ApiDocs';
import Settings from './pages/Settings';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeUser, setActiveUser] = useState('usr_99');
  const [sessionId, setSessionId] = useState('session_001');
  const [isDark, setIsDark] = useState(true);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard setActiveTab={setActiveTab} activeUser={activeUser} />;
      case 'chat':
        return <Chat activeUser={activeUser} sessionId={sessionId} setSessionId={setSessionId} />;
      case 'documents':
        return <Documents />;
      case 'analytics':
        return <Analytics activeUser={activeUser} />;
      case 'memory':
        return <Memories activeUser={activeUser} />;
      case 'api-docs':
        return <ApiDocs />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard setActiveTab={setActiveTab} activeUser={activeUser} />;
    }
  };

  return (
    <AppLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      activeUser={activeUser}
      setActiveUser={setActiveUser}
      sessionId={sessionId}
      setSessionId={setSessionId}
      isDark={isDark}
      setIsDark={setIsDark}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
        >
          {renderContent()}
        </motion.div>
      </AnimatePresence>
    </AppLayout>
  );
}
