# Mingalar Aid

Mingalar Aid is a Flask and SQLite disaster-relief prototype for verified reports, monetary donations, and volunteer registration.

## Project structure

```text
MingalarAid/
├── MingalarAid.Frontend/
│   ├── static/                 # CSS, JavaScript, and image assets
│   └── templates/              # Jinja HTML templates
├── MingalarAid.Backend/
│   ├── api/                    # HTTP routes, sessions, and responses
│   ├── service/                # Validation and business rules
│   ├── dataaccess/             # SQLite setup and repositories
│   ├── data/mingalar_aid.db    # Local SQLite database
│   ├── app.py                  # Flask application entry point
│   ├── config.py               # Paths and environment configuration
│   └── requirements.txt
├── .gitignore
└── README.md
```

## Main flows

- Public users can view approved disaster reports, approved donations, and volunteers.
- Signed-in users can submit disaster reports, monetary donations, and volunteer registrations.
- Administrators review disaster reports and donations before they appear publicly.
- Donations support KBZPay and WavePay in MMK and can be filtered by date, month, year, or disaster event.
- The frontend includes English/Myanmar language switching and light/dark themes.

## Run locally

From the repository root in Windows PowerShell:

```powershell
cd MingalarAid.Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SECRET_KEY="replace-with-a-long-random-value"
python app.py
```

Open <http://127.0.0.1:5000>.

Development accounts:

- Admin: `admin` / `admin@123`
- User: `user` / `user@123`

These defaults are for local development only and must be replaced before deployment.

## Production notes

Before public deployment, add CSRF protection, rate limiting, production WSGI hosting, HTTPS, configurable account management, privacy controls, receipt verification, and secure secret management.
