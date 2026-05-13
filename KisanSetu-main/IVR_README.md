# KisanSetu IVR System

Interactive Voice Response (IVR) system for farmer phone calls, integrated with disease detection.

## Overview

The IVR system allows farmers to:
- Call via phone and navigate menus in Hindi/English
- Send crop leaf photos via MMS for disease detection
- Get automated disease diagnosis and treatment advice
- Access market prices and weather information via voice

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Phone/User    │────▶│   IVR Engine     │────▶│  API Gateway    │
│   (Twilio/AT)   │     │   (Port 8001)    │     │   (Port 8000)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Disease Model   │     │   PostgreSQL    │
                        │  (TFLite)        │     │   Database      │
                        └──────────────────┘     └─────────────────┘
```

## Quick Start

### 1. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# For Twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# For Africa's Talking (Africa)
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_key
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Or start individually
docker-compose up db api_gateway ivr_engine redis
```

### 3. Configure Webhooks

**Twilio:**
- Set Voice URL to: `http://your-server/webhooks/call`
- Set Messaging URL to: `http://your-server/webhooks/mms`

**Africa's Talking:**
- Set callback URL to: `http://your-server/webhooks/call`

## IVR Flow

```
Call Initiated
     │
     ▼
┌─────────────┐
│  Welcome   │──▶ Press 1 (Hindi) / 2 (English)
└─────────────┘
     │
     ▼
┌─────────────┐
│ Main Menu   │──▶ 1: Disease Detection
└─────────────┘     2: Market Prices
     │              3: Weather
     │              9: Exit
     ▼
┌─────────────┐
│   Disease   │──▶ Send photo via MMS
│   Scan      │──▶ Get diagnosis + advice
└─────────────┘
```

## API Endpoints

### IVR Engine (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/webhooks/call` | POST | Incoming call handler |
| `/webhooks/gather` | POST | DTMF input handler |
| `/webhooks/mms` | POST | MMS image handler |
| `/api/analyze` | POST | Analyze image for disease |
| `/api/calls/{call_sid}` | GET | Get call info |
| `/api/active-calls` | GET | List active calls |

### API Gateway (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ivr/callback` | POST | IVR callback |
| `/api/v1/ivr/incoming-call` | POST | Incoming call |
| `/api/v1/ivr/mms-receive` | POST | Receive MMS |
| `/api/v1/disease/predict` | POST | Disease detection |
| `/api/v1/weather/...` | GET | Weather info |
| `/api/v1/mandi/...` | GET | Market prices |

## Language Support

| Language | Code | Voice |
|----------|------|-------|
| Hindi | hi | hi-IN-Standard-A |
| English | en | en-US-Standard-A |
| Marathi | mr | mr-IN-Standard-A |
| Gujarati | gu | gu-IN-Standard-A |
| Kannada | kn | kn-IN-Standard-A |

## Disease Detection

The system uses the MobileNetV2-based TFLite model to detect 38 plant diseases including:
- Apple (scab, black rot, cedar rust)
- Tomato (late blight, early blight, leaf mold)
- Potato (early blight, late blight)
- Grape (black rot, Esca, leaf blight)
- And more...

### Response Example

```json
{
  "success": true,
  "result": {
    "class_id": 27,
    "disease_name": "Tomato___Late_blight",
    "confidence": 0.92,
    "is_healthy": false
  },
  "message": "आपके पौधे में Late_blight पाया गया। इसकी पुष्टि 92 प्रतिशत है। उपचार: तुरंत कवकनाशी का उपयोग करें।"
}
```

## Testing

```bash
# Test the API
curl http://localhost:8001/health

# Test disease analysis
curl -X POST http://localhost:8000/api/v1/disease/predict \
  -F "file=@test_image.jpg"

# Test IVR call flow
curl -X POST http://localhost:8001/webhooks/call \
  -d "CallSid=test123" \
  -d "From=+1234567890"
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `IVR_PROVIDER` | twilio | Provider (twilio/africastalking) |
| `DEFAULT_LANGUAGE` | hi | Default language |
| `CALL_TIMEOUT` | 300 | Max call duration (seconds) |
| `MAX_RECORDING_DURATION` | 30 | Max recording length |

## Deployment

### Production Checklist
- [ ] Configure SSL/TLS
- [ ] Set up Twilio/Africa's Talking webhooks
- [ ] Configure Redis for session storage
- [ ] Set up database migrations
- [ ] Configure monitoring and logging
- [ ] Set up backup for disease images

## Troubleshooting

```bash
# Check service logs
docker-compose logs ivr_engine

# Check active calls
curl http://localhost:8001/api/active-calls

# Test database connection
docker-compose exec db psql -U kisan_admin -d kisansetu
```