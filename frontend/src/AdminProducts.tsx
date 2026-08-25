import { FormEvent, useEffect, useState } from 'react';
import { apiCall } from './api';
import { Product, Category } from './types';

interface AdminProductsProps {
  token: string;
  message: string;
  error: string;
  setMessage: (msg: string) => void;
  setError: (err: string) => void;
}

export function AdminProducts({ token, message, error, setMessage, setError }: AdminProductsProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState({
    product_id: 'OAN-PROD-1001',
    name: 'NPK Fertilizer',
    supercategory: '',
    category: '',
    subcategory: '',
    description: 'Balanced fertilizer for crop nutrition',
    unit: 'KG',
    npk_ratio: '10-26-26',
    is_active: true,
  });

  // Get unique values for dropdowns
  const supercategories = [...new Set(categories.map(c => c.supercategory))].sort();
  const categoriesForSuper = form.supercategory
    ? [...new Set(categories.filter(c => c.supercategory === form.supercategory).map(c => c.category))].sort()
    : [];
  const subcategoriesForCategory = form.supercategory && form.category
    ? categories
      .filter(c => c.supercategory === form.supercategory && c.category === form.category && c.subcategory)
      .map(c => c.subcategory as string)
      .sort()
    : [];

  async function loadProducts() {
    try {
      const data = await apiCall<Product[]>('/admin/products', 'GET', token);
      setProducts(data);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadCategories() {
    try {
      const data = await apiCall<Category[]>('/admin/categories', 'GET', token);
      setCategories(data);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, [token]);

  async function createProduct(e: FormEvent) {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await apiCall<Product>('/admin/products', 'POST', token, form);
      setMessage(`Product ${form.product_id} created.`);
      await loadProducts();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function updateStatus(productId: string, isActive: boolean) {
    setError('');
    setMessage('');
    try {
      await apiCall(`/admin/products/${productId}/status`, 'PATCH', token, { is_active: isActive });
      setMessage(`Product set to ${isActive ? 'ACTIVE' : 'INACTIVE'}.`);
      await loadProducts();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <h3>Products</h3>
      <form className="row" onSubmit={createProduct}>
        <input
          value={form.product_id}
          onChange={(e) => setForm({ ...form, product_id: e.target.value })}
          placeholder="Product ID"
        />
        <input
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder="Name"
        />
        <select
          value={form.supercategory}
          onChange={(e) => setForm({ ...form, supercategory: e.target.value, category: '', subcategory: '' })}
          required
        >
          <option value="">Select Supercategory</option>
          {supercategories.map((sc) => (
            <option key={sc} value={sc}>{sc}</option>
          ))}
        </select>
        <select
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value, subcategory: '' })}
          required
          disabled={!form.supercategory}
        >
          <option value="">Select Category</option>
          {categoriesForSuper.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <select
          value={form.subcategory}
          onChange={(e) => setForm({ ...form, subcategory: e.target.value })}
          disabled={!form.category}
        >
          <option value="">Select Subcategory (optional)</option>
          {subcategoriesForCategory.map((sub) => (
            <option key={sub} value={sub}>{sub}</option>
          ))}
        </select>
        <input
          value={form.unit}
          onChange={(e) => setForm({ ...form, unit: e.target.value })}
          placeholder="Unit"
        />
        <input
          value={form.npk_ratio}
          onChange={(e) => setForm({ ...form, npk_ratio: e.target.value })}
          placeholder="NPK ratio"
        />
        <button type="submit">Create Product</button>
        <button type="button" className="secondary" onClick={loadProducts}>
          Refresh
        </button>
      </form>

      <table className="table">
        <thead>
          <tr>
            <th>Product ID</th>
            <th>Name</th>
            <th>Category Hierarchy</th>
            <th>Unit</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.product_id}>
              <td>{product.product_id}</td>
              <td>{product.name}</td>
              <td>
                <div style={{ fontSize: '13px' }}>
                  <div><strong>Super:</strong> {product.supercategory}</div>
                  <div><strong>Category:</strong> {product.category}</div>
                  {product.subcategory && <div><strong>Sub:</strong> {product.subcategory}</div>}
                </div>
              </td>
              <td>{product.unit}</td>
              <td>{product.is_active ? 'ACTIVE' : 'INACTIVE'}</td>
              <td className="actions">
                <button onClick={() => updateStatus(product.product_id, true)}>Activate</button>
                <button className="secondary" onClick={() => updateStatus(product.product_id, false)}>
                  Deactivate
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
