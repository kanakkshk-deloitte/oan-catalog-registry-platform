import { FormEvent, useEffect, useState } from 'react';
import { apiCall } from './api';

interface Category {
    id: number;
    supercategory: string;
    category: string;
    subcategory?: string;
    description?: string;
    is_active: boolean;
}

interface AdminCategoriesProps {
    token: string;
    message: string;
    error: string;
    setMessage: (msg: string) => void;
    setError: (err: string) => void;
}

export function AdminCategories({ token, message, error, setMessage, setError }: AdminCategoriesProps) {
    const [categories, setCategories] = useState<Category[]>([]);
    const [form, setForm] = useState({
        supercategory: 'Agricultural Inputs',
        category: 'Fertilizers',
        subcategory: '',
        description: '',
    });

    async function loadCategories() {
        try {
            const data = await apiCall<Category[]>('/admin/categories', 'GET', token);
            setCategories(data);
        } catch (err) {
            setError((err as Error).message);
        }
    }

    useEffect(() => {
        loadCategories();
    }, [token]);

    async function createCategory(e: FormEvent) {
        e.preventDefault();
        setError('');
        setMessage('');

        // Clean subcategory if empty
        const payload = {
            ...form,
            subcategory: form.subcategory.trim() || null,
            is_active: true,
        };

        try {
            await apiCall<Category>('/admin/categories', 'POST', token, payload);
            setMessage(`Category created successfully.`);
            setForm({ supercategory: '', category: '', subcategory: '', description: '' });
            await loadCategories();
        } catch (err) {
            setError((err as Error).message);
        }
    }

    async function deleteCategory(categoryId: number) {
        if (!confirm('Are you sure you want to delete this category?')) return;

        setError('');
        setMessage('');
        try {
            await apiCall(`/admin/categories/${categoryId}`, 'DELETE', token);
            setMessage('Category deleted successfully.');
            await loadCategories();
        } catch (err) {
            setError((err as Error).message);
        }
    }

    return (
        <>
            <h3>Category Management</h3>
            <p style={{ color: '#6b7280', marginBottom: '20px' }}>
                Manage the three-level category hierarchy. Categories will be available when creating products.
            </p>

            <form className="row" onSubmit={createCategory}>
                <div>
                    <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>Supercategory *</label>
                    <input
                        value={form.supercategory}
                        onChange={(e) => setForm({ ...form, supercategory: e.target.value })}
                        placeholder="e.g., Agricultural Inputs"
                        required
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>Category *</label>
                    <input
                        value={form.category}
                        onChange={(e) => setForm({ ...form, category: e.target.value })}
                        placeholder="e.g., Fertilizers"
                        required
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>Subcategory</label>
                    <input
                        value={form.subcategory}
                        onChange={(e) => setForm({ ...form, subcategory: e.target.value })}
                        placeholder="e.g., NPK Fertilizers (optional)"
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>Description</label>
                    <input
                        value={form.description}
                        onChange={(e) => setForm({ ...form, description: e.target.value })}
                        placeholder="Description (optional)"
                    />
                </div>
                <button type="submit">Add Category</button>
                <button type="button" className="secondary" onClick={loadCategories}>
                    Refresh
                </button>
            </form>

            <table className="table">
                <thead>
                    <tr>
                        <th>Supercategory</th>
                        <th>Category</th>
                        <th>Subcategory</th>
                        <th>Description</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {categories.length === 0 && (
                        <tr>
                            <td colSpan={5} style={{ textAlign: 'center', color: '#6b7280' }}>
                                No categories found. Add some categories to get started.
                            </td>
                        </tr>
                    )}
                    {categories.map((cat) => (
                        <tr key={cat.id}>
                            <td><strong>{cat.supercategory}</strong></td>
                            <td>{cat.category}</td>
                            <td>{cat.subcategory || <span style={{ color: '#9ca3af' }}>—</span>}</td>
                            <td style={{ fontSize: '13px', color: '#4b5563' }}>{cat.description || '—'}</td>
                            <td className="actions">
                                <button className="secondary" onClick={() => deleteCategory(cat.id)}>
                                    Delete
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );
}
