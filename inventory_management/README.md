# Inventory Management System (Django REST Framework)

A small but complete DRF backend covering: custom user auth, profile
management, category/product/customer CRUD, invoice creation with stock
tracking, field-level validation, permission-gated writes, and an
invoice summary report.

## 1. Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser   # creates a staff/admin user
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/api/`.
Django admin is at `http://127.0.0.1:8000/admin/`.

## 2. Auth model

- `accounts.CustomUser` extends `AbstractUser` with `phone_number`,
  `address`, `bio`, `avatar`, and a required unique `email`.
- `accounts.managers.CustomUserManager` implements `create_user` /
  `create_superuser`.
- Authentication is JWT (via `djangorestframework-simplejwt`).
- `is_staff=True` users act as the "admin/authorized" role for write
  access to catalog data (categories/products/customers) and can see
  and manage every invoice. Regular users can only manage their own
  invoices.

## 3. Endpoints

### Accounts (`/api/accounts/`)

| Method | Path                | Description                              | Auth        |
|--------|---------------------|-------------------------------------------|-------------|
| POST   | `register/`         | Create a new account                       | Public      |
| POST   | `login/`             | Obtain JWT access/refresh tokens           | Public      |
| POST   | `login/refresh/`     | Refresh an access token                    | Public      |
| GET    | `profile/`           | View own profile                           | Authenticated |
| PUT/PATCH | `profile/`        | Update own profile                         | Authenticated |

**Register example**
```json
POST /api/accounts/register/
{
  "username": "jdoe",
  "email": "jdoe@example.com",
  "password": "StrongPass123",
  "password2": "StrongPass123",
  "phone_number": "+8801711111111",
  "address": "Dhaka"
}
```

**Login example**
```json
POST /api/accounts/login/
{ "username": "jdoe", "password": "StrongPass123" }
```
Response: `{ "access": "...", "refresh": "..." }`. Send
`Authorization: Bearer <access>` on subsequent requests.

### Inventory (`/api/inventory/`)

| Method | Path                    | Description                         | Write access      |
|--------|-------------------------|--------------------------------------|--------------------|
| GET/POST | `categories/`         | List / create categories             | Staff only writes |
| GET/PUT/PATCH/DELETE | `categories/{id}/` | Retrieve / update / delete   | Staff only writes |
| GET/POST | `products/`           | List / create products               | Staff only writes |
| GET/PUT/PATCH/DELETE | `products/{id}/`   | Retrieve / update / delete   | Staff only writes |
| GET/POST | `customers/`          | List / create customers              | Staff only writes |
| GET/PUT/PATCH/DELETE | `customers/{id}/`  | Retrieve / update / delete  | Staff only writes |
| GET/POST | `invoices/`           | List / create invoices               | Any authenticated user (own invoices) |
| GET/PUT/PATCH/DELETE | `invoices/{id}/`   | Retrieve / update / delete  | Owner or staff |
| GET    | `report/`                | Invoice summary report               | Any authenticated user |

All list endpoints require authentication; only staff/admin users can
create, update, or delete categories, products, and customers
(`IsStaffOrReadOnly`). Any authenticated user can create invoices, but
can only modify or delete invoices they created; staff/admin can
manage all invoices (`IsOwnerOrStaff`).

**Create product (staff only)**
```json
POST /api/inventory/products/
{
  "name": "Wireless Mouse",
  "sku": "WM-001",
  "category": 1,
  "price": "19.99",
  "quantity_in_stock": 50
}
```

**Create invoice (nested items, stock is validated and decremented)**
```json
POST /api/inventory/invoices/
{
  "customer": 1,
  "items": [
    { "product": 1, "quantity": 3, "unit_price": "19.99" }
  ]
}
```
If any item's quantity exceeds the product's current stock, the
request is rejected with a 400 and a descriptive validation error.
On success, each product's `quantity_in_stock` is decremented
atomically.

**Report**
```
GET /api/inventory/report/
```
```json
{
  "total_invoices": 1,
  "total_sales": "59.97",
  "total_products_sold": 3,
  "invoices_by_status": { "pending": 1, "paid": 0, "cancelled": 0 }
}
```
Staff users get figures across all invoices; regular users get
figures scoped to invoices they created.

## 4. Validation highlights

- `RegisterSerializer` / `ProfileSerializer`: email uniqueness, phone
  number format, password confirmation + Django's built-in password
  validators.
- `ProductSerializer`: price must be > 0, stock quantity can't be
  negative, SKU can't be blank.
- `InvoiceItemSerializer`: quantity ≥ 1, unit price > 0.
- `InvoiceSerializer`: at least one item required; each item's
  quantity is checked against live product stock before the invoice
  is accepted.

## 5. Project layout

```
inventory_management/
├── config/          # settings, root urls, wsgi/asgi
├── accounts/         # CustomUser, manager, profile serializers/views
└── inventory/         # Category, Product, Customer, Invoice, InvoiceItem,
                        # serializers, permissions, viewsets, report view
```
