import { FormEvent, useEffect, useState } from 'react';
import { apiCall } from './api';
import { Provider } from './types';

interface AdminProvidersProps {
  token: string;
  message: string;
  error: string;
  setMessage: (msg: string) => void;
  setError: (err: string) => void;
}

export function AdminProviders({ token, message, error, setMessage, setError }: AdminProvidersProps) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [form, setForm] = useState({
    provider_code: 'ABC',
    provider_name: 'ABC Agriculture',
    login_username: 'provider_abc',
  });

  async function loadProviders() {
    try {
      const data = await apiCall<Provider[]>('/admin/providers', 'GET', token);
      setProviders(data);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    loadProviders();
  }, [token]);

  async function create(e: FormEvent) {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await apiCall<Provider>('/admin/providers', 'POST', token, form);
      setMessage(`Provider ${form.provider_code} created.`);
      await loadProviders();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function updateStatus(code: string, status: Provider['status']) {
    setError('');
    setMessage('');
    try {
      await apiCall(`/admin/providers/${code}/status`, 'PATCH', token, { status });
      setMessage(`Provider ${code} set to ${status}.`);
      await loadProviders();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <h3>Providers</h3>
      <form className="row" onSubmit={create}>
        <input value={form.provider_code} onChange={(e) => setForm({ ...form, provider_code: e.target.value })} placeholder="Code" />
        <input value={form.provider_name} onChange={(e) => setForm({ ...form, provider_name: e.target.value })} placeholder="Name" />
        <input value={form.login_username} onChange={(e) => setForm({ ...form, login_username: e.target.value })} placeholder="Login" />
        <button type="submit">Create</button>
        <button type="button" className="secondary" onClick={loadProviders}>Refresh</button>
      </form>

      <table className="table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Username</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {providers.map((p) => (
            <tr key={p.provider_code}>
              <td>{p.provider_code}</td>
              <td>{p.provider_name}</td>
              <td>{p.login_username}</td>
              <td>{p.status}</td>
              <td className="actions">
                <button onClick={() => updateStatus(p.provider_code, 'APPROVED')}>Approve</button>
                <button onClick={() => updateStatus(p.provider_code, 'ACTIVE')}>Activate</button>
                <button className="secondary" onClick={() => updateStatus(p.provider_code, 'SUSPENDED')}>Suspend</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
