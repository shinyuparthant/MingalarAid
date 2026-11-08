# Mingalar Aid

A starter volunteer and donation management web application built with Python Flask, SQLite, HTML, CSS, and JavaScript.

## Features

- Anonymous disaster report submission
- Administrator review, approval, and rejection
- Public listing of approved disasters
- Donation offers (money or supplies)
- Volunteer registration
- Administrator dashboard for reviewing reports, donations, and volunteers

## Requirements

- Python 3.10 or newer
- pip

## Run locally

1. Open this folder in PyCharm (or another editor).
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set administrator credentials before starting the app.

   **Windows PowerShell:**
   ```powershell
   $env:ADMIN_USERNAME="admin"
   $env:ADMIN_PASSWORD="choose-a-strong-password"
   $env:SECRET_KEY="replace-this-with-a-long-random-secret"
   python app.py
   ```

   **Windows Command Prompt:**
   ```cmd
   set ADMIN_USERNAME=admin
   set ADMIN_PASSWORD=choose-a-strong-password
   set SECRET_KEY=replace-this-with-a-long-random-secret
   python app.py
   ```

5. Open http://127.0.0.1:5000 in your browser.
6. Open http://127.0.0.1:5000/admin/login to sign in to the admin area.

The database file `mingalar_aid.db` is created automatically on first run.

## Important notes

- This is a local development starter, not a production emergency-response service.
- The donation form records an offer; it does not process payments.
- The evidence field accepts an optional URL. File uploads can be added as a later feature.
- Before public deployment, add CSRF protection, rate limiting, secure HTTPS configuration, stronger authentication (preferably hashed passwords and individual admin accounts), privacy notices, and a safe process for handling personal contact information.
- Anonymous reports are not automatically verified. Admins must check each report before it appears publicly.
- Do not use this site as a substitute for contacting emergency services.

## Database choice

SQLite is used to keep setup simple. It is a real relational database and is suitable for a prototype or school project. The application can later be adapted to Microsoft SQL Server using `pyodbc` and SQL Server connection settings.
