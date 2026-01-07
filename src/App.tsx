import { Routes, Route, Navigate } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { DeepDive } from './pages/DeepDive';
import { Decomposition } from './pages/Decomposition';
import { WhatIf } from './pages/WhatIf';
import { AIChat } from './pages/AIChat';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-neutral-50">
      <Sidebar />
      <div className="ml-16 lg:ml-64">
        <Header />
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
      </div>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppLayout>
            <Dashboard />
          </AppLayout>
        }
      />
      <Route
        path="/deep-dive"
        element={
          <AppLayout>
            <DeepDive />
          </AppLayout>
        }
      />
      <Route
        path="/decomposition"
        element={
          <AppLayout>
            <Decomposition />
          </AppLayout>
        }
      />
      <Route
        path="/what-if"
        element={
          <AppLayout>
            <WhatIf />
          </AppLayout>
        }
      />
      <Route
        path="/ai-chat"
        element={
          <AppLayout>
            <AIChat />
          </AppLayout>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
