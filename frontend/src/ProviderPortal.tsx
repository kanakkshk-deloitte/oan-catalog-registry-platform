import { type FormEvent, useState } from 'react';
import { Layout } from './Layout';
import { ProviderDashboard } from './ProviderDashboard';
import { ProviderCatalog } from './ProviderCatalog';
import { ProviderOfferings } from './ProviderOfferings';
import { ProviderView } from './types';
import { apiCall } from './api';

interface ProviderPortalProps {
  token: string;
  username: string;
  onLogout: () => void;
}

export function ProviderPortal({ token, username, onLogout }: ProviderPortalProps) {
  const [view, setView] = useState<ProviderView>('dashboard');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isChangePasswordOpen, setIsChangePasswordOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordDialogError, setPasswordDialogError] = useState('');

  const navItems = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'catalog', label: 'Catalog' },
    { key: 'my-offerings', label: 'My Products' },
  ];

  function openChangePasswordModal() {
    setMessage('');
    setError('');
    setPasswordDialogError('');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setIsChangePasswordOpen(true);
  }

  function closeChangePasswordModal() {
    setIsChangePasswordOpen(false);
    setIsChangingPassword(false);
    setPasswordDialogError('');
  }

  async function handleChangePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordDialogError('All password fields are required.');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordDialogError('New password must be at least 8 characters.');
      return;
    }

    if (confirmPassword !== newPassword) {
      setPasswordDialogError('New password and confirm password do not match.');
      return;
    }

    try {
      setIsChangingPassword(true);
      setPasswordDialogError('');
      await apiCall<{ message: string }>('/auth/change-password', 'POST', token, {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setError('');
      setMessage('Password updated successfully. Please use your new password for next login.');
      closeChangePasswordModal();
    } catch (err) {
      setMessage('');
      const errorMessage = err instanceof Error ? err.message : 'Failed to update password';
      setError(errorMessage);
      setPasswordDialogError(errorMessage);
    } finally {
      setIsChangingPassword(false);
    }
  }

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
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="secondary" type="button" onClick={openChangePasswordModal}>
              Change Password
            </button>
            <button className="secondary" type="button" onClick={onLogout}>
              Logout
            </button>
          </div>
        </div>

        {view === 'dashboard' && <ProviderDashboard token={token} />}
        {view === 'catalog' && <ProviderCatalog token={token} />}
        {view === 'my-offerings' && (
          <ProviderOfferings token={token} message={message} error={error} setMessage={setMessage} setError={setError} />
        )}

        {message && <div className="message card" style={{ marginTop: '12px' }}>{message}</div>}
        {error && <div className="message error card" style={{ marginTop: '12px' }}>{error}</div>}

        {isChangePasswordOpen && (
          <div className="modal-backdrop" role="presentation">
            <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="change-password-title">
              <h3 id="change-password-title" style={{ marginTop: 0 }}>Change Password</h3>
              <form onSubmit={handleChangePasswordSubmit}>
                <div className="row">
                  <input
                    type="password"
                    placeholder="Current password"
                    autoComplete="current-password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />
                </div>
                <div className="row">
                  <input
                    type="password"
                    placeholder="New password"
                    autoComplete="new-password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div className="row">
                  <input
                    type="password"
                    placeholder="Confirm new password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
                {passwordDialogError && (
                  <div className="message error" style={{ marginBottom: '10px' }}>
                    {passwordDialogError}
                  </div>
                )}
                <div className="actions" style={{ justifyContent: 'flex-end' }}>
                  <button type="button" className="secondary" onClick={closeChangePasswordModal} disabled={isChangingPassword}>
                    Cancel
                  </button>
                  <button type="submit" disabled={isChangingPassword}>
                    {isChangingPassword ? 'Updating...' : 'Update Password'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </Layout>
    </div>
  );
}
