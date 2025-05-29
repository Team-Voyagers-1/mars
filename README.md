# 🛰️ Voyager Backend – Django REST API

This is the backend service for **Project Voyager** — a tool designed to simplify the Software Development Life Cycle (SDLC).

### 🚀 What is Voyager?

**Voyager** automates the process of story creation and management in JIRA. Given business requirements, documents, or even Excel files, the system:

- Analyzes and extracts user stories and epics
- Enhances story descriptions with more clarity
- Automatically creates stories/epics on JIRA
- Modifies any required JIRA fields
- Manages status based on comments
- Removes the manual work to review tasks

This backend handles the authentication and foundational logic for that automation using **Django REST Framework** and **MongoDB**.

---

## 📦 Requirements

- Python 3.8+
- pip
- MongoDB running locally or on the cloud (e.g. Atlas)

## 🛠️ Part 2: Local Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/Team-Voyagers-1/mars.git
cd mars

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
touch .env

# env content example:
MONGO_URI=mongodb://localhost:27017
DB_NAME=voyager_db


# 6. Run the Django server
python manage.py runserver
# Server will be available at: http://localhost:8000

```

---

## 📘 Part 3: Feature Documentation

### 💻 API Feature Documentation

#### 🔐 Authentication

| Method | Endpoint         | Body                         | Description            |
| ------ | ---------------- | ---------------------------- | ---------------------- |
| POST   | `/api/register/` | `{ "username", "password" }` | Register a user        |
| POST   | `/api/login/`    | `{ "username", "password" }` | Login, returns user_id |

**🔐 Response on Login**

```json
{
  "message": "Login successful",
  "token": "your_jwt_token_here"
}
```
