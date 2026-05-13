# 🌾 KisanSetu

KisanSetu is a multimodal agricultural platform designed to bridge the digital divide for Indian farmers. It provides localized weather, Mandi prices, crop disease detection, and AI advisories via a smartphone app (Flutter) and a feature-phone IVR system.

## 🏗️ Current Architecture

Our infrastructure relies on a Monorepo design, utilizing containerization for consistent cross-platform development.

*   **Frontend:** Flutter (Mobile App)
*   **Backend:** FastAPI (Python 3.10)
*   **Database:** PostgreSQL 15
*   **Containerization:** Docker / Podman (with Compose)
*   **CI/CD:** GitHub Actions (Automated backend testing on PRs)

---

## 🚀 Getting Started (Local Development)

We use Docker/Podman to ensure the backend and database run identically on everyone's machine. You do not need to install Python or PostgreSQL locally.

### Prerequisites
*   Git
*   Docker Desktop (Windows/Mac) OR Podman (Linux/Fedora)

### Step 1: Clone the Repository
```bash
git clone [https://github.com/rishikesh737/KisanSetu.git](https://github.com/rishikesh737/KisanSetu.git)
cd KisanSetu
git checkout dev
