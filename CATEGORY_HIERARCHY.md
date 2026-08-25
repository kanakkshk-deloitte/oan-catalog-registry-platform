# Category Hierarchy Documentation

## Overview

The OAN Catalog Registry Platform implements a **three-level category hierarchy** for product classification, providing flexible and granular organization of agricultural products.

## Category Levels

### 1. Supercategory (Top Level)
The broadest classification level representing major product domains.

**Examples:**
- Agricultural Inputs
- Farm Equipment
- Seeds & Planting Materials
- Animal Feed
- Crop Protection

### 2. Category (Mid Level)
A more specific classification within a supercategory.

**Examples:**
- Supercategory: `Agricultural Inputs`
  - Category: `Fertilizers`
  - Category: `Soil Amendments`
  - Category: `Growth Regulators`

- Supercategory: `Crop Protection`
  - Category: `Pesticides`
  - Category: `Fungicides`
  - Category: `Herbicides`

### 3. Subcategory (Bottom Level - Optional)
The most specific classification, providing detailed product types.

**Examples:**
- Supercategory: `Agricultural Inputs`
  - Category: `Fertilizers`
    - Subcategory: `NPK Fertilizers`
    - Subcategory: `Organic Fertilizers`
    - Subcategory: `Micronutrient Fertilizers`

## Database Schema

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    supercategory VARCHAR(128) NOT NULL,  -- Top-level category
    category VARCHAR(128) NOT NULL,        -- Mid-level category
    subcategory VARCHAR(128),              -- Specific category (optional)
    description TEXT,
    unit VARCHAR(32) NOT NULL,
    npk_ratio VARCHAR(32),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Usage

### Creating a Product with Category Hierarchy

```bash
curl -X POST http://localhost:8000/admin/products \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "OAN-PROD-1001",
    "name": "NPK Fertilizer 10-26-26",
    "supercategory": "Agricultural Inputs",
    "category": "Fertilizers",
    "subcategory": "NPK Fertilizers",
    "unit": "KG",
    "npk_ratio": "10-26-26",
    "description": "Balanced NPK fertilizer for crop growth",
    "is_active": true
  }'
```

### Search by Category

The Beckn search endpoint supports filtering by category hierarchy:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "context": {...},
    "message": {
      "intent": {
        "category": {
          "descriptor": {
            "name": "Fertilizers"
          }
        }
      }
    }
  }'
```

## Benefits

1. **Flexible Classification**: Three levels allow precise product categorization
2. **Easy Navigation**: Users can browse from broad to specific categories
3. **Better Search**: Enhanced filtering and discovery capabilities
4. **Scalability**: Easy to add new categories without restructuring
5. **Beckn Compatible**: Aligns with Beckn protocol category structures

## Example Product Classifications

| Product | Supercategory | Category | Subcategory |
|---------|--------------|----------|-------------|
| NPK 10-26-26 | Agricultural Inputs | Fertilizers | NPK Fertilizers |
| Organic Compost | Agricultural Inputs | Fertilizers | Organic Fertilizers |
| Urea | Agricultural Inputs | Fertilizers | Nitrogen Fertilizers |
| Pesticide X | Crop Protection | Pesticides | Insecticides |
| Wheat Seeds | Seeds & Planting Materials | Cereal Seeds | Wheat Varieties |

## Migration

Existing products are automatically migrated:
- `supercategory` is set to the current `category` value
- `category` remains unchanged
- `subcategory` is set to NULL

You can update products to use proper hierarchy via the admin portal.
