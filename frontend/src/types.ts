export type AdminView = 'dashboard' | 'products' | 'categories' | 'providers' | 'offerings';
export type ProviderView = 'dashboard' | 'catalog' | 'my-offerings';

export type Product = {
  product_id: string;
  name: string;
  supercategory: string;
  category: string;
  subcategory?: string;
  description?: string;
  unit: string;
  npk_ratio?: string;
  is_active: boolean;
};

export type Category = {
  id: number;
  supercategory: string;
  category: string;
  subcategory?: string;
  description?: string;
  is_active: boolean;
};

export type Provider = {
  provider_code: string;
  provider_name: string;
  login_username: string;
  status: 'PENDING' | 'APPROVED' | 'ACTIVE' | 'SUSPENDED' | 'DEACTIVATED';
};

export type Offering = {
  listing_id: string;
  product_id: string;
  product_name: string;
  provider_code: string;
  provider_name: string;
  sku: string;
  price: number;
  stock: number;
  availability: 'ACTIVE' | 'INACTIVE' | 'OUT_OF_STOCK';
};
