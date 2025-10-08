from app.services.firebase_service import FirebaseService
from app.services.supabase_service import SupabaseService
from app.services.analysis_service import AnalysisService
from app.services.database_service import DatabaseService
from app.local_database.connection import drop_tables, create_tables
from datetime import datetime
from app.core import tasks as core_tasks
import logging
import pytz

logger = logging.getLogger(__name__)

class OrchestrationService:
    """Main orchestration service that coordinates all analysis operations."""

    def __init__(self, db_service: DatabaseService):
        self.firebase_service = FirebaseService()
        self.supabase_service = SupabaseService()
        self.db_service = db_service

    def run_daily_analysis(self, date_analysis: str):
        # Before starting the analysis, ensure the local database is cleaned up and recreated
        logger.info("Cleaning up and recreating local database before starting daily analysis...")
        try:
            drop_tables()
            create_tables()
            logger.info("Local database cleaned up and recreated successfully.")
        except Exception as e:
            logger.error(f"Failed to clean up and recreate local database before starting daily analysis: {e}")
            return {"success": False, "error": f"Failed to clean up and recreate local database before starting daily analysis: {e}"}

        # Convert the date string to a datetime object
        try:
            athens_tz = pytz.timezone("Europe/Athens")
            analysis_start_datetime = athens_tz.localize(datetime.strptime(f"{date_analysis} 00:00:00", "%Y-%m-%d %H:%M:%S"))
            analysis_end_datetime = athens_tz.localize(datetime.strptime(f"{date_analysis} 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            print("\033[91mInvalid date format. Please provide a date in YYYY-MM-DD format.\033[0m")
            return {"success": False, "error": "Cannot convert date string to datetime object. Please provide a date in YYYY-MM-DD format."}

        logger.info(f"Running daily analysis for {date_analysis}: with start time {analysis_start_datetime} and end time {analysis_end_datetime}")

        # Fetch and store users
        users = self.firebase_service.fetch_users()
        if not users:
            logger.error("No users found")
            return {"success": False, "error": "No users found in the system."}

        # Store users in local database and send them to Supabase
        for user_uid, app_origin, user_email in users:
            logger.info(f"\n\nStoring user {user_uid} with app origin {app_origin} and email {user_email} in local database and Supabase")

            if self.db_service.check_if_user_exists(user_uid):
                logger.info(f"User {user_uid} already exists in local database, skipping save the user in local database and Supabase.")
            else:
                logger.info(f"Storing user {user_uid} in local database and sending to Supabase")
                if self.db_service.store_user(user_uid, app_origin, user_email):
                    logger.info(f"User {user_uid} stored successfully in local database")
                    if self.supabase_service.send_user(user_uid, user_email, app_origin):
                        logger.info(f"User {user_uid} processed for Supabase successfully")
                    else:
                        logger.error(f"Failed to send user {user_uid} to Supabase")
                else:
                    logger.error(f"Failed to store user {user_uid} in local database")

        logger.info(f"\033[94m\n\nFinished storing users for daily analysis on {date_analysis} at local database and Supabase.\033[0m")

        # Process each user with Celery workers
        results = []
        for user_uid, app_origin, user_email in users:
            try: 
                # Dispatch Celery task for each user (datetime objects need to be serialized to ISO strings)
                job = core_tasks.user_analysis_tasks.analyze_user_data.delay(
                    user_uid, 
                    app_origin, 
                    user_email, 
                    analysis_start_datetime.isoformat(),  # Convert to ISO string for serialization
                    analysis_end_datetime.isoformat()     # Convert to ISO string for serialization
                )
                
                logger.info(f"Dispatched Celery task for user {user_uid} with job ID: {job.id}")
                
                results.append({
                    "user_uid": user_uid,
                    "success": True,
                    "job_id": job.id
                })
            except Exception as e:
                logger.error(f"Error dispatching task for user {user_uid}: {e}")
                results.append({
                    "user_uid": user_uid,
                    "success": False,
                    "error": str(e),
                    "job_id": None
                })

        logger.info(f"\033[94m\n\nFinished running daily analysis for {date_analysis}.\033[0m")
        return {'success': True, 'message': f"Daily analysis for {date_analysis} completed successfully.", 'results': results}

    # NOTE: The code bellow is the old code that was used to process user data without using Celery workers.
    # def _process_user_data(self, user_uid: str, app_origin: str, user_email: str, analysis_start_datetime: datetime, analysis_end_datetime: datetime):
    #     """Process user data for a given user."""

    #     logger.info(f"\033[92m\n\n-----------Processing user {user_uid} (email: {user_email}, origin: {app_origin})-----------\033[0m\n\n")

    #     analysis_service = AnalysisService(self.db_service, self.supabase_service)
    #     if app_origin == "LogBoard":
    #         logger.info(f"--LogBoard analysis for user: {user_uid}--")
    #         # Fetch typing sessions
    #         typing_sessions = self.firebase_service.fetch_typing_sessions(user_uid, analysis_start_datetime, analysis_end_datetime)

    #         if not typing_sessions:
    #             return

    #         # Store each typing session to local database
    #         for session in typing_sessions:
    #             session_uid = session.get('session_uid')
    #             if self.db_service.store_typing_session_and_data(user_uid, session_uid, session):
    #                 # Send session to Supabase
    #                 logger.info("Sending typing session to Supabase...")
    #                 session_date_utc = session.get('dateCreated').astimezone(pytz.timezone("Europe/Athens"))
    #                 payload = {
    #                     'session_uid': session_uid,
    #                     'user_uid': user_uid,
    #                     'session_date': session_date_utc.isoformat(),
    #                     'cognitive_score': None,
    #                     'cognitive_decision': None
    #                 }

    #                 if self.supabase_service.send_data(
    #                     table_name="Typing_Sessions",
    #                     unique_field="session_uid",
    #                     unique_value=session_uid,
    #                     payload=payload
    #                 ):
    #                     logger.info(f"Typing session {session_uid} sent to Supabase successfully")
    #                 else:
    #                     logger.error(f"Failed to send typing session {session_uid} to Supabase")

    #         logger.info(f"\033[92mFinished processing user {user_uid} ({app_origin})\033[0m")

    #         logboard_analysis_result = analysis_service.start_logboard_data_analysis(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         if logboard_analysis_result is not None:
    #             if logboard_analysis_result['status'] == "error":
    #                 logger.error(f"Error in logboard analysis for user {user_uid}: {logboard_analysis_result['error']}")
    #             else:
    #                 logger.info(f"\033[92m\n\nLogboard analysis for user {user_uid} completed successfully\n\n\033[0m")

    #                 # Success with logboard analysis, so continue with updating the stats of the day
    #                 day_analyzed = analysis_start_datetime.date().isoformat()
    #                 self._calc_stats_for_a_day(user_uid, app_origin, day_analyzed, analysis_service)
    #     else:
    #         logger.info(f"Skipping user {user_uid} with app origin {app_origin} as it is not supported for logboard analysis")

    #     if app_origin == "LogMyself":
    #         logger.info(f"--LogMyself analysis for user: {user_uid}--")

    #         # Fetch various events for the user from Firebase of logmyself app
    #         gps_events = self.firebase_service.fetch_gps_events(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         sleep_events = self.firebase_service.fetch_sleep_events(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         screen_time_events = self.firebase_service.fetch_screen_time_events(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         device_unlock_events = self.firebase_service.fetch_device_unlock_events(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         user_activities_events = self.firebase_service.fetch_user_activities_events(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         call_events = self.firebase_service.fetch_call_events(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         device_drop_events = self.firebase_service.fetch_device_drop_events(user_uid, analysis_start_datetime, analysis_end_datetime)
    #         low_light_events = self.firebase_service.fetch_low_light_events(user_uid, analysis_start_datetime, analysis_end_datetime)

    #         #  Now, store them in local database to be used later for analysis
    #         logger.info(f"Storing GPS events for user {user_uid}, total events: {len(gps_events)}")
    #         for event in gps_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_gps_event(user_uid, event_id, event)

    #         logger.info(f"Storing sleep events for user {user_uid}, total events: {len(sleep_events)}")
    #         for event in sleep_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_sleep_event(user_uid, event_id, event)

    #         logger.info(f"Storing screen time events for user {user_uid}, total events: {len(screen_time_events)}")
    #         for event in screen_time_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_screen_time_event(user_uid, event_id, event)

    #         logger.info(f"Storing device unlock events for user {user_uid}, total events: {len(device_unlock_events)}")
    #         for event in device_unlock_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_device_unlock_event(user_uid, event_id, event)

    #         logger.info(f"Storing user activities events for user {user_uid}, total events: {len(user_activities_events)}")
    #         for event in user_activities_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_user_activity_event(user_uid, event_id, event)

    #         logger.info(f"Storing call events for user {user_uid}, total events: {len(call_events)}")
    #         for event in call_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_call_event(user_uid, event_id, event)

    #         logger.info(f"Storing device drop events for user {user_uid}, total events: {len(device_drop_events)}")
    #         for event in device_drop_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_device_drop_event(user_uid, event_id, event)

    #         logger.info(f"Storing low light events for user {user_uid}, total events: {len(low_light_events)}")
    #         for event in low_light_events:
    #             event_id = event.get('event_id')
    #             if event_id:
    #                 self.db_service.store_low_light_event(user_uid, event_id, event)

    #         logger.info(f"\033[92mFinished getting data for user {user_uid} ({app_origin})\033[0m")

    #         logmyself_analysis_final_status = analysis_service.start_logmyself_data_analysis(user_uid, analysis_start_datetime, analysis_end_datetime)

    #         logger.info(f"\033[93m\n\nLogmyself analysis final status results:\n {logmyself_analysis_final_status}\n\n\033[0m")

    #         # Success with logmyself analysis, so continue with updating the stats of the day
    #         day_analyzed = analysis_start_datetime.date().isoformat()
    #         self._calc_stats_for_a_day(user_uid, app_origin, day_analyzed, analysis_service)
    #     else:
    #         logger.info(f"Skipping user {user_uid} with app origin {app_origin} as it is not supported for logmyself analysis")

    # def _calc_stats_for_a_day(self, user_uid: str, app_origin: str, day_to_analyze: str, analysis_service: AnalysisService):

    #     logger.info(f"\033[94m\n\n--------Calculating stats for a day for user {user_uid} ({app_origin})--------\033[0m\n\n")
        
    #     daily_analysis_id = self.supabase_service.create_a_daily_analysis_event(user_uid, day_to_analyze, datetime.now().isoformat())

    #     if daily_analysis_id is None:
    #         logger.error(f"Failed to create a daily analysis event for user {user_uid} on {day_to_analyze}")
    #         return {"success": False, "error": "Failed to create a daily analysis event for user {user_uid} on {day_to_analyze}"}

    #     if app_origin == "LogBoard":
    #         status = analysis_service.calc_and_store_typing_stats(user_uid, daily_analysis_id, day_to_analyze)
    #         if not status:
    #             logger.error(f"Failed to calculate and store typing stats for user {user_uid} on {day_to_analyze}")
    #             return {"success": False, "error": "Failed to calculate and store typing stats for user {user_uid} on {day_to_analyze}"}
    #         else:
    #             logger.info(f"Successfully calculated and stored typing stats for user {user_uid} on {day_to_analyze}")
    #             return {"success": True, "message": "Successfully calculated and stored typing stats for user {user_uid} on {day_to_analyze}"}
    #     elif app_origin == "LogMyself": # Note: LogMyself in this version does not have stats for a day, only analysis results per data category
    #         logger.info("This version does not support stats calculation for LogMyself app, skipping stats calculation.")
    #         return {"success": True, "message": "LogMyself in this version does not have stats for a day, only analysis results per data category"}

    #     return None
