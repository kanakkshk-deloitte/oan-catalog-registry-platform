# OAN Catalog Registry Platform

A comprehensive catalog management system for the Open Agriculture Network (OAN) with Beckn protocol integration, supporting provider onboarding, product management, and catalog discovery.

## 🚀 Features

- **Provider Management**: Onboard and manage agricultural product providers
- **Product Catalog**: Multi-level category hierarchy (supercategory → category → subcategory)
- **Offerings Management**: Providers can list products with pricing and inventory
- **Beckn Protocol Integration**: Standard-compliant search API for catalog discovery
- **Role-Based Access**: Separate Admin and Provider portals
- **Authentication**: Keycloak-based OAuth2/JWT authentication
- **RESTful API**: FastAPI backend with comprehensive endpoints

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Category Hierarchy](#category-hierarchy)
- [Authentication](#authentication)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │ React + TypeScript + Vite
│   (Port 5173)   │ Role-based UI (Admin/Provider)
└────────┬────────┘
         │
┌────────▼────────┐
│   Backend       │ FastAPI + SQLAlchemy
│   (Port 8000)   │ REST API + Beckn Protocol
└────────┬────────┘
         │
    ┌────┴────┬────────┬─────────┐
    │         │        │         │
┌───▼───┐ ┌──▼──┐ ┌───▼────┐ ┌──▼──┐
│PostgreSQL Redis│ Keycloak│ │Other│
│ (5434)│(6380)│ │ (8082) │ │Services│
└───────┘ └─────┘ └────────┘ └─────┘
```

## 📦 Prerequisites

- **Docker** and **Docker Compose** (v2.0+)
- **Git**
- **Ports Available**: 5173, 8000, 8081, 8082, 5434, 6380

### System Requirements
- OS: Linux/macOS/Windows with WSL2
- RAM: 4GB minimum, 8GB recommended
- Disk Space: 5GB free space

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd oan-catalog-registry-platform
```

### 2. Verify Docker Installation

```bash
docker --version
docker compose version
```

## ▶️ Running the Project

### Quick Start (Production Mode)

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### Development Mode

```bash
# Build and start with live reload
docker compose up --build

# Start specific service
docker compose up backend

# Restart a service
docker compose restart frontend
```

### Accessing the Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | See below |
| **Backend API** | http://localhost:8000 | N/A |
| **API Docs** | http://localhost:8000/docs | N/A |
| **Keycloak Admin** | http://localhost:8082 | admin / admin |

### Default User Accounts

**Admin Account:**
- Username: `admin_user`
- Password: `admin123`
- Role: Admin (full access)

**Provider Accounts:**
- Username: `provider_abc` / Password: `provider123`
- Username: `provider_xyz` / Password: `provider123`
- Role: Provider (manage own offerings)

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration
Located in `docker-compose.yml`:

```yaml
environment:
  DATABASE_URL: postgresql+psycopg2://oan:oan@postgres:5432/oan_catalog
  REDIS_URL: redis://redis:6379/0
  KEYCLOAK_BASE_URL: http://keycloak:8080
  KEYCLOAK_REALM: oan
  KEYCLOAK_CLIENT_ID: oan-portal
  KEYCLOAK_CLIENT_SECRET: oan-portal-secret
  AUTH_ENABLED: 'true'
```

#### Frontend Configuration

```yaml
environment:
  VITE_API_BASE: /api  # Proxied to backend:8000
```

### Database Configuration

PostgreSQL database `oan_catalog` is automatically created with:
- User: `oan`
- Password: `oan`
- Port: 5434 (external), 5432 (internal)

## 📚 API Documentation

### Interactive API Docs

Visit http://localhost:8000/docs for Swagger UI documentation.

### Key Endpoints

#### Authentication
```bash
POST /auth/token
Content-Type: application/json

{
  "username": "admin_user",
  "password": "admin123"
}
```

#### Admin Endpoints

**Create Product:**
```bash
POST /admin/products
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_id": "OAN-PROD-1001",
  "name": "NPK Fertilizer",
  "supercategory": "Agricultural Inputs",
  "category": "Fertilizers",
  "subcategory": "NPK Fertilizers",
  "unit": "KG",
  "npk_ratio": "10-26-26",
  "is_active": true
}
```

**Create Provider:**
```bash
POST /admin/providers
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider_code": "ABC",
  "provider_name": "ABC Agriculture",
  "login_username": "provider_abc",
  "login_password": "provider123"
}
```

`login_password` is optional; if omitted, backend uses default `provider123`.

#### Provider Endpoints

**View Available Products:**
```bash
GET /provider/catalog
Authorization: Bearer <token>
```

**Create Offering:**
```bash
POST /provider/offerings
Authorization: Bearer <token>
Content-Type: application/json

{
  "listing_id": "ABC-LIST-001",
  "sku": "ABC-NPK-001",
  "product_id": "OAN-PROD-1001",
  "price": 850.00,
  "stock": 500,
  "availability": "ACTIVE"
}
```

#### Beckn Protocol Endpoint

**Search Catalog:**
```bash
POST /search
Content-Type: application/json

{
  "context": {
    "domain": "weather-advisory:oan",
    "country": "IND",
    "city": "Bengaluru",
    "action": "search",
    "version": "1.1.0",
    "bap_id": "bap-network",
    "bap_uri": "http://onix-adapter:8081/bap/receiver",
    "transaction_id": "txn-123",
    "message_id": "msg-123",
    "timestamp": "2026-08-25T10:00:00Z"
  },
  "message": {
    "intent": {
      "item": {
        "descriptor": {
          "name": "fertilizer"
        }
      }
    }
  }
}
```

**Search Request (from BAP to BPP):**
```json
{
  "context": {
    "domain": "agriculture",
    "country": "IND",
    "city": "Bengaluru",
    "action": "search",
    "core_version": "1.1.0",
    "bap_id": "example-bap.com",
    "bap_uri": "https://example-bap.com",
    "transaction_id": "a9aaecca-10b7-4d19-b640-b047a7c62196",
    "message_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2026-08-25T10:30:00.000Z"
  },
  "message": {
    "intent": {
      "item": {
        "descriptor": {
          "name": "fertilizer"
        }
      }
    }
  }
}
```

**ON_SEARCH Response (from BPP to BAP):**
```json
{
  "context": {
    "domain": "agriculture",
    "country": "IND",
    "city": "Bengaluru",
    "action": "on_search",
    "core_version": "1.1.0",
    "bap_id": "example-bap.com",
    "bap_uri": "https://example-bap.com",
    "bpp_id": "oan-catalog-registry.local",
    "bpp_uri": "https://oan-catalog-registry.local",
    "transaction_id": "a9aaecca-10b7-4d19-b640-b047a7c62196",
    "message_id": "987f6543-e21c-34d5-b654-789012345678",
    "timestamp": "2026-08-25T10:30:01.234Z"
  },
  "message": {
    "catalog": {
      "descriptor": {
        "name": "OAN Catalog Registry"
      },
      "providers": [
        {
          "id": "ABC-AGRI-001",
          "descriptor": {
            "name": "ABC Agriculture"
          },
          "items": [
            {
              "id": "LIST-ABC-001",
              "descriptor": {
                "name": "NPK Fertilizer 10-26-26"
              },
              "category_id": "Fertilizers",
              "price": {
                "currency": "INR",
                "value": "850.00"
              },
              "quantity": {
                "available": {
                  "count": "500"
                }
              },
              "tags": {
                "product_id": "OAN-PROD-1001",
                "sku": "ABC-NPK-001",
                "availability": "ACTIVE"
              }
            },
            {
              "id": "LIST-ABC-002",
              "descriptor": {
                "name": "Organic Fertilizer"
              },
              "category_id": "Fertilizers",
              "price": {
                "currency": "INR",
                "value": "750.00"
              },
              "quantity": {
                "available": {
                  "count": "300"
                }
              },
              "tags": {
                "product_id": "OAN-PROD-1002",
                "sku": "ABC-ORG-001",
                "availability": "ACTIVE"
              }
            }
          ]
        },
        {
          "id": "XYZ-AGRO-002",
          "descriptor": {
            "name": "XYZ Agro Products"
          },
          "items": [
            {
              "id": "LIST-XYZ-001",
              "descriptor": {
                "name": "NPK Fertilizer 10-26-26"
              },
              "category_id": "Fertilizers",
              "price": {
                "currency": "INR",
                "value": "900.00"
              },
              "quantity": {
                "available": {
                  "count": "250"
                }
              },
              "tags": {
                "product_id": "OAN-PROD-1001",
                "sku": "XYZ-NPK-001",
                "availability": "ACTIVE"
              }
            }
          ]
        }
      ]
    }
  }
}
```

### Beckn Search Behavior

- The `/search` endpoint is permissive and always returns immediate ACK.
- Payload validation errors are logged for debugging and do not block ACK.
- Search processing runs asynchronously and posts `on_search` callback later.

### ONIX Callback Routing

The backend callback URL is built using the same pattern as OAN Provider Service:

- For domains `schemes:oan` or `schemes:vistaar`:
  - Use `x-forwarded-host` when present: `http://<forwarded-host>/bpp/caller/on_search`
  - Fallback: `http://onix-adapter2:8081/bpp/caller/on_search`
- For other domains:
  - If `bap_uri` contains `/bap/receiver`, map to `/bpp/caller/on_search`
  - Else append `/on_search` to `bap_uri`

### BPP Proxy Path (ONIX)

For ONIX BPP receiver routing, this project includes an internal proxy service:

- Service name: `oan-bpp-proxy`
- Internal URL used by ONIX routing: `http://oan-bpp-proxy:8080/search`

This helps normalize transport behavior between ONIX and the backend.

## 🏷️ Category Hierarchy

The platform implements a **three-level category hierarchy** for flexible product classification:

### Hierarchy Levels

1. **Supercategory** (Top Level): Broadest classification
   - Examples: "Agricultural Inputs", "Farm Equipment", "Seeds & Planting Materials"

2. **Category** (Mid Level): More specific classification
   - Examples: "Fertilizers", "Pesticides", "Growth Regulators"

3. **Subcategory** (Bottom Level - Optional): Most specific classification
   - Examples: "NPK Fertilizers", "Organic Fertilizers", "Micronutrient Fertilizers"

### Example Classification

```
Supercategory: Agricultural Inputs
  └─ Category: Fertilizers
      ├─ Subcategory: NPK Fertilizers
      ├─ Subcategory: Organic Fertilizers
      └─ Subcategory: Micronutrient Fertilizers
```

### Benefits

- **Flexible Organization**: Three levels allow precise categorization
- **Easy Navigation**: Browse from broad to specific categories
- **Enhanced Search**: Better filtering and discovery
- **Scalable**: Add new categories without restructuring
- **Beckn Compatible**: Aligns with Beckn protocol standards

See [CATEGORY_HIERARCHY.md](./CATEGORY_HIERARCHY.md) for detailed documentation.

## 🔐 Authentication

### Login Flow

1. User submits credentials to `/auth/token`
2. Backend exchanges credentials with Keycloak
3. Keycloak returns JWT access token
4. Frontend stores token and includes in subsequent requests
5. Backend validates token for protected endpoints

### Token Format

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

### Provider Password Change

- Provider users can change their password from the Provider Portal using the `Change Password` button.
- The portal prompts for current and new password and calls backend API `POST /auth/change-password`.
- Backend first verifies current password, then updates password using Keycloak Admin API.
- If current password is wrong or password policy fails, the API returns an error message.

### Roles

- **admin**: Full access - manage products/providers/offerings
- **provider**: Limited access - manage own offerings, view catalog

## 👨‍💻 Development

### Project Structure

```
oan-catalog-registry-platform/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── auth.py          # Authentication logic
│   │   ├── config.py        # Configuration
│   │   └── database.py      # Database connection
│   ├── alembic/             # Database migrations
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main component
│   │   ├── AdminPortal.tsx  # Admin interface
│   │   ├── ProviderPortal.tsx # Provider interface
│   │   ├── types.ts         # TypeScript types
│   │   ├── api.ts           # API utilities
│   │   └── auth.ts          # Auth utilities
│   ├── package.json         # Node dependencies
│   └── Dockerfile
├── infra/keycloak/
│   └── realm-export.json    # Keycloak configuration
├── docker-compose.yml       # Service orchestration
├── README.md                # This file
└── CATEGORY_HIERARCHY.md    # Category documentation
```

### Database Migrations

**Create new migration:**
```bash
cd backend
alembic revision -m "description"
```

**Apply migrations:**
```bash
docker compose exec backend alembic upgrade head
```

**Rollback migration:**
```bash
docker compose exec backend alembic downgrade -1
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using the port
sudo lsof -i :5173

# Stop conflicting service or change port in docker-compose.yml
```

**Database Connection Error:**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# View database logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

**Frontend Not Loading:**
```bash
# Clear browser cache (Ctrl+Shift+R)
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
docker compose up -d --build frontend
```

**Authentication Fails:**
```bash
# Verify Keycloak is running
docker compose ps keycloak

# Reset Keycloak
docker compose down keycloak
docker compose up -d keycloak
```

### Logs and Debugging

```bash
# View all logs
docker compose logs

# Follow specific service logs
docker compose logs -f backend

# View last 100 lines
docker compose logs --tail=100 backend

# Container shell access
docker compose exec backend bash
docker compose exec frontend sh
```

### Reset Everything

```bash
# Stop and remove all containers
docker compose down

# Remove volumes (CAUTION: deletes all data)
docker compose down -v

# Fresh start
docker compose up -d --build
```

## 📖 Additional Documentation

- [Category Hierarchy](./CATEGORY_HIERARCHY.md) - Detailed category system documentation
- [API Reference](http://localhost:8000/docs) - Interactive API documentation
- [Beckn Protocol](https://developers.becknprotocol.io/) - Official Beckn documentation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team

---

**Version:** 1.0.0  
**Last Updated:** 2026-08-25
