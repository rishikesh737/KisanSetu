# 🗄️ Database Schemas

Our primary database is **PostgreSQL 15**, managed via **SQLAlchemy** ORM and **Alembic** for migrations.

## Core Tables (MVP)

### 1. `farmers`
Stores the personalization profile for each user.
*   `id` (Primary Key)
*   `phone_number` (Unique, used for login/IVR identification)
*   `language` (e.g., 'mr', 'kok', 'hi', 'en')
*   `state` & `district` (Used to filter weather and market prices)
*   `primary_crop` (Optional preference)

### 2. `market_prices`
A caching table. To avoid rate-limiting from government APIs, our backend fetches Mandi prices once daily and stores them here.
*   `id` (Primary Key)
*   `state` & `district` (For fast querying)
*   `market` (Specific Mandi name)
*   `commodity` (e.g., Wheat, Tomato)
*   `modal_price` (The most common trading price of the day)

### 3. `disease_scans`
Maintains a history of AI disease predictions for the farmer.
*   `id` (Primary Key)
*   `farmer_id` (Foreign Key -> farmers.id)
*   `image_path` (Location of the uploaded image)
*   `detected_disease` (String output from the CNN model)
*   `confidence_score` (Float representing AI certainty)

---

## 📱 Offline Caching (Mobile App)
The Flutter mobile application maintains a parallel **SQLite** database locally. 
When the phone has internet, it syncs with the PostgreSQL backend. When offline, it serves data strictly from the local SQLite cache to ensure uninterrupted access in remote fields.
