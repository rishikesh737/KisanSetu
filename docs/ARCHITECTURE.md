# 🏛️ KisanSetu System Architecture

KisanSetu relies on a distributed, API-first architecture designed to serve both high-end smartphones and basic feature phones simultaneously.

## 🔄 High-Level Data Flow

1. **The Client Layer**
   * **Smartphone Users (Flutter App):** Communicates via REST API to the backend. Uses a local SQLite database for offline caching.
   * **Feature Phone Users (IVR):** Dials a Twilio/Exotel number. The voice gateway sends an HTTP POST request to our backend webhook.

2. **The API Gateway (FastAPI)**
   * Acts as the central brain. It receives requests from both the mobile app and the IVR system.
   * Handles authentication, routing, and business logic.

3. **The Data Layer (PostgreSQL)**
   * Stores persistent data: `Farmers` (profiles), `MarketPrices` (daily cache), and `DiseaseScans` (history).

4. **The AI Microservices**
   * **Computer Vision:** A localized CNN model (ResNet/MobileNet) loaded via PyTorch/TensorFlow to analyze leaf images sent from the mobile app.
   * **Advisory System:** A RAG (Retrieval-Augmented Generation) pipeline using a local LLM and Vector Database (ChromaDB/FAISS) containing ICAR documents.

## 📡 External Integrations
*   **Weather:** OpenWeatherMap / IMD API (Fetched based on farmer's district).
*   **Market Prices:** Agmarknet API (Parsed and cached daily).
