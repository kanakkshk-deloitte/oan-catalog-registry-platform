import { useState } from 'react';
import { AdminLogin } from './AdminLogin';
import { ProviderLogin } from './ProviderLogin';
import { AdminPortal } from './AdminPortal';
import { ProviderPortal } from './ProviderPortal';

type ViewMode = 'select' | 'admin-login' | 'provider-login' | 'admin-portal' | 'provider-portal';

export default function App() {
  const [view, setView] = useState<ViewMode>('select');
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');

  function handleAdminLogin(accessToken: string, user: string) {
    setToken(accessToken);
    setUsername(user);
    setView('admin-portal');
  }

  function handleProviderLogin(accessToken: string, user: string) {
    setToken(accessToken);
    setUsername(user);
    setView('provider-portal');
  }

  function handleLogout() {
    setToken('');
    setUsername('');
    setView('select');
  }

  if (view === 'select') {
    return (
      <div className="app-wrap">
        <div className="container">
          <header className="header card">
            <h1>OAN Catalog Registry Platform</h1>
            <p className="sub">Provider management and catalog operations portal.</p>
          </header>
          
          <section className="card">
            <h3>Select Login Type</h3>
            <div className="row">
              <button onClick={() => setView('admin-login')}>Admin Login</button>
              <button onClick={() => setView('provider-login')}>Provider Login</button>
            </div>
          </section>
        </div>
      </div>
    );
  }

  if (view === 'admin-login') {
    return (
      <AdminLogin 
        onLogin={handleAdminLogin} 
        onBack={() => setView('select')} 
      />
    );
  }

  if (view === 'provider-login') {
    return (
      <ProviderLogin 
        onLogin={handleProviderLogin} 
        onBack={() => setView('select')} 
      />
    );
  }

  if (view === 'admin-portal') {
    return (
      <AdminPortal 
        token={token} 
        username={username} 
        onLogout={handleLogout} 
      />
    );
  }

  if (view === 'provider-portal') {
    return (
      <ProviderPortal 
        token={token} 
        username={username} 
        onLogout={handleLogout} 
      />
    );
  }

  return null;
}
