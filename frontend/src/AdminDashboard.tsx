import { useEffect, useState } from 'react';
import { apiCall } from './api';
import { Product, Provider, Offering } from './types';

interface AdminDashboardProps {
  token: string;
}

export function AdminDashboard({ token }: AdminDashboardProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [adminOfferings, setAdminOfferings] = useState<Offering[]>([]);

  useEffect(() => {
    Promise.all([
      apiCall<Product[]>('/admin/products', 'GET', token).then(setProducts).catch(() => {}),
      apiCall<Provider[]>('/admin/providers', 'GET', token).then(setProviders).catch(() => {}),
      apiCall<Offering[]>('/admin/offerings', 'GET', token).then(setAdminOfferings).catch(() => {}),
    ]);
  }, [token]);

  const stats = {
    totalProviders: providers.length,
    activeProviders: providers.filter((p) => p.status === 'ACTIVE').length,
    pendingProviders: providers.filter((p) => p.status === 'PENDING').length,
    totalProducts: products.length,
    activeProducts: products.filter((p) => p.is_active).length,
    totalOfferings: adminOfferings.length,
  };

  return (
    <>
      <h3>Admin Dashboard</h3>
      <div className="stats-grid">
        <div className="stat">
          <span>Total Providers</span>
          <strong>{stats.totalProviders}</strong>
        </div>
        <div className="stat">
          <span>Active Providers</span>
          <strong>{stats.activeProviders}</strong>
        </div>
        <div className="stat">
          <span>Pending Providers</span>
          <strong>{stats.pendingProviders}</strong>
        </div>
        <div className="stat">
          <span>Total Products</span>
          <strong>{stats.totalProducts}</strong>
        </div>
        <div className="stat">
          <span>Active Products</span>
          <strong>{stats.activeProducts}</strong>
        </div>
        <div className="stat">
          <span>Total Offerings</span>
          <strong>{stats.totalOfferings}</strong>
        </div>
      </div>
    </>
  );
}
