from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Time
from app.local_database.connection import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    app_origin = Column(String, nullable=False)  # LogBoard or LogMyself

class TypingSession(Base):
    __tablename__ = "typing_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.uid'), nullable=False)
    typing_session_id = Column(String, nullable=False, unique=True)

class TypingSessionData(Base):
    __tablename__ = "typing_session_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    typing_session_id = Column(String, nullable=False, unique=True)
    avg_pause_ctc_duration = Column(Float, nullable=False)
    avg_pause_wtw_duration = Column(Float, nullable=False)
    characters_typed = Column(Integer, nullable=False)
    date_created = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)
    end_time = Column(Time, nullable=False)
    iki_list_size = Column(Integer, nullable=False)
    max_backspace_burst_count = Column(Integer, nullable=False)
    max_pause_ctc_duration = Column(Float, nullable=False)
    max_pause_wtw_duration = Column(Float, nullable=False)
    mean_iki = Column(Float, nullable=False)
    pause_ctc_list_size = Column(Integer, nullable=False)
    pause_wtw_list_size = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    std_dev_iki = Column(Float, nullable=False)
    total_backspace_burst_count = Column(Integer, nullable=False)
    total_backspaces = Column(Integer, nullable=False)
    total_cps = Column(Float, nullable=False)
    total_characters_deleted = Column(Integer, nullable=False)
    total_pressure_by_times_counter = Column(Integer, nullable=False)
    total_wps = Column(Float, nullable=False)
    total_word_or_sentence_deletions = Column(Integer, nullable=False)
    words_typed = Column(Integer, nullable=False)

class SleepData(Base):
    __tablename__ = "sleep_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sleep_event_id = Column(String, nullable=False, unique=True)
    user_id = Column(String, ForeignKey('users.uid'), nullable=False)
    confidence = Column(Float, nullable=False)
    light = Column(Float, nullable=False)
    motion = Column(Float, nullable=False)
    screenOnDuration = Column(Float, nullable=False)
    timestamp_previous = Column(DateTime, nullable=False)
    timestamp_now = Column(DateTime, nullable=False)

class AppsSleepData(Base):
    __tablename__ = "apps_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sleep_id = Column(String, ForeignKey('sleep_data.sleep_event_id'), nullable=False)
    app_name = Column(String, nullable=False)
    time_used = Column(Float, nullable=True)

class ScreenTimeEvent(Base):
    __tablename__ = "screen_time_events"
    
    id = Column(Integer, primary_key=True, index=True)
    screen_time_event_id = Column(String, nullable = False, unique=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_ms = Column(Integer, nullable=False)

class DeviceUnlockEvent(Base):
    __tablename__ = "device_unlock_events"
    
    id = Column(Integer, primary_key=True, index=True)
    device_unlock_event_id = Column(String,nullable = False, unique=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    timestamp = Column(DateTime, nullable=False)

class UserActivityEvent(Base):
    __tablename__ = "user_activities_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_activity_event_id = Column(String, nullable = False, unique=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=True)
    timestamp = Column(DateTime, nullable=True)
    activity_type = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

class CallEvent(Base):
    __tablename__ = "call_events"
    
    id = Column(Integer, primary_key=True, index=True)
    call_event_id = Column(String, nullable = False, unique=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=True)
    call_date = Column(DateTime, nullable=False)
    call_type = Column(String, nullable=True)  # incoming, outgoing, missed
    call_description = Column(String, nullable=False)
    call_duration_sec = Column(Integer, nullable=True)

class DeviceDropEvent(Base):
    __tablename__ = "device_drop_events"
    
    id = Column(Integer, primary_key=True, index=True)
    device_drop_event_id = Column(String, nullable = False, unique=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable = False)
    detected_fall_duration = Column(Integer, nullable=False)  # in milliseconds
    detected_magnitude = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class LowLightEvent(Base):
    __tablename__ = "low_light_events"
    
    id = Column(Integer, primary_key=True, index=True)
    low_light_event_id = Column(String, unique=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    low_light_threshold_used = Column(Float, nullable=False)  # Threshold used for low light detection

class GPSEvent(Base):
    __tablename__ = "gps_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gps_event_id = Column(String, nullable=False, unique=True)
    user_uid = Column(String, ForeignKey('users.uid'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    bearing = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    speed_accuracy_meters_per_second = Column(Float, nullable=False)
    timestamp_now = Column(DateTime, nullable=False)