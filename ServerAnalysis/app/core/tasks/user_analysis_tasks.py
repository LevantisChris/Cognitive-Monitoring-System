import logging
from datetime import datetime, timedelta
import pytz

from app.celery_app import celery_app
from app.config import settings
from app.services.firebase_service import FirebaseService
from app.services.supabase_service import SupabaseService
from app.services.analysis_service import AnalysisService
from app.services.database_service import DatabaseService
from app.local_database.connection import SessionLocal

# Celery tasks related for user analysis data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task
def analyze_user_data(user_uid: str, app_origin: str, user_email: str, analysis_start_datetime_iso: str, analysis_end_datetime_iso: str):
    """
    Celery task to analyze user data for a specific user.
    
    Args:
        user_uid: User unique identifier
        app_origin: Origin of the app (LogBoard or LogMyself)
        user_email: User email
        analysis_start_datetime_iso: Start datetime in ISO format string
        analysis_end_datetime_iso: End datetime in ISO format string
    
    Returns:
        str: Success message
    """
    logger.info(f"\033[92m\n\n-----------Processing user {user_uid} (email: {user_email}, origin: {app_origin})-----------\033[0m\n\n")

    # Convert ISO datetime strings back to datetime objects
    analysis_start_datetime = datetime.fromisoformat(analysis_start_datetime_iso)
    analysis_end_datetime = datetime.fromisoformat(analysis_end_datetime_iso)

    # Create a database session for this task
    db = SessionLocal()
    try:
        # Initialize services for this task
        db_service = DatabaseService(db)
        firebase_service = FirebaseService()
        supabase_service = SupabaseService()
        analysis_service = AnalysisService(db_service, supabase_service)
        
        if app_origin == "LogBoard":
            logger.info(f"--LogBoard analysis for user: {user_uid}--")
            # Fetch typing sessions
            typing_sessions = firebase_service.fetch_typing_sessions(user_uid, analysis_start_datetime, analysis_end_datetime)

            if not typing_sessions:
                return

            # Store each typing session to local database
            for session in typing_sessions:
                session_uid = session.get('session_uid')
                if db_service.store_typing_session_and_data(user_uid, session_uid, session):
                    # Send session to Supabase
                    logger.info("Sending typing session to Supabase...")
                    session_date_utc = session.get('dateCreated').astimezone(pytz.timezone("Europe/Athens"))
                    payload = {
                        'session_uid': session_uid,
                        'user_uid': user_uid,
                        'session_date': session_date_utc.isoformat(),
                        'cognitive_score': None,
                        'cognitive_decision': None
                    }

                    if supabase_service.send_data(
                        table_name="Typing_Sessions",
                        unique_field="session_uid",
                        unique_value=session_uid,
                        payload=payload
                    ):
                        logger.info(f"Typing session {session_uid} sent to Supabase successfully")
                    else:
                        logger.error(f"Failed to send typing session {session_uid} to Supabase")

            logger.info(f"\033[92mFinished processing user {user_uid} ({app_origin})\033[0m")

            logboard_analysis_result = analysis_service.start_logboard_data_analysis(user_uid, analysis_start_datetime, analysis_end_datetime)
            if logboard_analysis_result is not None:
                if logboard_analysis_result['status'] == "error":
                    logger.error(f"Error in logboard analysis for user {user_uid}: {logboard_analysis_result['error']}")
                else:
                    logger.info(f"\033[92m\n\nLogboard analysis for user {user_uid} completed successfully\n\n\033[0m")

                    # Success with logboard analysis, so continue with updating the stats of the day
                    day_analyzed = analysis_start_datetime.date().isoformat()
                    _calc_stats_for_a_day(user_uid, app_origin, day_analyzed, analysis_service, supabase_service)
        else:
            logger.info(f"Skipping user {user_uid} with app origin {app_origin} as it is not supported for logboard analysis")

        if app_origin == "LogMyself":
            logger.info(f"--LogMyself analysis for user: {user_uid}--")

            # Fetch various events for the user from Firebase of logmyself app
            gps_events = firebase_service.fetch_gps_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            sleep_events = firebase_service.fetch_sleep_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            screen_time_events = firebase_service.fetch_screen_time_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            device_unlock_events = firebase_service.fetch_device_unlock_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            user_activities_events = firebase_service.fetch_user_activities_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            call_events = firebase_service.fetch_call_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            device_drop_events = firebase_service.fetch_device_drop_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            low_light_events = firebase_service.fetch_low_light_events(user_uid, analysis_start_datetime, analysis_end_datetime)

            #  Now, store them in local database to be used later for analysis
            logger.info(f"Storing GPS events for user {user_uid}, total events: {len(gps_events)}")
            for event in gps_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_gps_event(user_uid, event_id, event)

            logger.info(f"Storing sleep events for user {user_uid}, total events: {len(sleep_events)}")
            for event in sleep_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_sleep_event(user_uid, event_id, event)

            logger.info(f"Storing screen time events for user {user_uid}, total events: {len(screen_time_events)}")
            for event in screen_time_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_screen_time_event(user_uid, event_id, event)

            logger.info(f"Storing device unlock events for user {user_uid}, total events: {len(device_unlock_events)}")
            for event in device_unlock_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_device_unlock_event(user_uid, event_id, event)

            logger.info(f"Storing user activities events for user {user_uid}, total events: {len(user_activities_events)}")
            for event in user_activities_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_user_activity_event(user_uid, event_id, event)

            logger.info(f"Storing call events for user {user_uid}, total events: {len(call_events)}")
            for event in call_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_call_event(user_uid, event_id, event)

            logger.info(f"Storing device drop events for user {user_uid}, total events: {len(device_drop_events)}")
            for event in device_drop_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_device_drop_event(user_uid, event_id, event)

            logger.info(f"Storing low light events for user {user_uid}, total events: {len(low_light_events)}")
            for event in low_light_events:
                event_id = event.get('event_id')
                if event_id:
                    db_service.store_low_light_event(user_uid, event_id, event)

            logger.info(f"\033[92mFinished getting data for user {user_uid} ({app_origin})\033[0m")

            logmyself_analysis_final_status = analysis_service.start_logmyself_data_analysis(user_uid, analysis_start_datetime, analysis_end_datetime)

            logger.info(f"\033[93m\n\nLogmyself analysis final status results:\n {logmyself_analysis_final_status}\n\n\033[0m")

            # Success with logmyself analysis, so continue with updating the stats of the day
            day_analyzed = analysis_start_datetime.date().isoformat()
            _calc_stats_for_a_day(user_uid, app_origin, day_analyzed, analysis_service, supabase_service)
        else:
            logger.info(f"Skipping user {user_uid} with app origin {app_origin} as it is not supported for logmyself analysis")

        return "User data analyzed successfully"
    finally:
        # Always close the database session
        db.close()

def _calc_stats_for_a_day(user_uid: str, app_origin: str, day_to_analyze: str, 
                          analysis_service: AnalysisService, supabase_service: SupabaseService):
    """
    Calculate and store stats for a day for a specific user.
    
    Args:
        user_uid: User unique identifier
        app_origin: Origin of the app (LogBoard or LogMyself)
        day_to_analyze: Day to analyze in ISO format
        analysis_service: AnalysisService instance
        supabase_service: SupabaseService instance
    """
    logger.info(f"\033[94m\n\n--------Calculating stats for a day for user {user_uid} ({app_origin})--------\033[0m\n\n")
    
    daily_analysis_id = supabase_service.create_a_daily_analysis_event(user_uid, day_to_analyze, datetime.now().isoformat())

    if daily_analysis_id is None:
        logger.error(f"Failed to create a daily analysis event for user {user_uid} on {day_to_analyze}")
        return {"success": False, "error": f"Failed to create a daily analysis event for user {user_uid} on {day_to_analyze}"}

    if app_origin == "LogBoard":
        status = analysis_service.calc_and_store_typing_stats(user_uid, daily_analysis_id, day_to_analyze)
        if not status:
            logger.error(f"Failed to calculate and store typing stats for user {user_uid} on {day_to_analyze}")
            return {"success": False, "error": f"Failed to calculate and store typing stats for user {user_uid} on {day_to_analyze}"}
        else:
            logger.info(f"Successfully calculated and stored typing stats for user {user_uid} on {day_to_analyze}")
            return {"success": True, "message": f"Successfully calculated and stored typing stats for user {user_uid} on {day_to_analyze}"}
    elif app_origin == "LogMyself":
        logger.info("This version does not support stats calculation for LogMyself app, skipping stats calculation.")
        return {"success": True, "message": "LogMyself in this version does not have stats for a day, only analysis results per data category"}

    return None


@celery_app.task
def run_daily_analysis_task():
    """
    Scheduled Celery task to run daily analysis at 23:59.
    Analyzes data for the current day in Europe/Athens timezone.
    
    Returns:
        dict: Result of the daily analysis
    """
    # Import here to avoid circular import
    from app.services.orchestration_service import OrchestrationService
    
    # Get current date in Europe/Athens timezone
    athens_tz = pytz.timezone("Europe/Athens")
    current_date = datetime.now(athens_tz).date()
    date_str = current_date.isoformat()  # Format: YYYY-MM-DD
    
    logger.info(f"\033[96m\n\n{'='*80}\n")
    logger.info(f"SCHEDULED DAILY ANALYSIS STARTED FOR DATE: {date_str}")
    logger.info(f"{'='*80}\n\033[0m")
    
    # Create a database session for this task
    db = SessionLocal()
    try:
        # Initialize services
        db_service = DatabaseService(db)
        orchestration_service = OrchestrationService(db_service)

        # The analysis will run for the previous day
        date_str = (datetime.now(athens_tz).date() - timedelta(days=1)).isoformat()
        
        logger.info(f"Running daily analysis for (previous day): {date_str}")
        
        # Run the daily analysis
        result = orchestration_service.run_daily_analysis(date_str)
        
        logger.info(f"\033[96m\n\n{'='*80}\n")
        logger.info(f"SCHEDULED DAILY ANALYSIS COMPLETED FOR DATE: {date_str}")
        logger.info(f"Result: {result}")
        logger.info(f"{'='*80}\n\033[0m")
        
        return result
    except Exception as e:
        error_msg = f"Error in scheduled daily analysis for {date_str}: {str(e)}"
        logger.error(f"\033[91m{error_msg}\033[0m")
        return {"success": False, "error": error_msg}
    finally:
        # Always close the database session
        db.close()
