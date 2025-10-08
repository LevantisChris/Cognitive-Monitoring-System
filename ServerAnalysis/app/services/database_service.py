from typing import Dict, Any, Sequence

import pytz
from sqlalchemy import text, Row
from sqlalchemy.orm import Session
from app.local_database.models import *
import logging
import pandas as pd

from app.services.helper_service import HelperService

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for handling database operations."""
    
    def __init__(self, db: Session):
        self.db = db

    def store_user(self, user_uid: str, user_email: str, app_origin: str) -> bool:
        """Store user in database."""
        try:
            user = User(
                uid=user_uid,
                email=user_email,
                app_origin=app_origin
            )
            self.db.add(user)
            self.db.commit()
            logger.info(f"User {user_uid} with origin {app_origin} and email {user_email} stored successfully.")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing user {user_uid}: {e}")
            return False

    def check_if_user_exists(self, user_uid: str) -> bool:
        """Check if user exists in local database."""
        try:
            user = self.db.query(User).filter(User.uid == user_uid).first()
            return user is not None
        except Exception as e:
            logger.error(f"Error checking if user {user_uid} exists: {e}")
            return False

    def check_if_typing_session_exists(self, session_uid: str) -> bool:
        """Check if typing session exists."""
        try:
            session = self.db.query(TypingSession).filter(
                TypingSession.typing_session_id == session_uid
            ).first()
            return session is not None
        except Exception as e:
            logger.error(f"Error checking if typing session {session_uid}: {e}")
            return False

    def check_if_user_has_typing_sessions(self, user_uid: str) -> bool:
        """Check if a user has any (at least one) typing session."""
        try:
            sessions = self.db.query(TypingSession).filter(
                TypingSession.user_id == user_uid
            ).all()
            return len(sessions) > 0
        except Exception as e:
            logger.error(f"Error checking if user {user_uid} has typing sessions: {e}")
            return False

    def store_typing_session_and_data(self, user_uid: str, session_uid: str, session_data: dict):
        try:
            if self.check_if_typing_session_exists(session_uid):
                logger.info(f"Typing session {session_uid} already exists for user {user_uid}")
                return True

            # Session not exists, create a new one
            typing_session = TypingSession(
                user_id=user_uid,
                typing_session_id=session_uid
            )
            self.db.add(typing_session)
            self.db.commit()
            logger.info(f"Typing session (basic info) {session_uid} stored successfully for user {user_uid}")

            # Parse dataTime
            raw_date_created = session_data.get("dateCreated")
            # Convert it back to the real date
            # The dateCreate in Date format (from Java) so firebase applied UTC format.
            # This is not something very handy to work with, so we need to convert it to the local time.
            athens = pytz.timezone("Europe/Athens")  # We suppose the user is in Athens
            date_created = raw_date_created.astimezone(athens)

            # Parse startTime and endTime
            start_time_obj = HelperService.parse_time_field(session_data, 'startTime', session_uid)
            end_time_obj = HelperService.parse_time_field(session_data, 'endTime', session_uid)

            typing_session_data = TypingSessionData(
                typing_session_id=session_uid,
                avg_pause_ctc_duration=session_data.get('avgPauseCtCDuration'),
                avg_pause_wtw_duration=session_data.get('avgPauseWtWDuration'),
                characters_typed=session_data.get('charactersTyped'),
                date_created=date_created,
                duration=session_data.get('duration'),
                end_time=end_time_obj,
                iki_list_size=session_data.get('ikiListSize'),
                max_backspace_burst_count=session_data.get('maxBackspaceBurstCount'),
                max_pause_ctc_duration=session_data.get('maxPauseCtCDuration'),
                max_pause_wtw_duration=session_data.get('maxPauseWtWDuration'),
                mean_iki=session_data.get('meanIKI'),
                pause_ctc_list_size=session_data.get('pauseCtCListSize'),
                pause_wtw_list_size=session_data.get('pauseWtWListSize'),
                start_time=start_time_obj,
                std_dev_iki=session_data.get('stdDevIKI'),
                total_backspace_burst_count=session_data.get('totalBackspaceBurstCount'),
                total_backspaces=session_data.get('totalBackspaces'),
                total_cps=session_data.get('totalCPS'),
                total_characters_deleted=session_data.get('totalCharactersDeleted'),
                total_pressure_by_times_counter=session_data.get('totalPressureByTimesCounter'),
                total_wps=session_data.get('totalWPS'),
                total_word_or_sentence_deletions=session_data.get('totalWordOrSentenceDeletions'),
                words_typed=session_data.get('wordsTyped')
            )
            self.db.add(typing_session_data)
            self.db.commit()
            logger.info(f"Typing session (analytic info) for {session_uid} stored successfully")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing typing session {session_uid} for user {user_uid}: {e}")
            return False

    def store_gps_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store GPS event in database."""
        try:
            # First, check if the event already exists
            existing_event = self.db.query(GPSEvent).filter(
                GPSEvent.gps_event_id == event_id
            ).first()

            if existing_event:
                logger.info(f"GPS event {event_id} already exists for user {user_uid}")
                return True

            event = GPSEvent(
                gps_event_id=event_id,
                user_uid=user_uid,
                latitude=event_data.get('latitude'),
                longitude=event_data.get('longitude'),
                accuracy=event_data.get('accuracy'),
                bearing=event_data.get('bearing'),
                speed=event_data.get('speed'),
                speed_accuracy_meters_per_second=event_data.get('speedAccuracyMetersPerSecond'),
                timestamp_now=event_data.get('timestampNow').astimezone(pytz.timezone("Europe/Athens"))
            )
            self.db.add(event)
            self.db.commit()
            # logger.info(f"GPS event {event_id} stored successfully")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing GPS event {event_id}: {e}")
            return False

    def store_sleep_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store sleep event in database."""
        try:
            # First, check if the event already exists
            existing_event = self.db.query(SleepData).filter(
                SleepData.sleep_event_id == event_id
            ).first()
            if existing_event:
                logger.info(f"Sleep event {event_id} already exists for user {user_uid}")
                return True

            # Validate required fields
            required_fields = ['confidence', 'light', 'motion', 'screenOnDuration', 'timestampPrevious', 'timestampNow']
            for field in required_fields:
                if event_data.get(field) is None:
                    logger.error(f"Missing required field '{field}' for sleep event {event_id}")
                    return False

            event = SleepData(
                sleep_event_id=event_id,
                user_id=user_uid,
                confidence=event_data.get('confidence'),
                light=event_data.get('light'),
                motion=event_data.get('motion'),
                screenOnDuration=event_data.get('screenOnDuration'),
                timestamp_previous=event_data.get('timestampPrevious').astimezone(pytz.timezone("Europe/Athens")),
                timestamp_now=event_data.get('timestampNow').astimezone(pytz.timezone("Europe/Athens"))
            )
            self.db.add(event)
            
            # Flush to get the sleep event committed before adding apps
            self.db.flush()

            # Store the used apps during the sleep event
            used_apps_list = event_data.get('usedApps')
            if used_apps_list:
                for app_name, time_used in used_apps_list.items():
                    app_entry = AppsSleepData(
                        sleep_id=event_id,
                        app_name=app_name,
                        time_used=time_used
                    )
                    self.db.add(app_entry)

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing sleep event {event_id}: {e}")
            return False

    def store_screen_time_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store screen time event in database."""
        try:
            # First, check if the event already exists
            existing_event = self.db.query(ScreenTimeEvent).filter(
                ScreenTimeEvent.screen_time_event_id == event_id
            ).first()

            if existing_event:
                logger.info(f"Screen time event {event_id} already exists for user {user_uid}")
                return True

            end_time = event_data.get('timeEnd').astimezone(pytz.timezone("Europe/Athens"))
            start_time = event_data.get('timeStart').astimezone(pytz.timezone("Europe/Athens"))

            event = ScreenTimeEvent(
                screen_time_event_id=event_id,
                user_uid=user_uid,
                start_time=start_time,
                end_time=end_time,
                duration_ms=event_data.get('duration')
            )
            self.db.add(event)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing screen time event {event_id}: {e}")
            return False

    def store_device_unlock_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store device unlock event in database."""
        try:
            # First, check if the event already exists
            existing_event = self.db.query(DeviceUnlockEvent).filter(
                DeviceUnlockEvent.device_unlock_event_id == event_id
            ).first()

            if existing_event:
                logger.info(f"Device unlock event {event_id} already exists for user {user_uid}")
                return True

            event = DeviceUnlockEvent(
                device_unlock_event_id=event_id,
                user_uid=user_uid,
                timestamp=event_data.get('timestamp').astimezone(pytz.timezone("Europe/Athens")),
            )
            self.db.add(event)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing device unlock event {event_id}: {e}")
            return False

    def store_user_activity_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store user activity event in database."""
        try:
            # First, check if the event already exists
            existing_event = self.db.query(UserActivityEvent).filter(
                UserActivityEvent.user_activity_event_id == event_id
            ).first()

            if existing_event:
                logger.info(f"User activity event {event_id} already exists for user {user_uid}")
                return True

            timestamp = event_data.get('timestamp').astimezone(pytz.timezone("Europe/Athens"))

            event = UserActivityEvent(
                user_activity_event_id=event_id,
                user_uid=user_uid,
                timestamp=timestamp,
                activity_type=event_data.get('activityType'),
                confidence=event_data.get('confidence')
            )
            self.db.add(event)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing user activity event {event_id}: {e}")
            return False

    def store_call_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store call event in database."""
        # First, check if the event already exists
        existing_event = self.db.query(CallEvent).filter(
            CallEvent.call_event_id == event_id
        ).first()

        if existing_event:
            logger.info(f"Call event {event_id} already exists for user {user_uid}")
            return True

        try:
            event = CallEvent(
                call_event_id=event_id,
                user_uid=user_uid,
                call_date=event_data.get('callDate').astimezone(pytz.timezone("Europe/Athens")),
                call_type=event_data.get('callType'),
                call_description=event_data.get('callDescription'),
                call_duration_sec=event_data.get('callDuration')
            )
            self.db.add(event)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing call event {event_id}: {e}")
            return False

    def store_device_drop_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store device drop event in database."""
        # First, check if the event already exists
        existing_event = self.db.query(DeviceDropEvent).filter(
            DeviceDropEvent.device_drop_event_id == event_id
        ).first()

        if existing_event:
            logger.info(f"Device drop event {event_id} already exists for user {user_uid}")
            return True

        try:
            event = DeviceDropEvent(
                device_drop_event_id=event_id,
                user_uid=user_uid,
                detected_fall_duration=event_data.get('detectedFallDuration'),
                detected_magnitude=event_data.get('detectedMagnitude'),
                timestamp=event_data.get('timestamp').astimezone(pytz.timezone("Europe/Athens"))
            )
            self.db.add(event)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing device drop event {event_id}: {e}")
            return False

    def store_low_light_event(self, user_uid: str, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Store low light event in database."""
        try:
            # First, check if the event already exists
            existing_event = self.db.query(LowLightEvent).filter(
                LowLightEvent.low_light_event_id == event_id
            ).first()

            if existing_event:
                logger.info(f"Low light event {event_id} already exists for user {user_uid}")
                return True

            event = LowLightEvent(
                low_light_event_id=event_id,
                user_uid=user_uid,
                start_time=event_data.get('startTime').astimezone(pytz.timezone("Europe/Athens")),
                end_time= event_data.get('endTime').astimezone(pytz.timezone("Europe/Athens")),
                duration_ms=event_data.get('duration'),
                low_light_threshold_used=event_data.get('lowLightThreshold'),
            )
            self.db.add(event)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing low light event {event_id}: {e}")
            return False

    def get_typing_sessions_of_a_user(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> Sequence[Row[tuple[Any, ...] | Any]] | list[Any]:
        """Get typing sessions of a user after a specific date."""
        try:
            query = text("""
                SELECT * FROM typing_session_data AS tsd
                JOIN typing_sessions AS ts ON tsd.typing_session_id = ts.typing_session_id
                JOIN users AS usr ON ts.user_id = usr.uid
                WHERE usr.uid = :user_id
                AND tsd.date_created >= :start_datetime
                AND tsd.date_created <= :end_datetime
            """)
            sessions = self.db.execute(query, {"user_id": user_uid, "start_datetime": start_datetime, "end_datetime": end_datetime}).fetchall()
            return sessions
        except Exception as e:
            logger.error(f"Error getting typing sessions for user {user_uid}: {e}")
            return []

    def get_sleep_data_of_a_user(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame | None:
        """Get sleep data for a user within a specified time range.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            DataFrame containing sleep data or None if error occurs
        """
        logger.info(f"Getting sleep data for user {user_uid} from {start_datetime} to {end_datetime}")
        try:
            sleep_events = self.db.query(SleepData).filter(
                SleepData.user_id == user_uid,
                SleepData.timestamp_now >= start_datetime,
                SleepData.timestamp_now <= end_datetime
            ).all()
            
            if not sleep_events:
                return None

            logger.info(f"Number of sleep events: {len(sleep_events)}")
            
            sleep_events_df = pd.DataFrame([
                {
                    'id': event.id,
                    'sleep_event_id': event.sleep_event_id,
                    'user_id': event.user_id,
                    'confidence': event.confidence,
                    'light': event.light,
                    'motion': event.motion,
                    'screenOnDuration': event.screenOnDuration,
                    'timestamp_previous': event.timestamp_previous,
                    'timestamp_now': event.timestamp_now,
                }
                for event in sleep_events
            ])
            return sleep_events_df
        except Exception as e:
            logger.error(f"Error getting sleep data for user {user_uid}: {e}")
            return None
        
    def get_screen_time_events_of_a_user(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame | None:
        """Get screen time events for a user within a specified time range.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            DataFrame containing screen time events or None if error occurs
        """
        try:
            screen_time_events = self.db.query(ScreenTimeEvent).filter(
                ScreenTimeEvent.user_uid == user_uid,
                ScreenTimeEvent.start_time >= start_datetime,
                ScreenTimeEvent.end_time <= end_datetime
            ).all()
            if not screen_time_events:
                return None
            
            screen_time_events_df = pd.DataFrame([
                {
                    'id': event.id,
                    'screen_time_event_id': event.screen_time_event_id,
                    'user_id': event.user_uid,
                    'start_time': event.start_time,
                    'end_time': event.end_time,
                    'duration_ms': event.duration_ms
                }
                for event in screen_time_events
            ])
            return screen_time_events_df
        except Exception as e:
            logger.error(f"Error getting screen time events for user {user_uid}: {e}")
            return None
    
    def get_low_light_data(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> list[LowLightEvent] | None:
        """
        Get low light data for a user within a specified time range
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            List of LowLightEvent objects containing low light data or None if error occurs
        """
        try:
            low_light_events = self.db.query(LowLightEvent).filter(
                LowLightEvent.user_uid == user_uid,
                LowLightEvent.start_time >= start_datetime,
                LowLightEvent.end_time <= end_datetime
            ).all()
            return low_light_events
        except Exception as e:
            logger.error(f"Error getting low light data for user {user_uid}: {e}")
            return None

    def get_device_drop_events(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> list[DeviceDropEvent] | None:
        """Get device drop events for a user within a specified time range.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            List of DeviceDropEvent objects containing device drop events or None if error occurs
        """
        try:
            device_drop_events = self.db.query(DeviceDropEvent).filter(
                DeviceDropEvent.user_uid == user_uid,
                DeviceDropEvent.timestamp >= start_datetime,
                DeviceDropEvent.timestamp <= end_datetime
            ).all()
            return device_drop_events
        except Exception as e:
            logger.error(f"Error getting device drop events for user {user_uid}: {e}")
            return None

    def get_app_usage(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> list[AppsSleepData] | None:
        """Get app usage for a user within a specified time range.
           Note that the sleep events must be fetched for the day analyzed, and
           then associate them with the apps data from the app_usage table.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            List of AppsSleepData objects containing app usage or None if error occurs
        """

        try:
            select_query = text("""
                select at.* from apps_table as at
                JOIN sleep_data as sd on sd.sleep_event_id = at.sleep_id
                where sd.timestamp_previous >= :start_datetime
                    and sd.timestamp_now <= :end_datetime
                    and sd.user_id = :user_id
            """)
            app_usage = self.db.execute(select_query, {"user_id": user_uid, "start_datetime": start_datetime, "end_datetime": end_datetime}).fetchall()
            return app_usage
        except Exception as e:
            logger.error(f"Error getting app usage for user {user_uid}: {e}")
            return None

    def get_activity_data(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> list[UserActivityEvent] | None:
        """Get activity data for a user within a specified time range.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            List of UserActivityEvent objects containing activity data or None if error occurs
        """
        try:
            activity_data = self.db.query(UserActivityEvent).filter(
                UserActivityEvent.user_uid == user_uid,
                UserActivityEvent.timestamp >= start_datetime,
                UserActivityEvent.timestamp <= end_datetime
            ).all()

            return activity_data
        except Exception as e:
            logger.error(f"Error getting activity data for user {user_uid}: {e}")
            return None
    
    def get_call_data(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> list[CallEvent] | None:
        """Get call data for a user within a specified time range.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            DataFrame containing call data or None if error occurs
        """
        try:
            call_data = self.db.query(CallEvent).filter(
                CallEvent.user_uid == user_uid,
                CallEvent.call_date >= start_datetime,
                CallEvent.call_date <= end_datetime
            ).all()
            return call_data
        except Exception as e:
            logger.error(f"Error getting call data for user {user_uid}: {e}")
            return None

    def get_gps_data(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> list[GPSEvent] | None:
        """Get GPS data for a user within a specified time range.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            List of GPSEvent objects containing GPS data or None if error occurs
        """
        try:
            gps_data = self.db.query(GPSEvent).filter(
                GPSEvent.user_uid == user_uid,
                GPSEvent.timestamp_now >= start_datetime,  # Changed from timestamp to timestamp_now
                GPSEvent.timestamp_now <= end_datetime     # Changed from timestamp to timestamp_now
            ).all()
            return gps_data
        except Exception as e:
            logger.error(f"Error getting GPS data for user {user_uid}: {e}")
            return None
    
    def get_device_unlock_events_of_a_user(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> list[DeviceUnlockEvent] | None:
        """Get device unlock events for a user within a specified time range.
        Args:
            user_uid: The user's unique identifier
            start_datetime: Start of the time range (inclusive)
            end_datetime: End of the time range (inclusive)
        Returns:
            List of DeviceUnlockEvent objects containing device unlock events or None if error occurs
        """
        try:
            device_unlock_events = self.db.query(DeviceUnlockEvent).filter(
                DeviceUnlockEvent.user_uid == user_uid,
                DeviceUnlockEvent.timestamp >= start_datetime,
                DeviceUnlockEvent.timestamp <= end_datetime
            ).all()
            return device_unlock_events
        except Exception as e:
            logger.error(f"Error getting device unlock events for user {user_uid}: {e}")
            return None