import { useState } from 'react';
import { Layout } from './Layout';
import { ProviderDashboard } from './ProviderDashboard';
import { ProviderCatalog } from './ProviderCatalog';
import { ProviderOfferings } from './ProviderOfferings';
import { ProviderView } from './types';

interface ProviderPortalProps {
  token: string;
  username: string;
  onLogout: () => void;
}

export function ProviderPortal({ token, username, onLogout }: ProviderPortalProps) {
  const [view, setView] = useState<ProviderView>('dashboard');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const navItems = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'catalog', label: 'Catalog' },
    { key: 'my-offerings', label: 'My Products' },
  ];

  return (
    <div className="app-wrap">
      <Layout
        title="Provider Portal"
        description="Manage your catalog"
        navItems={navItems}
        activeNav={view}
        onNavChange={(key) => setView(key as ProviderView)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2 style={{ margin: 0 }}>Provider Portal</h2>
            <p style={{ margin: '4px 0 0', color: '#4b5563' }}>Logged in as <strong>{username}</strong></p>
          </div>
          <button className="secondary" onClick={onLogout}>
            Logout
          </button>
        </div>

        {view === 'dashboard' && <ProviderDashboard token={token} />}
        {view === 'catalog' && <ProviderCatalog token={token} />}
        {view === 'my-offerings' && (
          <ProviderOfferings token={token} message={message} error={error} setMessage={setMessage} setError={setError} />
        )}

        {message && <div className="message card" style={{ marginTop: '12px' }}>{message}</div>}
        {error && <div className="message error card" style={{ marginTop: '12px' }}>{error}</div>}
      </Layout>
    </div>
  );
}
