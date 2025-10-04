# ClearSkies API

Unified air quality intelligence platform integrating NASA TEMPO satellite data, OpenAQ ground sensors, and OpenWeather data.

## Features

- 🛰️ **NASA TEMPO Satellite Data** - Atmospheric measurements from space
- 🌍 **OpenAQ v3 Ground Sensors** - Real-time street-level air quality
- 🌤️ **OpenWeather Integration** - Weather context and conditions
- 📊 **Unified Dashboard Endpoint** - All data in one API call
- 🔐 **Bearer Token Authentication** - Secure API access
- 📱 **React Native Ready** - Optimized for mobile apps

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Development Server

```bash
python app.py
```

Server will start at `http://localhost:5000`

## API Endpoints

### Unified Dashboard Endpoint

**POST** `/api/dashboard`

Returns all necessary data for React Native dashboard in a single request.

**Headers:**
```
Authorization: Bearer <your_api_key>
Content-Type: application/json
```

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

### Other Endpoints

- **POST** `/api/air-quality/current` - Current air quality only
- **POST** `/api/forecast` - 24-hour forecast
- **POST** `/api/alerts` - Health alerts
- **GET** `/api/health` - Health check

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `API_KEY` | Authentication token | Yes |
| `OPENAQ_API_KEY` | OpenAQ v3 API key | Recommended |
| `OPENWEATHER_API_KEY` | OpenWeather API key | Recommended |
| `NASA_EARTHDATA_TOKEN` | NASA Earthdata token | Optional |
| `FLASK_ENV` | Environment (development/production) | No |
| `PORT` | Server port (default: 5000) | No |

## Data Sources

### NASA TEMPO
- Tropospheric pollutant measurements
- NO2, O3, HCHO from satellite
- Coverage: North America

### OpenAQ v3
- Ground-based sensor network
- PM2.5, PM10, O3, NO2, SO2, CO
- Global coverage

### OpenWeather
- Temperature, humidity, wind
- Weather conditions
- Global coverage

## React Native Integration

```typescript
const response = await fetch('http://localhost:5000/api/dashboard', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your_api_key_here'
  },
  body: JSON.stringify({
    latitude: 37.7749,
    longitude: -122.4194
  })
});

const data = await response.json();
console.log(data.data.current.aqi);
```
