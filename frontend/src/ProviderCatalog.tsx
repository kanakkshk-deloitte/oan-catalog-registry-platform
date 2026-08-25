import { useEffect, useState } from 'react';
import { apiCall } from './api';
import { Product } from './types';

interface ProviderCatalogProps {
  token: string;
}

export function ProviderCatalog({ token }: ProviderCatalogProps) {
  const [catalog, setCatalog] = useState<Product[]>([]);

  async function load() {
    try {
      const data = await apiCall<Product[]>('/provider/catalog', 'GET', token);
      setCatalog(data);
    } catch {}
  }

  useEffect(() => {
    load();
  }, [token]);

  return (
    <>
      <h3>Available Catalog</h3>
      <button type="button" className="secondary" onClick={load}>Refresh</button>
      <table className="table">
        <thead>
          <tr>
            <th>Product ID</th>
            <th>Name</th>
            <th>Category</th>
            <th>Unit</th>
            <th>NPK Ratio</th>
          </tr>
        </thead>
        <tbody>
          {catalog.map((p) => (
            <tr key={p.product_id}>
              <td>{p.product_id}</td>
              <td>{p.name}</td>
              <td>{p.category}</td>
              <td>{p.unit}</td>
              <td>{p.npk_ratio || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
