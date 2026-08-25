import { FormEvent } from 'react';
import { apiCall } from './api';

interface LoginPageProps {
  usernameInput: string;
  setUsernameInput: (val: string) => void;
  passwordInput: string;
  setPasswordInput: (val: string) => void;
  onLogin: (token: string) => void;
  onLogout: () => void;
  isLoggedIn: boolean;
  loggedInUsername: string;
  roles: string[];
  message: string;
  error: string;
  setMessage: (msg: string) => void;
  setError: (err: string) => void;
}

export function LoginPage({
  usernameInput,
  setUsernameInput,
  passwordInput,
  setPasswordInput,
  onLogin,
  onLogout,
  isLoggedIn,
  loggedInUsername,
  roles,
  message,
  error,
  setMessage,
  setError,
}: LoginPageProps) {
  async function login(e: FormEvent) {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const tokenData = await apiCall<{ access_token: string }>('/auth/token', 'POST', undefined, {
        username: usernameInput,
        password: passwordInput,
      });
      setMessage('Logged in successfully.');
      onLogin(tokenData.access_token);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <section className="card">
      <h3>Login</h3>
      <form className="row" onSubmit={login}>
        <input
          value={usernameInput}
          onChange={(e) => setUsernameInput(e.target.value)}
          placeholder="username"
        />
        <input
          value={passwordInput}
          onChange={(e) => setPasswordInput(e.target.value)}
          placeholder="password"
          type="password"
        />
        <button type="submit">Login</button>
        <button className="secondary" type="button" onClick={onLogout}>
          Logout
        </button>
      </form>
      {isLoggedIn ? (
        <div className="message">
          Logged in as <strong>{loggedInUsername}</strong> with roles: {roles.join(', ') || 'none'}
        </div>
      ) : null}
      {message ? <div className="message card" style={{ marginTop: '12px' }}>{message}</div> : null}
      {error ? <div className="message error card" style={{ marginTop: '12px' }}>{error}</div> : null}
    </section>
  );
}
