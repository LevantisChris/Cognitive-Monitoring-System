from datetime import timedelta
from firebase_admin import credentials, firestore
import firebase_admin
from app.config import settings
from datetime import datetime
import logging
from google.cloud.firestore_v1 import FieldFilter
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class FirebaseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance.db_logBoard = None
            cls._instance.db_logMyself = None
            cls._instance._initialize_firebase()
        return cls._instance

    def __init__(self):
        pass
    
    def _initialize_firebase(self):
       if settings.USE_FIREBASE_EMULATOR:
           from google.cloud.firestore_v1 import Client
           # Initialize the emulator for LogMyself
           self.db_logMyself = Client(project="YOUR-LOCAL-EMULATOR-PROJECT-ID")
           self.db_logMyself._emulator_host = f"{settings.FIREBASE_EMULATOR_HOST}:{settings.FIREBASE_EMULATOR_PORT}"
           logger.info("LogMyself Firebase emulator initialized")
       else:
           # Check if LogMyself app already exists and initialize if not
           try:
               logMyself_app = firebase_admin.get_app('logmyself')
               logger.info("LogMyself Firebase app already initialized")
           except ValueError:
               cred_logMyself = credentials.Certificate(settings.FIREBASE_LOGMYSELF_CREDENTIALS_PATH)
               logMyself_app = firebase_admin.initialize_app(cred_logMyself, name='logmyself')
               logger.info("LogMyself Firebase app initialized")
           self.db_logMyself = firestore.client(app=logMyself_app)

       # We will use LogBoard in Cloud Firebase always
       # Check if LogBoard app already exists and initialize if not
       try:
           logBoard_app = firebase_admin.get_app('logboard')
           logger.info("LogBoard Firebase app already initialized")
       except ValueError:
           cred_logBoard = credentials.Certificate(settings.FIREBASE_LOGBOARD_CREDENTIALS_PATH)
           logBoard_app = firebase_admin.initialize_app(cred_logBoard, name='logboard')
           logger.info("LogBoard Firebase app initialized")
       self.db_logBoard = firestore.client(app=logBoard_app)

    def fetch_users(self) -> List[Tuple[str, str, str]]:
        """Fetch all users from both LogBoard and LogMyself."""
        users = []
        
        try:
            # Fetch LogBoard users
            logboard_users = self._fetch_logboard_users()
            users.extend(logboard_users)
            
            # Fetch LogMyself users
            logmyself_users = self._fetch_logmyself_users()
            users.extend(logmyself_users)
            
            logger.info(f"Fetched {len(users)} total users")
            return users
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    def _fetch_logboard_users(self) -> List[Tuple[str, str, str]]:
        """Fetch users from LogBoard Firebase."""
        users = []
        try:
            users_ref = self.db_logBoard.collection('users')
            docs = users_ref.stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                users.append((doc.id, "LogBoard", user_data.get('email', '')))
            
            logger.info(f"Fetched {len(users)} LogBoard users")
            return users
        except Exception as e:
            logger.error(f"Error fetching LogBoard users: {e}")
            return []
    
    def _fetch_logmyself_users(self) -> List[Tuple[str, str, str]]:
        """Fetch users from LogMyself Firebase."""
        users = []
        try:
            users_ref = self.db_logMyself.collection('users')
            docs = users_ref.stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                users.append((doc.id, "LogMyself", user_data.get('email', '')))
            
            logger.info(f"Fetched {len(users)} LogMyself users")
            return users
        except Exception as e:
            logger.error(f"Error fetching LogMyself users: {e}")
            return []

    def fetch_typing_sessions(self, user_uid: str, start_dt: datetime, end_dt: datetime):
        sessions = []
        try:
            if self.db_logBoard is None:
                logger.error("Firebase client not initialized. Skipping typing sessions fetch operation.")
                return []

            sessions_ref = self.db_logBoard.collection(f'users/{user_uid}/typing_session_data')
            query = sessions_ref.where(filter=FieldFilter("dateCreated", ">=", start_dt)).where(filter=FieldFilter("dateCreated", "<=", end_dt))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_SESSIONS_LENGTH:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_SESSIONS_LENGTH} typing sessions")
                return []

            for doc in docs:
                session_data = doc.to_dict()
                session_data['session_uid'] = doc.id
                sessions.append(session_data)

            logger.info(f"Fetched {len(sessions)} typing sessions for user {user_uid}")
            return sessions
        except Exception as e:
            logger.error(f"Error fetching typing sessions: {e}")
            return []

    def fetch_gps_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch GPS events for a user from LogMyself."""
        events = []
        try:
            events_ref = self.db_logMyself.collection(f'users/{user_uid}/gps_events')
            query = events_ref.where(filter=FieldFilter("timestampNow", ">=", start_dt)) \
                .where(filter=FieldFilter("timestampNow", "<=", end_dt))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_GPS_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_GPS_EVENTS} GPS events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} GPS events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching GPS events for user {user_uid}: {e}")
            return []

    def fetch_sleep_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch sleep events for a user from LogMyself."""
        events = []
        try:
            # Extend end time to include next day until 17:59
            end_dt_extended = (end_dt + timedelta(days=1)).replace(hour=17, minute=59, second=59, microsecond=999999)

            events_ref = self.db_logMyself.collection(f'users/{user_uid}/sleep_events')
            query = events_ref.where(filter=FieldFilter("timestampNow", ">=", start_dt)) \
                .where(filter=FieldFilter("timestampNow", "<=", end_dt_extended))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_SLEEP_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_SLEEP_EVENTS} sleep events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} sleep events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching sleep events for user {user_uid}: {e}")
            return []

    def fetch_screen_time_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch screen time events for a user from LogMyself."""
        events = []
        try:
            # Extend end time to include next day until 17:59
            end_dt_extended = (end_dt + timedelta(days=1)).replace(hour=17, minute=59, second=59, microsecond=999999)

            events_ref = self.db_logMyself.collection(f'users/{user_uid}/screen_time_events')
            query = events_ref.where(filter=FieldFilter("timeStart", ">=", start_dt)) \
                .where(filter=FieldFilter("timeEnd", "<=", end_dt_extended))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_SCREEN_TIME_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_SCREEN_TIME_EVENTS} screen time events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} screen time events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching screen time events for user {user_uid}: {e}")
            return []

    def fetch_device_unlock_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch device unlock events for a user from LogMyself."""
        events = []
        try:

            end_dt = (end_dt + timedelta(days=1)).replace(hour=17, minute=59, second=59, microsecond=999999)

            events_ref = self.db_logMyself.collection(f'users/{user_uid}/device_unlocks_events')
            query = events_ref.where(filter=FieldFilter("timestamp", ">=", start_dt)) \
                .where(filter=FieldFilter("timestamp", "<=", end_dt))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_DEVICE_UNLOCK_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_DEVICE_UNLOCK_EVENTS} device unlock events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} device unlock events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching device unlock events for user {user_uid}: {e}")
            return []

    def fetch_user_activities_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch user activity events from LogMyself."""
        events = []
        try:

            end_dt = (end_dt + timedelta(days=1)).replace(hour=17, minute=59, second=59, microsecond=999999)

            events_ref = self.db_logMyself.collection(f'users/{user_uid}/user_activities_events')
            query = events_ref.where(filter=FieldFilter("timestamp", ">=", start_dt)) \
                .where(filter=FieldFilter("timestamp", "<=", end_dt))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_USER_ACTIVITY_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_USER_ACTIVITY_EVENTS} user activity events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} user activity events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching user activity events for user {user_uid}: {e}")
            return []

    def fetch_call_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch call events for a user from LogMyself."""
        events = []
        try:

            end_dt = (end_dt + timedelta(days=1)).replace(hour=17, minute=59, second=59, microsecond=999999)

            events_ref = self.db_logMyself.collection(f'users/{user_uid}/call_events')
            query = events_ref.where(filter=FieldFilter("callDate", ">=", start_dt)) \
                .where(filter=FieldFilter("callDate", "<=", end_dt))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_CALL_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_CALL_EVENTS} call events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} call events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching call events for user {user_uid}: {e}")
            return []

    def fetch_device_drop_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch device drop events for a user from LogMyself."""
        events = []
        try:
            events_ref = self.db_logMyself.collection(f'users/{user_uid}/drop_events')
            query = events_ref.where(filter=FieldFilter("timestamp", ">=", start_dt)) \
                .where(filter=FieldFilter("timestamp", "<=", end_dt))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_DEVICE_DROP_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_DEVICE_DROP_EVENTS} device drop events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} device drop events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching device drop events for user {user_uid}: {e}")
            return []

    def fetch_low_light_events(self, user_uid: str, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch low light events for a user from LogMyself."""
        events = []
        try:
            events_ref = self.db_logMyself.collection(f'users/{user_uid}/low_light_events')
            query = events_ref.where(filter=FieldFilter("startTime", ">=", start_dt)) \
                .where(filter=FieldFilter("endTime", "<=", end_dt))
            docs = list(query.stream())

            if len(docs) <= settings.MINIMUM_LOW_LIGHTS_EVENTS:
                logger.info(f"User {user_uid} has less than {settings.MINIMUM_LOW_LIGHTS_EVENTS} low light events")
                return []

            for doc in docs:
                event_data = doc.to_dict()
                event_data['event_id'] = doc.id
                events.append(event_data)

            logger.info(f"Fetched {len(events)} low light events for user {user_uid}")
            return events
        except Exception as e:
            logger.error(f"Error fetching low light events for user {user_uid}: {e}")
            return []