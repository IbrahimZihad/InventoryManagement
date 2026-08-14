# Inventory Management System (Django REST Framework)

A REST API for managing users, products, customers, and sales invoices, with
JWT authentication and role-based permissions (staff vs. regular users).

## Features

- Custom `User` model (`AbstractUser` + custom manager), unique email
- `UserProfile` (1-to-1, auto-created via signal) with view/update endpoint
- Category & Product CRUD (read = any authenticated user, write = staff only)
- Customer CRUD (any authenticated user)
- Invoice + line-item ("InvoiceItem") creation with automatic stock
  deduction/restock, ownership-based permissions
- Invoice report/summary endpoint (total invoices, total sales, total
  products sold, average invoice value)
- JWT auth via `djangorestframework-simplejwt` (access + refresh + blacklist)
- Field-level serializer validation throughout

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations accounts inventory
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Auth flow

There are two equivalent ways to authenticate — pick whichever fits your client.

### Option A: `/login/` (recommended — body tokens + httponly cookies)

1. `POST /api/accounts/register/` — create an account (public).
2. `POST /api/accounts/login/` — body `{"username": "...", "password": "..."}`.
   Returns `{"access": "...", "refresh": "...", "user": {...}}` in the JSON
   body **and** sets `access_token` / `refresh_token` as httponly cookies.
   - Browser-based clients can rely on the cookies alone — no manual
     `localStorage`/`sessionStorage` handling needed, and the cookies aren't
     readable by JS (XSS-resistant).
   - Script/mobile clients can instead take `access`/`refresh` from the body
     and manage storage themselves.
3. Send `Authorization: Bearer <access>` on every subsequent request (or,
   for browser clients using the cookie, nothing extra is needed as long as
   requests are same-site).
4. `POST /api/accounts/token/refresh/` — with `{"refresh": "..."}` in the
   body, or no body at all if the `refresh_token` cookie is already set.
   Returns a new `access` (and rotated `refresh`, since
   `ROTATE_REFRESH_TOKENS=True`) and re-sets the cookies.
5. `POST /api/accounts/logout/` — blacklists the refresh token and clears
   both cookies. Requires `Authorization: Bearer <access>`.

### Option B: plain `/token/` (SimpleJWT default, no cookies)

1. `POST /api/accounts/token/` — body `{"username": "...", "password": "..."}`
   returns `{"access": "...", "refresh": "..."}` in the body only (no
   cookies set). Useful for pure API clients that manage their own storage.
2. `POST /api/accounts/token/refresh/` — body `{"refresh": "..."}` returns a
   new access token.
3. `POST /api/accounts/token/verify/` — body `{"token": "..."}` checks a
   token is still valid.

Both options issue the same kind of JWT and work interchangeably — you can
log in with `/login/` and still refresh with a bare `{"refresh": ...}` body
against `/token/refresh/`, for example.

## Endpoints

### Accounts (`/api/accounts/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `register/` | Create a new user | Public |
| GET/PUT/PATCH | `me/` | View/update own profile (nested `profile` object) | Any user |
| POST | `change-password/` | Change own password | Any user |
| POST | `login/` | Log in; returns JWTs in body + sets httponly cookies | Public |
| POST | `logout/` | Blacklist refresh token + clear cookies | Any user |
| POST | `token/` | Obtain JWT access + refresh tokens (body only, no cookies) | Public |
| POST | `token/refresh/` | Refresh access token (body or `refresh_token` cookie); re-sets cookies | Public |
| POST | `token/verify/` | Verify a token | Public |

### Inventory (`/api/inventory/`)
| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `categories/`, `categories/{id}/` | List/retrieve categories | Any user |
| POST/PUT/PATCH/DELETE | `categories/...` | Manage categories | Staff only |
| GET/POST/PUT/PATCH/DELETE | `customers/...` | Manage customers | Any user |
| GET | `products/`, `products/{id}/` | List/retrieve products (filter `?category=`, search `?search=`) | Any user |
| POST/PUT/PATCH/DELETE | `products/...` | Manage products | Staff only |
| GET | `invoices/`, `invoices/{id}/` | List/retrieve invoices (own only, unless staff) | Any user |
| POST | `invoices/` | Create invoice with nested `items` | Any user |
| PUT/PATCH/DELETE | `invoices/{id}/` | Update/delete invoice | Owner or staff |
| GET | `invoices/report/` | Summary: total invoices, total sales, total products sold, avg. invoice value | Any user (scoped to own data unless staff) |

### Example: create an invoice

```json
POST /api/inventory/invoices/
{
  "customer": 1,
  "status": "PENDING",
  "items": [
    {"product": 3, "quantity": 2, "unit_price": "19.99"},
    {"product": 5, "quantity": 1, "unit_price": "49.50"}
  ]
}
```

Stock (`quantity_in_stock`) on each referenced product is validated (can't
oversell) and automatically decremented on create / adjusted on update.

## Design notes

- `InvoiceItem.unit_price` is captured at sale time so historic invoices
  aren't retroactively affected by later `Product.price` changes.
- `Invoice.invoice_number` is auto-generated (`INV-XXXXXXXXXX`) and read-only.
- Non-staff users only ever see/manage their own invoices; staff see and can
  manage everything system-wide (`IsOwnerOrAdmin` / `IsAdminOrReadOnly`).
- Deleting a `Category` or `Product` that's referenced elsewhere is blocked
  (`on_delete=PROTECT`) to preserve invoice history integrity.
