# ⚡ kartavya — Personal Productivity & Daily Task Management Workspace

**kartavya** is a high-performance, multi-user personal productivity workspace built with **Python**, **Streamlit**, **SQLAlchemy**, **Neon PostgreSQL**, and a **Neo-Brutalist Light Mode** design system.

It features Google OAuth authentication, strict database-level user data isolation, spreadsheet-style timeline task tracking, task priority & recurrence engines, date-specific focus planning, goal progress tracking, global reminders, GitHub-style productivity heatmaps, deterministic pattern insights, versioned data export/import, automatic backup rotation, and Alembic database migrations.

---

## ✨ End-User Experience

> [!IMPORTANT]
> **END USERS ONLY NEED TO OPEN THE WEBSITE AND LOG IN WITH GOOGLE.**
>
> End users do NOT need a Neon account, database credentials, Render account, Upstash, Redis, GitHub account, or any developer configuration whatsoever.
>
> **Flow**: Open kartavya → Google Login → Private Personal Workspace.

---

## 🛠️ Minimal Production Architecture

- **App Server**: Streamlit Community Cloud (`streamlit run app.py`)
- **Production Database**: Neon PostgreSQL
- **Authentication**: Native Streamlit Google OAuth (`st.login("google")`, `st.user`, `st.logout()`)
- **ORM & Migrations**: SQLAlchemy 2.0 & Alembic

---

## 🚀 Public Deployment Guide (Streamlit Community Cloud + Neon PostgreSQL)

Follow this 7-step guide to deploy kartavya to public web hosting:

### Step 1: Create a free Neon PostgreSQL Database
1. Go to [Neon.tech](https://neon.tech) and create a free project.
2. Copy your PostgreSQL connection string (`postgresql://user:password@ep-xxx.neon.tech/neondb?sslmode=require`).

### Step 2: Configure Google OAuth Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com).
2. Create an OAuth 2.0 Client ID (Web Application).
3. Set Authorized Redirect URIs to:
   `https://share.streamlit.io/oauth2callback` and `http://localhost:8501/oauth2callback`.

### Step 3: Push Repository to GitHub
1. Push your repository to GitHub.

### Step 4: Deploy to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and click **New App**.
2. Select your repository, branch, and set main file path to `app.py`.

### Step 5: Add Streamlit Secrets
In your Streamlit Cloud App Settings -> **Secrets**, paste:

```toml
KARTAVYA_ENV = "production"
KARTAVYA_MODE = "production"

[database]
url = "postgresql://user:password@ep-xxx.neon.tech/neondb?sslmode=require"

[google]
client_id = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
```

### Step 6: Run Database Migrations
Initialize the schema on your Neon PostgreSQL instance:
```bash
alembic upgrade head
```

### Step 7: Open Public kartavya URL
Launch your public app URL. Users can now open kartavya and sign in with Google seamlessly!

---

## 💻 Local Development Setup

1. **Clone & Virtual Environment**:
   ```bash
   git clone https://github.com/your-username/kartavya.git
   cd kartavya
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Local Database Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Launch Local Application**:
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501`.

---

## 🛡️ Security & Multi-User Data Isolation

- **Database-Level Ownership Enforcement**: Every query filters by `user_id = :authenticated_user_id`.
- **Session Security**: `logout_user()` purges all user-specific state from `st.session_state` before calling `st.logout()`.
- **Import Security**: Imported JSON data is reassigned to the current authenticated user; foreign user IDs are discarded.
- **Verification**: Verified with automated test suite `python scratch/test_phase9_suite.py` (100% pass rate across all 22 test items + E2E flow).

---

## 📄 License

Built with ❤️ by **Agrim Sharma** 🇮🇳. Distributed under the MIT License.
