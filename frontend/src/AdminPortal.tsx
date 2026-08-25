import { useState } from 'react';
import { Layout } from './Layout';
import { AdminDashboard } from './AdminDashboard';
import { AdminProducts } from './AdminProducts';
import { AdminCategories } from './AdminCategories';
import { AdminProviders } from './AdminProviders';
import { AdminOfferings } from './AdminOfferings';
import { AdminView } from './types';

interface AdminPortalProps {
  token: string;
  username: string;
  onLogout: () => void;
}

export function AdminPortal({ token, username, onLogout }: AdminPortalProps) {
  const [view, setView] = useState<AdminView>('dashboard');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const navItems = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'products', label: 'Products' },
    { key: 'categories', label: 'Categories' },
    { key: 'providers', label: 'Providers' },
    { key: 'offerings', label: 'Offerings' },
  ];

  return (
    <div className="app-wrap">
      <Layout
        title="Admin Portal"
        description="Manage platform operations"
        navItems={navItems}
        activeNav={view}
        onNavChange={(key) => setView(key as AdminView)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2 style={{ margin: 0 }}>Admin Portal</h2>
            <p style={{ margin: '4px 0 0', color: '#4b5563' }}>Logged in as <strong>{username}</strong></p>
          </div>
          <button className="secondary" onClick={onLogout}>
            Logout
          </button>
        </div>

        {view === 'dashboard' && <AdminDashboard token={token} />}
        {view === 'products' && (
          <AdminProducts token={token} message={message} error={error} setMessage={setMessage} setError={setError} />
        )}
        {view === 'categories' && (
          <AdminCategories token={token} message={message} error={error} setMessage={setMessage} setError={setError} />
        )}
        {view === 'providers' && (
          <AdminProviders token={token} message={message} error={error} setMessage={setMessage} setError={setError} />
        )}
        {view === 'offerings' && <AdminOfferings token={token} />}

        {message && <div className="message card" style={{ marginTop: '12px' }}>{message}</div>}
        {error && <div className="message error card" style={{ marginTop: '12px' }}>{error}</div>}
      </Layout>
    </div>
  );
}
