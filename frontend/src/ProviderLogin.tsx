import { useState, FormEvent } from 'react';
import { apiCall } from './api';

interface ProviderLoginProps {
  onLogin: (token: string, username: string) => void;
  onBack: () => void;
}

export function ProviderLogin({ onLogin, onBack }: ProviderLoginProps) {
  const [username, setUsername] = useState('provider_abc');
  const [password, setPassword] = useState('provider123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await apiCall<{ access_token: string }>('/auth/token', 'POST', undefined, {
        username,
        password,
      });
      onLogin(result.access_token, username);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-wrap">
      <div className="container">
        <header className="header card">
          <h1>Provider Login</h1>
          <p className="sub">Sign in to manage your catalog</p>
        </header>

        <section className="card">
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter provider username"
                style={{ width: '100%', maxWidth: '400px' }}
                required
              />
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                style={{ width: '100%', maxWidth: '400px' }}
                required
              />
            </div>

            {error && (
              <div className="message error" style={{ marginBottom: '12px', maxWidth: '400px' }}>
                {error}
              </div>
            )}

            <div className="row">
              <button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
              </button>
              <button type="button" className="secondary" onClick={onBack}>
                Back
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}
