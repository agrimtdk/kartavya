# kartavya

**kartavya** is a high-performance, multi-user personal productivity workspace built with **Python**, **Streamlit**, **SQLAlchemy**, and **PostgreSQL**. It features a clean Neo-Brutalist Light Mode design system.

## Features

- **Google OAuth Authentication:** Secure, native Google login for all users.
- **Strict Data Isolation:** Database-level enforcement guarantees zero data leakage between users.
- **Spreadsheet-Style Timeline:** Intuitive daily task tracking with interactive checkboxes and completion badges.
- **Task Management:** Priority tagging, recurrence engines, and date-specific focus planning.
- **Goal Progress Tracking:** Visualize long-term objectives alongside daily tasks.
- **Global Reminders:** Keep track of urgent deadlines and upcoming events.
- **Analytics & Insights:** GitHub-style productivity heatmaps and deterministic pattern insights.
- **Data Portability:** Versioned data export/import with automatic backup rotation.

## Technology Stack

- **Frontend/Backend:** Streamlit (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 & Alembic

## Local Setup

1. **Clone & Virtual Environment:**
   ```bash
   git clone https://github.com/your-username/kartavya.git
   cd kartavya
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Local Database Migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Launch Local Application:**
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501`.

## License

Built by **Agrim Sharma**. Distributed under the MIT License.
