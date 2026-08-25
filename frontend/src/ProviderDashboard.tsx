import { useEffect, useState } from 'react';
import { apiCall } from './api';
import { Offering } from './types';

interface ProviderDashboardProps {
  token: string;
}

export function ProviderDashboard({ token }: ProviderDashboardProps) {
  const [offerings, setOfferings] = useState<Offering[]>([]);

  useEffect(() => {
    apiCall<Offering[]>('/provider/offerings/me', 'GET', token)
      .then(setOfferings)
      .catch(() => {});
  }, [token]);

  return (
    <>
      <h3>Provider Dashboard</h3>
      <div className="stats-grid">
        <div className="stat">
          <span>Total Products</span>
          <strong>{offerings.length}</strong>
        </div>
        <div className="stat">
          <span>Active</span>
          <strong>{offerings.filter((o) => o.availability === 'ACTIVE').length}</strong>
        </div>
        <div className="stat">
          <span>Inactive</span>
          <strong>{offerings.filter((o) => o.availability === 'INACTIVE').length}</strong>
        </div>
        <div className="stat">
          <span>Out of Stock</span>
          <strong>{offerings.filter((o) => o.availability === 'OUT_OF_STOCK' || o.stock === 0).length}</strong>
        </div>
      </div>
    </>
  );
}
