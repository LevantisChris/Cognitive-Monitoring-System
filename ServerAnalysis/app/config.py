import os

from dotenv import load_dotenv
from celery.schedules import crontab

class Settings:
    load_dotenv()

    # DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///analysis_db.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://analysis_user:analysis_pass@localhost:5432/analysis_db")

    # Firebase settings
    FIREBASE_LOGBOARD_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_LOGBOARD_CREDENTIALS_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credentials_logboard.json")
    )
    FIREBASE_LOGMYSELF_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_LOGMYSELF_CREDENTIALS_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credentials_logmyself.json")
    )

    FIREBASE_EMULATOR_HOST = os.getenv("FIREBASE_EMULATOR_HOST", "127.0.0.1")
    FIREBASE_EMULATOR_PORT = int(os.getenv("FIREBASE_EMULATOR_PORT", "8080"))
    # USE_FIREBASE_EMULATOR = bool(os.getenv("USE_FIREBASE_EMULATOR", "false").lower() == "true") # cuncomment this when you define the environment variable USE_FIREBASE_EMULATOR
    USE_FIREBASE_EMULATOR = False

    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and Key must be set in environment variables.")

    # Analysis settings
    MINIMUM_SESSIONS_LENGTH: int = int(os.getenv("MINIMUM_SESSIONS_LENGTH", "0"))
    MINIMUM_SLEEP_EVENTS: int = int(os.getenv("MINIMUM_SLEEP_EVENTS", "0"))
    MINIMUM_SCREEN_TIME_EVENTS: int = int(os.getenv("MINIMUM_SCREEN_TIME_EVENTS", "0"))
    MINIMUM_DEVICE_UNLOCK_EVENTS: int = int(os.getenv("MINIMUM_DEVICE_UNLOCK_EVENTS", "0"))
    MINIMUM_USER_ACTIVITY_EVENTS: int = int(os.getenv("MINIMUM_USER_ACTIVITY_EVENTS", "0"))
    MINIMUM_DEVICE_DROP_EVENTS: int = int(os.getenv("MINIMUM_DEVICE_DROP_EVENTS", "0"))
    MINIMUM_LOW_LIGHTS_EVENTS: int = int(os.getenv("MINIMUM_LOW_LIGHTS_EVENTS", "0"))
    MINIMUM_CALL_EVENTS: int = int(os.getenv("MINIMUM_CALL_EVENTS", "0"))
    MINIMUM_GPS_EVENTS: int = int(os.getenv("MINIMUM_GPS_EVENTS", "0"))
    
    # Timezone settings
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Europe/Athens")

    ## Celery settings ##
    beat_schedule = {
        'daily-analysis-at-17-59': {
            'task': 'app.core.tasks.user_analysis_tasks.run_daily_analysis_task',
            'schedule': crontab(hour=17, minute=59),  # Run daily at 17:59
        },
    }
    broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Task Routing
    task_routes = {
        'app.core.tasks.user_analysis_tasks.analyze_user_data': {'queue': 'default'},
    }

    # Queue Configuration
    task_default_queue = 'default'
    task_create_missing_queues = True

    # Result Configuration
    task_ignore_result = False
    task_store_eager_result = True

    # Retry Configuration
    task_acks_late = True

    # Logging
    worker_hijack_root_logger = False
    worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
    worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

settings = Settings()