# Centralized Campus Drive Management System

## 📖 About The Project
CareerFlow is a commercial-grade Applicant Tracking System (ATS) tailored specifically for the university ecosystem. It replaces the chaos of scattered spreadsheets, missed emails, and repetitive Google Forms with a centralized, role-based platform. 

It is designed with strict **Data Isolation**, **State Machine Integrity**, and a **Two-Step Deletion Pipeline** to ensure secure and efficient placement drives for Students, HR Professionals, and College Administrators.

## ✨ Key Features

### 🎓 For Students
* **Single-Click Applications:** Build a profile once (Resume, Branch, GPA) and apply to multiple drives instantly.
* **Real-Time Tracking:** Transparent pipeline visibility (Applied → Shortlisted → Written Test → Placed).
* **Modern UI/UX:** Engaging, responsive interface featuring custom Aurora mesh gradients and fluid animations.

### 🏢 For HR & Companies
* **Dedicated Dashboards:** A bird's-eye view of active drives and applicant metrics.
* **Full CRUD Lifecycle:** Create, Read, Update, and manage job postings independently.
* **Enterprise Safety Net (Soft Delete):** A two-step deletion pipeline. Closing a drive prevents new applications but preserves historical data. A second confirmation is required for a permanent hard-purge.

### 🛡️ For College Admin (God Mode)
* **Role-Based Access Control (RBAC):** Strict boundaries preventing URL-guessing or cross-role data leaks.
* **Profile Verification:** Companies cannot post jobs until manually verified by the Admin.
* **State Locks:** Students who accept an offer are automatically locked from applying to further drives to ensure fair opportunity distribution.

## 🛠️ Tech Stack
* **Frontend:** HTML5, CSS3 (Custom Variables/Animations), Bootstrap 5, FontAwesome
* **Backend:** Python, Django
* **Database:** SQLite (Development)
* **Architecture:** Self-Contained Monolith (MVC/MVT Pattern)

## 🚀 Local Installation & Setup

To run CareerFlow on your local machine, follow these steps:
**1. Clone the repository:**
`git clone https://github.com/meghmala-code/Centralized-Campus-Drive-Management-System.git`

**2. Navigate to the project directory:**
`cd placement-portal`

**3. Create a virtual environment:**
`python -m venv .venv`

**4. Activate the virtual environment:**
* On Windows: `.venv\Scripts\activate`
* On Mac/Linux: `source .venv/bin/activate`

**5. Install dependencies:**
`pip install -r requirements.txt`

**6. Apply database migrations:**
`python manage.py migrate`

**7. Run the development server:**
`python manage.py runserver`
