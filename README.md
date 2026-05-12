# 🌾 KisanSetu

KisanSetu is a multimodal agricultural platform designed to bridge the digital divide for Indian farmers. It provides localized weather, Mandi prices, **offline rice disease detection**, and AI advisories via a smartphone app (Flutter) and a feature-phone IVR system.

## 🏗️ Current Architecture

Our infrastructure relies on a Monorepo design, utilizing containerization for consistent cross-platform development.

*   **Frontend:** Flutter (Mobile App) with **on-device TFLite inference**
*   **Backend:** FastAPI (Python 3.10) — Weather & Mandi APIs only
*   **Database:** PostgreSQL 15
*   **AI/ML:** MobileNetV2 fine-tuned on 5 rice disease classes, exported as TFLite
*   **Containerization:** Docker / Podman (with Compose)
*   **CI/CD:** GitHub Actions (Automated backend testing on PRs)

## 🌿 Rice Disease Scanner (Offline)

The scanner runs **100% offline** on the farmer's device:

*   **Model:** MobileNetV2 → TFLite (~2-4 MB), bundled in the APK
*   **Classes:** Rice Blast, Bacterial Blight, Brown Spot, Tungro, Healthy
*   **Weather Fusion:** Local weather data adjusts disease probabilities (e.g., Rice Blast boosted during high humidity)
*   **Guardrail:** >85% confidence threshold rejects out-of-distribution scans

---

## 🚀 Getting Started (Local Development)

We use Docker/Podman to ensure the backend and database run identically on everyone's machine. You do not need to install Python or PostgreSQL locally.

### Prerequisites
*   Git
*   Docker Desktop (Windows/Mac) OR Podman (Linux/Fedora)
*   Flutter SDK (for the mobile app)

### Step 1: Clone the Repository
```bash
git clone https://github.com/rishikesh737/KisanSetu.git
cd KisanSetu
git checkout dev
```

### Step 2: Train the Rice Model (Optional — pre-trained model may be bundled)
```bash
cd ai_services/disease_detection
pip install tensorflow numpy Pillow
python train_rice_expert.py
cp rice_expert_v1.tflite ../../app/assets/models/
```

### Step 3: Run the Flutter App
```bash
cd app
flutter pub get
flutter run
```
