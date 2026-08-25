import { useEffect, useState } from 'react';
import { apiCall } from './api';
import { Offering } from './types';

interface AdminOfferingsProps {
  token: string;
}

export function AdminOfferings({ token }: AdminOfferingsProps) {
  const [offerings, setOfferings] = useState<Offering[]>([]);

  async function load() {
    try {
      const data = await apiCall<Offering[]>('/admin/offerings', 'GET', token);
      setOfferings(data);
    } catch {}
  }

  useEffect(() => {
    load();
  }, [token]);

  return (
    <>
      <h3>Provider Offerings</h3>
      <button type="button" className="secondary" onClick={load}>Refresh</button>
      <table className="table">
        <thead>
          <tr>
            <th>Provider</th>
            <th>Product</th>
            <th>Listing ID</th>
            <th>SKU</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {offerings.map((o) => (
            <tr key={o.listing_id}>
              <td>{o.provider_name}</td>
              <td>{o.product_name}</td>
              <td>{o.listing_id}</td>
              <td>{o.sku}</td>
              <td>Rs {o.price}</td>
              <td>{o.stock}</td>
              <td>{o.availability}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
