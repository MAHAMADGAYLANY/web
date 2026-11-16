# SecureShop

SecureShop is a beginner-friendly Flask online store with SQLite orders and privacy-aware analytics.

## Install and run in VS Code

Open this folder in VS Code, then open **Terminal > New Terminal**:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Visit <http://127.0.0.1:5000>. The first run creates `database.db`, seeds four products, and creates `secret.key`.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` once in that terminal.

## Demo accounts

* Admin: `admin` / `admin123` — view full order details, add products, and view analytics.
* Analyst: `analyst` / `analyst123` — view analytics with masked email and phone values.

## Privacy technologies

* **Fernet:** name, email, phone, and address are encrypted before insertion into the `orders` table. The local key is stored in `secret.key`.
* **Masking:** Analyst dashboard values show only a small safe portion, such as `a***@example.com` and `*******123`.
* **Roles:** Flask sessions restrict product management and full customer details to Admins.
* **Differential privacy:** `diffprivlib` adds Laplace noise to the displayed sales estimate (`epsilon=1.0`); the exact sales total remains available only to the Admin view.
* **Pandas:** Converts order rows to a DataFrame for sales analysis.
* **DuckDB:** Queries the Pandas order data for aggregate order count and sales, a pattern that can be extended to larger datasets.

This is an educational prototype. A production store also needs password hashing, CSRF protection, HTTPS, secure key management, validation, and audit logging.
