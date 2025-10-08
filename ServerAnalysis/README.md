# ServerAnalysis - LogMyself & LogBoard API

A powerful analysis server for LogMyself and LogBoard applications, providing automated data analysis, scheduling, and processing capabilities.

## 🚀 Overview

ServerAnalysis is a FastAPI-based backend service designed to perform comprehensive data analysis on user activity data collected from LogMyself and LogBoard applications. The server processes various types of user events including GPS locations, sleep patterns, screen time, device interactions, and more.

## ✨ Features

- **RESTful API**: FastAPI-powered endpoints for triggering and managing analysis tasks
- **Automated Scheduling**: Daily analysis tasks scheduled via Celery Beat
- **Asynchronous Processing**: Celery workers for efficient background task execution
- **Task Monitoring**: Flower dashboard for real-time monitoring of Celery tasks
- **Data Analysis**: Advanced analysis using scikit-learn, scipy, and pandas
- **Geospatial Analysis**: Location-based analysis with geopy and haversine
- **Multi-Database Support**: PostgreSQL for local data, Firebase and Supabase integration
- **Containerized Deployment**: Full Docker Compose setup for easy deployment
- **Health Monitoring**: Built-in health check endpoints
- **Comprehensive Testing**: Test suite with pytest

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.112.0
- **Task Queue**: Celery 5.4.0 with Redis
- **Database**: PostgreSQL 15, SQLAlchemy 2.0.41
- **Cloud Services**: 
  - Firebase Admin SDK 6.8.0
  - Supabase 2.15.1
- **Data Analysis**:
  - pandas 2.3.1
  - scikit-learn 1.7.1
  - scipy 1.16.0
  - numpy 2.3.1
- **Geospatial**: geopy, haversine, pyproj 3.7.1
- **Server**: Uvicorn 0.24.0
- **Monitoring**: Flower 2.0.1+
- **Testing**: pytest 7.0.0+

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended) or
- **Python 3.12+**
- **PostgreSQL 15+** (if running locally)
- **Redis 7+** (if running locally)

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ServerAnalysis.git
cd ServerAnalysis
```

### 2. Configure Environment Variables

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` and set the required values:

```env
# PostgreSQL Database
POSTGRES_DB=analysis_db
POSTGRES_USER=analysis_user
POSTGRES_PASSWORD=your_secure_password

# Supabase (REQUIRED)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Firebase Credentials
FIREBASE_LOGBOARD_CREDENTIALS_PATH=/app/credentials_logboard.json
FIREBASE_LOGMYSELF_CREDENTIALS_PATH=/app/credentials_logmyself.json

# Timezone
DEFAULT_TIMEZONE=Europe/Athens
```

### 3. Add Firebase Credentials

Place your Firebase credentials JSON files in the project root:
- `credentials_logboard.json`
- `credentials_logmyself.json`

## 🚀 Running the Server

### Option 1: Docker Compose (Recommended)

The easiest way to run the entire stack:

```bash
docker-compose up --build
```

This will start:
- **API Server** on `http://localhost:8000`
- **Flower Dashboard** on `http://localhost:5555`
- **PostgreSQL** database
- **Redis** message broker
- **Celery Worker** for background tasks
- **Celery Beat** for scheduled tasks

### Option 2: Local Development

#### Set up Python environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Start required services:

Make sure PostgreSQL and Redis are running locally, then:

```bash
# Terminal 1: Start the API server
python run.py
# or
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Celery worker
celery -A app.celery_app worker --loglevel=info --concurrency=4

# Terminal 3: Start Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info

# Terminal 4 (Optional): Start Flower monitoring
celery -A app.celery_app flower --port=5555
```

## 📡 API Endpoints

### Health Check
```
GET /
```
Returns server health status.

**Response:**
```json
{
  "message": "I am alive",
  "status": "healthy"
}
```

### Start Daily Analysis
```
POST /api/analysis/daily
```
Triggers a daily analysis for a specific date.

**Request Body:**
```json
{
  "date": "2025-10-08"
}
```

**Response:**
```json
{
  "status": "analysis started",
  "date": "2025-10-08",
  "result": { ... }
}
```

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📊 Monitoring

### Flower Dashboard

Access the Celery task monitoring dashboard at `http://localhost:5555` to:
- Monitor active tasks
- View task history
- Check worker status
- Review task execution times

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_database_service.py
```

## 📁 Project Structure

```
ServerAnalysis/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── core/             # Core application logic
│   │   └── tasks/        # Celery tasks
│   ├── local_database/   # Database models and connection
│   ├── services/         # Business logic services
│   │   ├── analysis_service.py
│   │   ├── database_service.py
│   │   ├── firebase_service.py
│   │   ├── orchestration_service.py
│   │   └── supabase_service.py
│   ├── celery_app.py     # Celery configuration
│   ├── config.py         # Application settings
│   └── main.py           # FastAPI application
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── docker-compose.yml    # Docker orchestration
├── dockerfile            # Docker image definition
├── requirements.txt      # Python dependencies
└── run.py               # Local development server
```

## ⚙️ Configuration

### Analysis Settings

Configure minimum event thresholds in `.env`:

```env
MINIMUM_SESSIONS_LENGTH=0
MINIMUM_SLEEP_EVENTS=0
MINIMUM_SCREEN_TIME_EVENTS=0
MINIMUM_DEVICE_UNLOCK_EVENTS=0
MINIMUM_USER_ACTIVITY_EVENTS=0
MINIMUM_DEVICE_DROP_EVENTS=0
MINIMUM_LOW_LIGHTS_EVENTS=0
MINIMUM_CALL_EVENTS=0
MINIMUM_GPS_EVENTS=0
```

### Scheduled Tasks

The server automatically runs daily analysis at **17:59** (configured in `config.py`). Modify the schedule by editing:

```python
beat_schedule = {
    'daily-analysis-at-17-59': {
        'task': 'app.core.tasks.user_analysis_tasks.run_daily_analysis_task',
        'schedule': crontab(hour=17, minute=59),
    },
}
```

## 🔒 Security Notes

- Never commit `.env` files or Firebase credentials to version control
- Use strong passwords for database access
- In production, configure CORS properly (currently allows all origins)
- Keep dependencies updated for security patches

## 📝 Development

### Adding New Analysis Tasks

1. Create task in `app/core/tasks/`
2. Register task in Celery autodiscovery
3. Add API endpoint in `app/api/routes.py`
4. Update orchestration service if needed

### Database Migrations

The server automatically creates tables on startup. For schema changes, refer to `db_schema.sql`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors:**
- Verify PostgreSQL is running
- Check DATABASE_URL in environment variables
- Ensure database exists and credentials are correct

**Celery Tasks Not Running:**
- Verify Redis is accessible
- Check Celery worker logs
- Ensure CELERY_BROKER_URL is correctly configured

**Firebase Authentication Errors:**
- Verify credentials files exist and are valid
- Check file paths in environment variables
- Ensure proper permissions for service accounts

## 📞 Support

For issues and questions, please open an issue on the GitHub repository.

---

Built with ❤️ using FastAPI, Celery, and modern Python tools.
