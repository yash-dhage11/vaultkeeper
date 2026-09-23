# 🔐 VaultKeeper — Encrypted Password Manager

A simple, secure password manager built with Flask. Store your site credentials
in an encrypted vault, protected behind a master login.

## Features

- User registration & login (passwords hashed with Werkzeug)
- Each saved password encrypted with Fernet (symmetric AES-based encryption) before hitting the database
- Add / view / delete vault entries
- Show/hide password toggle on the dashboard
- Clean Bootstrap 5 UI

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Encryption:** `cryptography` library (Fernet)
- **Frontend:** HTML, Bootstrap 5, vanilla JS

## Project Structure

```
vaultkeeper/
├── app.py                  # Main Flask application
├── requirements.txt
├── instance/                # DB + encryption key get created here at runtime
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── add_item.html
└── static/
    ├── css/style.css
    └── js/script.js
```

## How to Run

1. Extract this zip and open a terminal inside the `vaultkeeper` folder.

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Mac/Linux
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the app:
   ```
   python app.py
   ```

5. Open your browser at `http://127.0.0.1:5000`

The database and encryption key are auto-created on first run inside the
`instance/` folder.

## How the Encryption Works

- On first run, a random Fernet key is generated and saved to `instance/secret.key`.
- Every password you save is encrypted with this key before being stored in SQLite.
- When you view your dashboard, passwords are decrypted on the fly — they're
  never stored in plain text in the database.

⚠️ **Note:** This is a learning/portfolio project. For real production use,
you'd want to move the Flask `secret_key` and encryption key out of the code/
disk into a proper secrets manager, add HTTPS, and add rate-limiting on login.

## Possible Extensions (good talking points for a viva/demo)

- Password strength checker while adding an entry
- Auto-generate strong passwords
- Search/filter vault items
- Export vault as encrypted backup file
- Two-factor authentication on login

---
Built as a BCA project — feel free to customize the branding, colors, and
add your name/college details wherever needed.
