import { FormEvent, useEffect, useState } from 'react';
import { apiCall } from './api';
import { Offering, Product } from './types';

interface ProviderOfferingsProps {
  token: string;
  message: string;
  error: string;
  setMessage: (msg: string) => void;
  setError: (err: string) => void;
}

export function ProviderOfferings({ token, message, error, setMessage, setError }: ProviderOfferingsProps) {
  const [offerings, setOfferings] = useState<Offering[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [form, setForm] = useState({
    listing_id: '',
    sku: '',
    product_id: '',
    price: 0,
    stock: 0,
    availability: 'ACTIVE' as 'ACTIVE' | 'INACTIVE' | 'OUT_OF_STOCK',
  });

  const [editForm, setEditForm] = useState({
    price: 0,
    stock: 0,
    availability: 'ACTIVE' as 'ACTIVE' | 'INACTIVE' | 'OUT_OF_STOCK',
  });

  async function loadOfferings() {
    try {
      const data = await apiCall<Offering[]>('/provider/offerings/me', 'GET', token);
      setOfferings(data);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadProducts() {
    try {
      const data = await apiCall<Product[]>('/provider/catalog', 'GET', token);
      setProducts(data);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    loadOfferings();
    loadProducts();
  }, [token]);

  function handleProductSelect(productId: string) {
    const product = products.find(p => p.product_id === productId);
    setSelectedProduct(product || null);
    setForm({ ...form, product_id: productId });
  }

  async function create(e: FormEvent) {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!form.product_id || !form.listing_id || !form.sku) {
      setError('Please fill all required fields');
      return;
    }

    try {
      await apiCall('/provider/offerings', 'POST', token, form);
      setMessage(`Offering created successfully!`);
      setForm({
        listing_id: '',
        sku: '',
        product_id: '',
        price: 0,
        stock: 0,
        availability: 'ACTIVE' as 'ACTIVE' | 'INACTIVE' | 'OUT_OF_STOCK',
      });
      setSelectedProduct(null);
      await loadOfferings();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function updateOffering(listingId: string) {
    setError('');
    setMessage('');
    try {
      await apiCall(`/provider/offerings/${listingId}`, 'PATCH', token, editForm);
      setMessage(`Offering updated successfully!`);
      setEditingId(null);
      await loadOfferings();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function startEdit(offering: Offering) {
    setEditingId(offering.listing_id);
    setEditForm({
      price: offering.price,
      stock: offering.stock,
      availability: offering.availability,
    });
  }

  function cancelEdit() {
    setEditingId(null);
  }

  return (
    <>
      <h3>My Products</h3>

      <div className="card" style={{ marginBottom: '20px' }}>
        <h4 style={{ marginTop: 0 }}>Add New Offering</h4>
        <form onSubmit={create}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Select Product *</label>
              <select
                value={form.product_id}
                onChange={(e) => handleProductSelect(e.target.value)}
                required
                style={{ width: '100%' }}
              >
                <option value="">-- Choose a product --</option>
                {products.map(p => (
                  <option key={p.product_id} value={p.product_id}>
                    {p.product_id} - {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Listing ID *</label>
              <input
                value={form.listing_id}
                onChange={(e) => setForm({ ...form, listing_id: e.target.value })}
                placeholder="e.g., ABC-LIST-001"
                required
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>SKU *</label>
              <input
                value={form.sku}
                onChange={(e) => setForm({ ...form, sku: e.target.value })}
                placeholder="e.g., ABC-NPK-001"
                required
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Price (Rs) *</label>
              <input
                type="number"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
                placeholder="Enter price"
                required
                min="0"
                step="0.01"
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Stock *</label>
              <input
                type="number"
                value={form.stock}
                onChange={(e) => setForm({ ...form, stock: Number(e.target.value) })}
                placeholder="Enter stock quantity"
                required
                min="0"
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Availability</label>
              <select
                value={form.availability}
                onChange={(e) => setForm({ ...form, availability: e.target.value as any })}
                style={{ width: '100%' }}
              >
                <option value="ACTIVE">ACTIVE</option>
                <option value="INACTIVE">INACTIVE</option>
                <option value="OUT_OF_STOCK">OUT_OF_STOCK</option>
              </select>
            </div>
          </div>

          {selectedProduct && (
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px', marginBottom: '12px' }}>
              <strong>Selected Product Details:</strong>
              <div style={{ marginTop: '6px', fontSize: '14px' }}>
                <div><strong>Name:</strong> {selectedProduct.name}</div>
                <div><strong>Category:</strong> {selectedProduct.category}</div>
                <div><strong>Unit:</strong> {selectedProduct.unit}</div>
                {selectedProduct.npk_ratio && <div><strong>NPK Ratio:</strong> {selectedProduct.npk_ratio}</div>}
              </div>
            </div>
          )}

          <div className="row">
            <button type="submit">Add Offering</button>
            <button type="button" className="secondary" onClick={loadOfferings}>Refresh</button>
          </div>
        </form>
      </div>

      <h4>My Listed Offerings</h4>
      <table className="table">
        <thead>
          <tr>
            <th>Listing ID</th>
            <th>Product</th>
            <th>SKU</th>
            <th>Price (Rs)</th>
            <th>Stock</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {offerings.length === 0 && (
            <tr>
              <td colSpan={7} style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
                No offerings yet. Add your first product above!
              </td>
            </tr>
          )}
          {offerings.map((o) => (
            <tr key={o.listing_id}>
              <td>{o.listing_id}</td>
              <td>
                <strong>{o.product_name}</strong>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>{o.product_id}</div>
              </td>
              <td>{o.sku}</td>
              <td>
                {editingId === o.listing_id ? (
                  <input
                    type="number"
                    value={editForm.price}
                    onChange={(e) => setEditForm({ ...editForm, price: Number(e.target.value) })}
                    style={{ width: '100px' }}
                    min="0"
                    step="0.01"
                  />
                ) : (
                  `Rs ${o.price}`
                )}
              </td>
              <td>
                {editingId === o.listing_id ? (
                  <input
                    type="number"
                    value={editForm.stock}
                    onChange={(e) => setEditForm({ ...editForm, stock: Number(e.target.value) })}
                    style={{ width: '80px' }}
                    min="0"
                  />
                ) : (
                  o.stock
                )}
              </td>
              <td>
                {editingId === o.listing_id ? (
                  <select
                    value={editForm.availability}
                    onChange={(e) => setEditForm({ ...editForm, availability: e.target.value as any })}
                    style={{ width: '140px' }}
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="INACTIVE">INACTIVE</option>
                    <option value="OUT_OF_STOCK">OUT_OF_STOCK</option>
                  </select>
                ) : (
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 600,
                    background: o.availability === 'ACTIVE' ? '#d1fae5' : o.availability === 'OUT_OF_STOCK' ? '#fee2e2' : '#e5e7eb',
                    color: o.availability === 'ACTIVE' ? '#065f46' : o.availability === 'OUT_OF_STOCK' ? '#991b1b' : '#374151'
                  }}>
                    {o.availability}
                  </span>
                )}
              </td>
              <td className="actions">
                {editingId === o.listing_id ? (
                  <>
                    <button onClick={() => updateOffering(o.listing_id)}>Save</button>
                    <button className="secondary" onClick={cancelEdit}>Cancel</button>
                  </>
                ) : (
                  <button onClick={() => startEdit(o)}>Edit</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
