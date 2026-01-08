import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { useData } from './hooks/useData';
import { OverviewPage } from './pages/Overview';
import { AIThinkingPage } from './pages/AIThinking';
import { PortfolioPage } from './pages/Portfolio';
import { MarketPage } from './pages/Market';
import { TradeHistoryPage } from './pages/TradeHistory';
import { ArchitecturePage } from './pages/Architecture';
import './index.css';

function App() {
  const { data, loading, error } = useData();

  if (loading) {
    return <LoadingScreen />;
  }

  if (error && !data) {
    return <ErrorScreen error={error} />;
  }

  if (!data) {
    return <ErrorScreen error="No data available" />;
  }

  return (
    <BrowserRouter>
      <Layout lastUpdated={data.metadata.lastUpdated}>
        <Routes>
          <Route path="/" element={<OverviewPage data={data} />} />
          <Route path="/thinking" element={<AIThinkingPage data={data} />} />
          <Route path="/portfolio" element={<PortfolioPage data={data} />} />
          <Route path="/market" element={<MarketPage data={data} />} />
          <Route path="/trades" element={<TradeHistoryPage data={data} />} />
          <Route path="/architecture" element={<ArchitecturePage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] flex items-center justify-center animate-pulse">
          <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          Loading Dashboard
        </h2>
        <p className="text-[var(--color-text-muted)]">
          Fetching trading data...
        </p>
      </div>
    </div>
  );
}

function ErrorScreen({ error }: { error: string }) {
  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-[var(--color-accent-danger)]/20 flex items-center justify-center">
          <svg className="w-8 h-8 text-[var(--color-accent-danger)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          Error Loading Data
        </h2>
        <p className="text-[var(--color-text-muted)] mb-6">
          {error}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 bg-[var(--color-accent-primary)] text-white rounded-lg font-medium hover:bg-[var(--color-accent-secondary)] transition-colors"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

export default App;
