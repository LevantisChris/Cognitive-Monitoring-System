from cmath import log
from datetime import datetime, timedelta, time, date
from annotated_types import Unit
from pandas.core.dtypes.cast import dt
from scipy.stats import entropy
from typing import List
from haversine import haversine, Unit
from sklearn.metrics.pairwise import haversine_distances
from math import radians
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull
import pyproj
from geopy.distance import distance
from sklearn.decomposition import PCA
import numpy as np

from app.config import settings
import pandas as pd

from app.services.database_service import DatabaseService
from app.services.supabase_service import SupabaseService

import logging

logger = logging.getLogger(__name__)

# Service class responsible for data analysis

class AnalysisService:
    def __init__(self, db_service: DatabaseService, supabase_service: SupabaseService):
        self.timezone = settings.DEFAULT_TIMEZONE
        self.db_service = db_service
        self.supabase_service = supabase_service

    def start_logboard_data_analysis(self, user_uid: str, analysis_start_datetime: datetime, analysis_end_datetime: datetime):
        logger.info(f"\n\n--Starting LogBoard data analysis, for user {user_uid}--\n\n")

        # First check if the user has any sessions in the local database
        if not self.db_service.check_if_user_has_typing_sessions(user_uid):
            logger.info(f"User {user_uid} has no typing sessions in local database, skipping analysis...")
            return {"status": "no typing sessions found", "user_uid": user_uid}

        # Get the typing sessions for the user
        typing_sessions = self.db_service.get_typing_sessions_of_a_user(user_uid, analysis_start_datetime, analysis_end_datetime)

        if len(typing_sessions) == 0:
            logger.info(f"No typing sessions found for user {user_uid}.")
            return {"status": "no typing sessions found", "user_uid": user_uid}

        # Pressure Intensity computation and storing in Supabase
        # Get the latest baseline information for the user about the metric
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'PRESSURE_INTENSITY')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric PRESSURE_INTENSITY.\033[0m")
        self._compute_and_store_pressure_intensity(user_uid, typing_sessions, bl_rec)

        # Effort to Output Ration computation
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'EFFORT_TO_OUTPUT_RATIO')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric EFFORT_TO_OUTPUT_RATIO.\033[0m")
        self._compute_and_store_effort_to_output_ratio(user_uid, typing_sessions, bl_rec)

        # Typing Rhythm Stability
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'TYPING_RHYTHM_STABILITY')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric TYPING_RHYTHM_STABILITY.\033[0m")
        self._compute_and_store_typing_rhythm_stability(user_uid, typing_sessions, bl_rec)

        # Cognitive Processing Index
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'COGNITIVE_PROCESSING_INDEX')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric COGNITIVE_PROCESSING_INDEX.\033[0m")
        self._compute_and_store_cognitive_processing_index(user_uid, typing_sessions, bl_rec)

        # Pause to Production Ratio
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'PAUSE_TO_PRODUCTION_RATIO')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric PAUSE_TO_PRODUCTION_RATIO.\033[0m")
        self._compute_and_store_pause_to_production_ratio(user_uid, typing_sessions, bl_rec)

        # Correction Efficiency
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'CORRECTION_EFFICIENCY')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric CORRECTION_EFFICIENCY.\033[0m")
        self._compute_and_store_correction_efficiency(user_uid, typing_sessions, bl_rec)

        # Net Production Rate
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'NET_PRODUCTION_RATE')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric NET_PRODUCTION_RATE.\033[0m")
        self._compute_and_store_net_production_rate(user_uid, typing_sessions, bl_rec)

        # Cognitive Processing Efficiency
        bl_rec = self.supabase_service.get_user_baseline_metric_values(user_uid, 'COGNITIVE_PROCESSING_EFFICIENCY')
        if bl_rec is None:
            logger.warning(f"\033[93mBaseline record not found for user {user_uid} and metric COGNITIVE_PROCESSING_EFFICIENCY.\033[0m")
        self._compute_and_store_cognitive_processing_efficiency(user_uid, typing_sessions, bl_rec)

        # Update the baseline metrics
        state = self._update_typing_baseline_metrics(user_uid)

        # NOTE: state will be True in 3 cases:
        # 1) Creates New Baselines (No baselines exist)
        # 2) Updates Existing Baselines (Baselines need refresh)
        # 3) Baseline Already Valid (No action needed)
        # False in any other case and of course errors

        if not state:
            status = self._calculate_typing_score_and_decision(user_uid, analysis_start_datetime, analysis_end_datetime)
            if not status:
                logger.error(f"Failed to update the cognitive score and final decision for user {user_uid}.")
                return {"status": "error", "error": "Failed to update the cognitive score and final decision."}
        else:
            logger.warning(f"\033[93mCannot proceed with the update of the cognitive score and final decision for user {user_uid}.\033[0m")
        
        return {"status": "success", "user_uid": user_uid}

    def start_logmyself_data_analysis(self, user_uid: str, analysis_start_datetime: datetime, analysis_end_datetime: datetime) -> dict | None:
        logger.info(f"\n\n--Starting LogMyself data analysis, for user {user_uid}--\n\n")

        # JSON that will hold the logmyself analysis results
        logmyself_analysis_final_status = {}

        # Sleep Behavior Analysis
        logger.info(f"\033[94m\n\n--Starting sleep behavior analysis for user {user_uid} at {analysis_start_datetime} and {analysis_end_datetime}--\033[0m")
        all_sleep_analysis_results = self._calc_sleep_data(user_uid, analysis_start_datetime, analysis_end_datetime)
        logger.info(f"\033[94m\n\n*Sleep behavior analysis results: {all_sleep_analysis_results}*\033[0m")
        if all_sleep_analysis_results is not None and len(all_sleep_analysis_results) > 0:
            # Send all sleep data to Supabase (both main sleep and naps)
            sleep_data_analysis_ids = self.supabase_service.send_computed_sleep_info(user_uid, all_sleep_analysis_results, analysis_start_datetime.date())
            
            # Find main sleep for Z-score calculations
            main_sleep_data = None
            main_sleep_id = None
            logger.info(f"Searching for main_sleep in {len(all_sleep_analysis_results)} sleep analysis results")
            for i, sleep_data in enumerate(all_sleep_analysis_results):
                logger.info(f"Sleep data {i}: type={sleep_data.get('type')}, sqs={sleep_data.get('sqs')}")
                if sleep_data.get('type') == 'main_sleep':
                    main_sleep_data = sleep_data
                    logger.info(f"Found main_sleep at index {i}")
                    if sleep_data_analysis_ids and isinstance(sleep_data_analysis_ids, list) and i < len(sleep_data_analysis_ids):
                        main_sleep_id = sleep_data_analysis_ids[i]
                        logger.info(f"Matched main_sleep_id: {main_sleep_id}")
                    else:
                        logger.error(f"Failed to match main_sleep_id: sleep_data_analysis_ids={sleep_data_analysis_ids}, index={i}")
                    break
            
            if main_sleep_data is not None and main_sleep_id is not None:
                logger.info(f"Computed sleep data stored successfully. Main sleep ID: {main_sleep_id}")
                # Calculate the Z-Scores for main sleep data for the day analyzed
                sleep_duration = main_sleep_data.get('estimated_end_date_time') - main_sleep_data.get('estimated_start_date_time')
                logger.info(f"Calling Z-score calculation for main sleep with duration: {sleep_duration}")
                self._calculate_z_scores_for_sleep_data(
                    main_sleep_id,
                    user_uid, 
                    sleep_duration, 
                    main_sleep_data.get('sqs'), 
                    main_sleep_data.get('estimated_start_date_time'),
                    main_sleep_data.get('estimated_end_date_time')
                )
                logmyself_analysis_final_status['sleep_analysis_success'] = True
            else:
                logger.error(f"   CRITICAL: No main sleep found or failed to store main sleep data.")
                logger.error(f"   main_sleep_data is None: {main_sleep_data is None}")
                logger.error(f"   main_sleep_id is None: {main_sleep_id is None}")
                logger.error(f"   sleep_data_analysis_ids: {sleep_data_analysis_ids}")
                logmyself_analysis_final_status['sleep_analysis_success'] = False
        else:
            logger.error(f"No sleep data found for analysis.")
            logmyself_analysis_final_status['sleep_analysis_success'] = False

        # Daily Device Interaction Behavior Analysis
        logger.info(f"\033[94m\n\n--Starting daily device interaction analysis for user {user_uid} at {analysis_start_datetime} and {analysis_end_datetime}--\033[0m")
        device_interaction_analysis_result = self._calc_device_interaction_data(user_uid, analysis_start_datetime, analysis_end_datetime)
        logger.info(f"\033[94m\n\n*Daily device interaction analysis result: {device_interaction_analysis_result}*\033[0m")
        if device_interaction_analysis_result is not None:
            interaction_data_analysis_id = self.supabase_service.send_computed_device_interaction_info(user_uid, device_interaction_analysis_result, analysis_start_datetime.date())
            if interaction_data_analysis_id is not None:
                logger.info(f"Computed device interaction data stored successfully.")
                # Calculate the Z-Scores for device interaction data for the day analyzed
                self._calculate_z_scores_for_device_interaction_data(
                    interaction_data_analysis_id,
                    user_uid, 
                    device_interaction_analysis_result.get('screen_time_analysis_result'),
                    device_interaction_analysis_result.get('low_light_day_time_result'),
                    device_interaction_analysis_result.get('device_drop_events_result'),
                )
                logmyself_analysis_final_status['device_interaction_analysis_success'] = True
            else:
                logger.error(f"Failed to store computed device interaction data.")
                logmyself_analysis_final_status['device_interaction_analysis_success'] = False

        # Activity Behavior Analysis
        logger.info(f"\033[94m\n\n--Starting activity analysis for user {user_uid} at {analysis_start_datetime} and {analysis_end_datetime}--\033[0m")
        activity_analysis_result = self._calc_activity_data(user_uid, analysis_start_datetime, analysis_end_datetime)
        logger.info(f"\033[94m\n\n*Activity behavior analysis result: {activity_analysis_result}*\033[0m")
        if activity_analysis_result is not None:
            activity_data_analysis_id = self.supabase_service.send_computed_activity_info(user_uid, activity_analysis_result, analysis_start_datetime.date())
            if activity_data_analysis_id is not None:
                logger.info(f"Computed activity data stored successfully.")
                # Calculate the Z-Scores for activity data for the day analyzed
                self._calculate_z_scores_for_activity_data(
                    activity_data_analysis_id,
                    user_uid,
                    activity_analysis_result.get('daily_active_minutes'),
                )
                logmyself_analysis_final_status['activity_analysis_success'] = True
            else:
                logger.error(f"Failed to store computed activity data.")
                logmyself_analysis_final_status['activity_analysis_success'] = False

        # Call Behavior Analysis - Social Interaction Behavior Analysis
        logger.info(f"\033[94m\n\n--Starting call analysis for user {user_uid} at {analysis_start_datetime} and {analysis_end_datetime}--\033[0m")
        call_analysis_result = self._calc_call_data(user_uid, analysis_start_datetime, analysis_end_datetime)
        logger.info(f"\033[94m\n\n*Call behavior analysis result: {call_analysis_result}*\033[0m")
        if call_analysis_result is not None:
            call_data_analysis_id = self.supabase_service.send_computed_call_info(user_uid, call_analysis_result, analysis_start_datetime.date())
            if call_data_analysis_id is not None:
                logger.info(f"Computed call data stored successfully.")
                # Calculate the Z-Scores for call data for the day analyzed
                self._calculate_z_scores_for_call_data(
                    call_data_analysis_id,
                    user_uid,
                    call_analysis_result.get('missed_call_ratio'),
                    call_analysis_result.get('avg_call_duration'),
                    call_analysis_result.get('total_calls_in_a_day')
                )
                logmyself_analysis_final_status['call_analysis_success'] = True
            else:
                logger.error(f"Failed to store computed call data.")
                logmyself_analysis_final_status['call_analysis_success'] = False

        # GPS Behavior Analysis - Mobility Behavior Analysis
        logger.info(f"\033[94m\n\n--Starting GPS analysis for user {user_uid} at {analysis_start_datetime} and {analysis_end_datetime}--\033[0m")
        gps_analysis_result = self._calc_gps_data(user_uid, analysis_start_datetime, analysis_end_datetime)
        logger.info(f"\033[94m\n\n*GPS behavior analysis result: {gps_analysis_result}*\033[0m")
        if gps_analysis_result is not None:
            gps_data_analysis_id = self.supabase_service.send_computed_gps_info(user_uid, gps_analysis_result, analysis_start_datetime.date())
            if gps_data_analysis_id is not None:
                logger.info(f"Computed GPS data stored successfully.")
                # Calculate the Z-Scores for GPS data for the day analyzed
                self._calculate_z_scores_for_gps_data(
                    gps_data_analysis_id,
                    user_uid,
                    gps_analysis_result.get('total_time_spend_in_home_seconds'),
                    gps_analysis_result.get('total_time_spend_traveling_seconds'),
                    gps_analysis_result.get('total_time_spend_out_of_home_seconds'),
                    gps_analysis_result.get('total_distance_traveled_km'),
                    gps_analysis_result.get('average_time_spend_in_locations_hours'),
                    gps_analysis_result.get('number_of_unique_locations'),
                    gps_analysis_result.get('convex_hull', {}).get('area_m2'),
                    gps_analysis_result.get('standard_deviation_ellipse', {}).get('area_m2'),
                    gps_analysis_result.get('max_distance_from_home', {}).get('timestamp'),
                    gps_analysis_result.get('entropy'),
                )
                logmyself_analysis_final_status['gps_analysis_success'] = True
            else:
                logger.error(f"Failed to store computed GPS data.")
                logmyself_analysis_final_status['gps_analysis_success'] = False

        # Update the baseline metrics
        state = self._update_behavioral_baseline_metrics(user_uid)

        if state.get('success'):
            if state.get('isFirstTime'):
                logger.info(f"Successfully created baseline data for user {user_uid}, this is the first time")
                backfill_status = self._backfill_behavioral_zscores_and_decisions(user_uid, analysis_start_datetime.date())
                if not backfill_status:
                    logger.error(f"Failed to backfill the behavioral z-scores and decisions for user {user_uid}.")
                    return {"status": "error", "error": "Failed to backfill the behavioral z-scores and decisions."}
            else:
                logger.info(f"Successfully updated baseline data for user {user_uid}, this is not the first time, continuing normal flow...")

            status = self._calculate_behavioral_score_and_decision(user_uid, analysis_start_datetime.date())
            if not status:
                logger.error(f"Failed to update the behavioral score and final decision for user {user_uid}.")
                return {"status": "error", "error": "Failed to update the behavioral score and final decision."}
        else:
            logger.warning(f"\033[93mCannot proceed with the update of the behavioral score and final decision for user {user_uid}.\033[0m")

        # Result like:
        # {
        #     "sleep_analysis_success": True,
        #     "device_interaction_analysis_success": True,
        #     "activity_analysis_success": True,
        #     "call_analysis_success": True,
        #     "gps_analysis_success": True
        # }
        return logmyself_analysis_final_status
    
    def _backfill_behavioral_zscores_and_decisions(self, user_uid: str, day_analyzed: date):
        """
            This function is responsible for backfilling the behavioral z-scores and decisions for a user.
            When the system creates for the first time baseline data for a user, Z-Scores, decisions and scores
            must be filled for the 1st to 14th days before the day analyzed.
        Args:
            user_uid: str - The user's unique identifier
            day_analyzed: datetime - The day analyzed
        Returns:
            bool - True if the behavioral z-scores and decisions were backfilled successfully, False otherwise
        """

        logger.info(f"Backfilling the behavioral z-scores and decisions for user {user_uid}")

        # TODO: To be implemented (maybe version 2 is not so important for this version)

        logger.info(f"To be implemented (maybe version 2 is not so important for this version)")
        
        return True
    
    def _calculate_z_scores_for_sleep_data(self, sleep_data_analysis_id: int, user_uid: str, sleep_time, sqs, start_time, end_time):
        logger.info(f"Updating the z-scores for sleep data for user {user_uid}")

        try:

            # --- Sleep Time ---
            bl_rec_sleep_time = self.supabase_service.get_user_baseline_metric_values(user_uid, 'SLEEP_TIME')
            z_score_sleep_time = None
            if bl_rec_sleep_time is not None:
                logger.info(f"Calculating z-score for sleep time for user {user_uid} with baseline record found with bl-data {bl_rec_sleep_time}")
                z_score_sleep_time = self._calc_modified_z_score(sleep_time, bl_rec_sleep_time.get('baseline_median'), bl_rec_sleep_time.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for sleep time for user {user_uid}")

            # --- Sleep Quality Score ---
            bl_rec_sqs = self.supabase_service.get_user_baseline_metric_values(user_uid, 'SQS')
            z_score_sqs = 0
            if bl_rec_sqs is not None:
                logger.info(f"Calculating z-score for sleep quality score for user {user_uid} with baseline record found with bl-data {bl_rec_sqs}")
                z_score_sqs = self._calc_modified_z_score(sqs, bl_rec_sqs.get('baseline_median'), bl_rec_sqs.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for sleep quality score for user {user_uid}")

            # --- Sleep Start Time (normalize to minutes since midnight) ---
            def to_minutes(t):
                if isinstance(t, dt.time):
                    return t.hour * 60 + t.minute
                elif hasattr(t, 'time'):  # pandas Timestamp or datetime objects
                    time_obj = t.time()
                    return time_obj.hour * 60 + time_obj.minute
                elif hasattr(t, 'hour') and hasattr(t, 'minute'):  # datetime objects
                    return t.hour * 60 + t.minute
                else:
                    # If it's already a numeric value (minutes), return as-is
                    try:
                        return float(t)
                    except (ValueError, TypeError):
                        logger.error(f"Unable to convert time value to minutes: {t} (type: {type(t)})")
                        return 0

            current_start_time_minutes = to_minutes(start_time)
            logger.debug(f"Converted start_time {start_time} (type: {type(start_time)}) to {current_start_time_minutes} minutes")
            
            bl_rec_sleep_start_time = self.supabase_service.get_user_baseline_metric_values(user_uid, 'SLEEP_START_TIME')
            z_score_sleep_start_time = None
            if bl_rec_sleep_start_time:
                try:
                    logger.info(f"Calculating z-score for sleep start time for user {user_uid} with baseline record found with bl-data {bl_rec_sleep_start_time}")
                    z_score_sleep_start_time = self._calc_modified_z_score(
                        current_start_time_minutes,
                        bl_rec_sleep_start_time.get('baseline_median'),
                        bl_rec_sleep_start_time.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for sleep start time: {e}")
                    logger.error(f"Values: current={current_start_time_minutes} (type: {type(current_start_time_minutes)}), median={bl_rec_sleep_start_time.get('baseline_median')}, mad={bl_rec_sleep_start_time.get('baseline_mad')}")
                    z_score_sleep_start_time = None
            else:
                logger.info(f"No baseline record found for sleep start time for user {user_uid}")

            # --- Sleep End Time (normalize too) ---
            current_end_time_minutes = to_minutes(end_time)
            logger.debug(f"Converted end_time {end_time} (type: {type(end_time)}) to {current_end_time_minutes} minutes")
            
            bl_rec_sleep_end_time = self.supabase_service.get_user_baseline_metric_values(user_uid, 'SLEEP_END_TIME')
            z_score_sleep_end_time = None
            if bl_rec_sleep_end_time:
                try:
                    logger.info(f"Calculating z-score for sleep end time for user {user_uid} with baseline record found with bl-data {bl_rec_sleep_end_time}")
                    z_score_sleep_end_time = self._calc_modified_z_score(
                        current_end_time_minutes,
                        bl_rec_sleep_end_time.get('baseline_median'),
                        bl_rec_sleep_end_time.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for sleep end time: {e}")
                    logger.error(f"Values: current={current_end_time_minutes} (type: {type(current_end_time_minutes)}), median={bl_rec_sleep_end_time.get('baseline_median')}, mad={bl_rec_sleep_end_time.get('baseline_mad')}")
                    z_score_sleep_end_time = None
            else:
                logger.info(f"No baseline record found for sleep end time for user {user_uid}")
            
            # Check which z-scores were successfully calculated
            valid_z_scores = []
            if z_score_sleep_time is not None:
                valid_z_scores.append("sleep_time")
            if z_score_sqs is not None:
                valid_z_scores.append("sqs")
            if z_score_sleep_start_time is not None:
                valid_z_scores.append("sleep_start_time")
            if z_score_sleep_end_time is not None:
                valid_z_scores.append("sleep_end_time")
            
            if not valid_z_scores:
                logger.error(f"Failed to calculate any z-scores for sleep data for user {user_uid}")
                return False
            
            logger.info(f"Successfully calculated z-scores for: {', '.join(valid_z_scores)} for user {user_uid}")
            
            # Use 0 as default for missing z-scores to prevent database update failures
            z_score_sleep_time = z_score_sleep_time if z_score_sleep_time is not None else 0
            z_score_sqs = z_score_sqs if z_score_sqs is not None else 0
            z_score_sleep_start_time = z_score_sleep_start_time if z_score_sleep_start_time is not None else 0
            z_score_sleep_end_time = z_score_sleep_end_time if z_score_sleep_end_time is not None else 0
            
            # Update the z-scores for the sleep data
            status = self.supabase_service.create_z_scores_for_sleep_data(user_uid, sleep_data_analysis_id, z_score_sleep_time, z_score_sqs, z_score_sleep_start_time, z_score_sleep_end_time)
            if status is False:
                logger.error(f"Failed to create the z-scores for sleep data for user {user_uid}")
            return status
        except Exception as e:
            logger.error(f"Error updating the z-scores for sleep data for user {user_uid}: {e}")

    def _calculate_z_scores_for_device_interaction_data(self, interaction_data_analysis_id: int, user_uid: str, screen_time_analysis_result: float, low_light_day_time_result: float, device_drop_events_result: float):
        logger.info(f"Updating the z-scores for device interaction data for user {user_uid}")

        try:
            # --- Screen Time ---
            bl_rec_screen_time = self.supabase_service.get_user_baseline_metric_values(user_uid, 'SCREEN_TIME')
            z_score_screen_time = None
            if bl_rec_screen_time is not None:
                try:
                    logger.info(f"Calculating z-score for screen time for user {user_uid}")
                    z_score_screen_time = self._calc_modified_z_score(
                        screen_time_analysis_result, 
                        bl_rec_screen_time.get('baseline_median'), 
                        bl_rec_screen_time.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for screen time: {e}")
                    logger.error(f"Values: screen_time={screen_time_analysis_result}, median={bl_rec_screen_time.get('baseline_median')}, mad={bl_rec_screen_time.get('baseline_mad')}")
                    z_score_screen_time = None
            else:
                logger.info(f"No baseline record found for screen time for user {user_uid}")
            
            # --- Low Light Time ---
            bl_rec_low_light_day_time = self.supabase_service.get_user_baseline_metric_values(user_uid, 'LOW_LIGHT_TIME')
            z_score_low_light_day_time = None
            if bl_rec_low_light_day_time is not None:
                try:
                    logger.info(f"Calculating z-score for low light time for user {user_uid}")
                    z_score_low_light_day_time = self._calc_modified_z_score(
                        low_light_day_time_result, 
                        bl_rec_low_light_day_time.get('baseline_median'), 
                        bl_rec_low_light_day_time.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for low light time: {e}")
                    logger.error(f"Values: low_light={low_light_day_time_result}, median={bl_rec_low_light_day_time.get('baseline_median')}, mad={bl_rec_low_light_day_time.get('baseline_mad')}")
                    z_score_low_light_day_time = None
            else:
                logger.info(f"No baseline record found for low light time for user {user_uid}")
            
            # --- Device Drop Events ---
            bl_rec_device_drop_events = self.supabase_service.get_user_baseline_metric_values(user_uid, 'DEVICE_DROP_EVENTS')
            z_score_device_drop_events = None
            if bl_rec_device_drop_events is not None:
                try:
                    logger.info(f"Calculating z-score for device drop events for user {user_uid}")
                    z_score_device_drop_events = self._calc_modified_z_score(
                        device_drop_events_result, 
                        bl_rec_device_drop_events.get('baseline_median'), 
                        bl_rec_device_drop_events.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for device drop events: {e}")
                    logger.error(f"Values: drop_events={device_drop_events_result}, median={bl_rec_device_drop_events.get('baseline_median')}, mad={bl_rec_device_drop_events.get('baseline_mad')}")
                    z_score_device_drop_events = None
            else:
                logger.info(f"No baseline record found for device drop events for user {user_uid}")

            # Check which z-scores were successfully calculated
            valid_z_scores = []
            if z_score_screen_time is not None:
                valid_z_scores.append("screen_time")
            if z_score_low_light_day_time is not None:
                valid_z_scores.append("low_light_time")
            if z_score_device_drop_events is not None:
                valid_z_scores.append("device_drop_events")
            
            if not valid_z_scores:
                logger.error(f"Failed to calculate any z-scores for device interaction data for user {user_uid}")
                return False
            
            logger.info(f"Successfully calculated z-scores for: {', '.join(valid_z_scores)} for user {user_uid}")
            
            # Use 0 as default for missing z-scores to prevent database update failures
            z_score_screen_time = z_score_screen_time if z_score_screen_time is not None else 0
            z_score_low_light_day_time = z_score_low_light_day_time if z_score_low_light_day_time is not None else 0
            z_score_device_drop_events = z_score_device_drop_events if z_score_device_drop_events is not None else 0
            
            # Update the z-scores for the device interaction data
            status = self.supabase_service.create_z_scores_for_device_interaction_data(user_uid, interaction_data_analysis_id, z_score_screen_time, z_score_low_light_day_time, z_score_device_drop_events)
            if status is False:
                logger.error(f"Failed to create the z-scores for device interaction data for user {user_uid}")
            return status
        except Exception as e:
            logger.error(f"Error creating the z-scores for device interaction data for user {user_uid}: {e}")
    
    def _calculate_z_scores_for_activity_data(self, activity_data_analysis_id: int, user_uid: str, daily_active_minutes: float):
        logger.info(f"Updating the z-scores for activity data for user {user_uid}")
        
        try:
            # --- Daily Active Minutes ---
            bl_rec_daily_active_minutes = self.supabase_service.get_user_baseline_metric_values(user_uid, 'ACTIVE_MINUTES')
            z_score_daily_active_minutes = None
            if bl_rec_daily_active_minutes is not None:
                try:
                    logger.info(f"Calculating z-score for daily active minutes for user {user_uid}")
                    z_score_daily_active_minutes = self._calc_modified_z_score(
                        daily_active_minutes, 
                        bl_rec_daily_active_minutes.get('baseline_median'), 
                        bl_rec_daily_active_minutes.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for daily active minutes: {e}")
                    logger.error(f"Values: active_minutes={daily_active_minutes}, median={bl_rec_daily_active_minutes.get('baseline_median')}, mad={bl_rec_daily_active_minutes.get('baseline_mad')}")
                    z_score_daily_active_minutes = None
            else:
                logger.info(f"No baseline record found for daily active minutes for user {user_uid}")
            
            # Use 0 as default if calculation failed
            z_score_daily_active_minutes = z_score_daily_active_minutes if z_score_daily_active_minutes is not None else 0
            logger.info(f"Successfully calculated z-score for daily active minutes: {z_score_daily_active_minutes} for user {user_uid}")

            # Create the z-scores for the activity data
            status = self.supabase_service.create_z_scores_for_activity_data(user_uid, activity_data_analysis_id, z_score_daily_active_minutes)
            if status is False:
                logger.error(f"Failed to create the z-scores for activity data for user {user_uid}")

            return status
        except Exception as e:
            logger.error(f"Error creating the z-scores for activity data for user {user_uid}: {e}")
            return False
    
    def _calculate_z_scores_for_call_data(self, call_data_analysis_id: int, user_uid: str, missed_call_ratio: float, avg_call_duration: float, total_calls_in_a_day: int):
        logger.info(f"Updating the z-scores for call data for user {user_uid}")
        
        try:
            # --- Missed Call Ratio ---
            bl_rec_missed_call_ratio = self.supabase_service.get_user_baseline_metric_values(user_uid, 'MISSED_CALL_RATIO')
            z_score_missed_call_ratio = None
            if bl_rec_missed_call_ratio is not None:
                try:
                    logger.info(f"Calculating z-score for missed call ratio for user {user_uid}")
                    z_score_missed_call_ratio = self._calc_modified_z_score(
                        missed_call_ratio, 
                        bl_rec_missed_call_ratio.get('baseline_median'), 
                        bl_rec_missed_call_ratio.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for missed call ratio: {e}")
                    logger.error(f"Values: ratio={missed_call_ratio}, median={bl_rec_missed_call_ratio.get('baseline_median')}, mad={bl_rec_missed_call_ratio.get('baseline_mad')}")
                    z_score_missed_call_ratio = None
            else:
                logger.info(f"No baseline record found for missed call ratio for user {user_uid}")
            
            # --- Avg Call Duration ---
            bl_rec_avg_call_duration = self.supabase_service.get_user_baseline_metric_values(user_uid, 'AVG_CALL_DURATION')
            z_score_avg_call_duration = None
            if bl_rec_avg_call_duration is not None:
                try:
                    logger.info(f"Calculating z-score for avg call duration for user {user_uid}")
                    z_score_avg_call_duration = self._calc_modified_z_score(
                        avg_call_duration, 
                        bl_rec_avg_call_duration.get('baseline_median'), 
                        bl_rec_avg_call_duration.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for avg call duration: {e}")
                    logger.error(f"Values: duration={avg_call_duration}, median={bl_rec_avg_call_duration.get('baseline_median')}, mad={bl_rec_avg_call_duration.get('baseline_mad')}")
                    z_score_avg_call_duration = None
            else:
                logger.info(f"No baseline record found for avg call duration for user {user_uid}")
            
            # --- Total Calls in a Day ---
            bl_rec_total_calls_in_a_day = self.supabase_service.get_user_baseline_metric_values(user_uid, 'TOTAL_CALLS_IN_A_DAY')
            z_score_total_calls_in_a_day = None
            if bl_rec_total_calls_in_a_day is not None:
                try:
                    logger.info(f"Calculating z-score for total calls in a day for user {user_uid}")
                    z_score_total_calls_in_a_day = self._calc_modified_z_score(
                        total_calls_in_a_day, 
                        bl_rec_total_calls_in_a_day.get('baseline_median'), 
                        bl_rec_total_calls_in_a_day.get('baseline_mad')
                    )
                except Exception as e:
                    logger.error(f"Error calculating z-score for total calls in a day: {e}")
                    logger.error(f"Values: total={total_calls_in_a_day}, median={bl_rec_total_calls_in_a_day.get('baseline_median')}, mad={bl_rec_total_calls_in_a_day.get('baseline_mad')}")
                    z_score_total_calls_in_a_day = None
            else:
                logger.info(f"No baseline record found for total calls in a day for user {user_uid}")
            
            # Check which z-scores were successfully calculated
            valid_z_scores = []
            if z_score_missed_call_ratio is not None:
                valid_z_scores.append("missed_call_ratio")
            if z_score_avg_call_duration is not None:
                valid_z_scores.append("avg_call_duration")
            if z_score_total_calls_in_a_day is not None:
                valid_z_scores.append("total_calls_in_a_day")
            
            if not valid_z_scores:
                logger.error(f"Failed to calculate any z-scores for call data for user {user_uid}")
                return False
            
            logger.info(f"Successfully calculated z-scores for: {', '.join(valid_z_scores)} for user {user_uid}")
            
            # Use 0 as default for missing z-scores to prevent database update failures
            z_score_missed_call_ratio = z_score_missed_call_ratio if z_score_missed_call_ratio is not None else 0
            z_score_avg_call_duration = z_score_avg_call_duration if z_score_avg_call_duration is not None else 0
            z_score_total_calls_in_a_day = z_score_total_calls_in_a_day if z_score_total_calls_in_a_day is not None else 0
            
            # Create the z-scores for the call data
            status = self.supabase_service.create_z_scores_for_call_data(user_uid, call_data_analysis_id, z_score_missed_call_ratio, z_score_avg_call_duration, z_score_total_calls_in_a_day)
            if status is False:
                logger.error(f"Failed to create the z-scores for call data for user {user_uid}")
            return status
        except Exception as e:
            logger.error(f"Error creating the z-scores for call data for user {user_uid}: {e}")
            return False
    
    def _calculate_z_scores_for_gps_data(self, gps_data_analysis_id: int, user_uid: str, total_time_spend_in_home_seconds: float, total_time_spend_traveling_seconds: float, total_time_spend_out_of_home_seconds: float, total_distance_traveled_km: float, average_time_spend_in_locations_hours: float, number_of_unique_locations: int, convex_hull_area_m2: float, standard_deviation_ellipse_area_m2: float, max_distance_from_home_timestamp: datetime, entropy: float):
        logger.info(f"Calculating GPS Z-scores for user {user_uid}, GPS analysis ID: {gps_data_analysis_id}")
        logger.info(f"GPS values: home_time={total_time_spend_in_home_seconds}, travel_time={total_time_spend_traveling_seconds}, out_time={total_time_spend_out_of_home_seconds}")
        logger.info(f"GPS values: distance={total_distance_traveled_km}, locations={number_of_unique_locations}, entropy={entropy}")
        try:
            # --- Total Time Spend in Home Seconds ---
            bl_rec_total_time_spend_in_home_seconds = self.supabase_service.get_user_baseline_metric_values(user_uid, 'TIME_SPEND_IN_HOME')
            z_score_total_time_spend_in_home_seconds = None
            if bl_rec_total_time_spend_in_home_seconds is not None:
                z_score_total_time_spend_in_home_seconds = self._calc_modified_z_score(total_time_spend_in_home_seconds, bl_rec_total_time_spend_in_home_seconds.get('baseline_median'), bl_rec_total_time_spend_in_home_seconds.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for total time spend in home seconds for user {user_uid}")
            
            # --- Total Time Spend Traveling Seconds ---
            bl_rec_total_time_spend_traveling_seconds = self.supabase_service.get_user_baseline_metric_values(user_uid, 'TIME_SPEND_TRAVELLING')
            z_score_total_time_spend_traveling_seconds = None
            if bl_rec_total_time_spend_traveling_seconds is not None:
                z_score_total_time_spend_traveling_seconds = self._calc_modified_z_score(total_time_spend_traveling_seconds, bl_rec_total_time_spend_traveling_seconds.get('baseline_median'), bl_rec_total_time_spend_traveling_seconds.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for total time spend traveling seconds for user {user_uid}")
                
            # --- Total Time Spend Out of Home Seconds ---
            bl_rec_total_time_spend_out_of_home_seconds = self.supabase_service.get_user_baseline_metric_values(user_uid, 'TIME_SPEND_OUT_OF_HOME')
            z_score_total_time_spend_out_of_home_seconds = None
            if bl_rec_total_time_spend_out_of_home_seconds is not None:
                z_score_total_time_spend_out_of_home_seconds = self._calc_modified_z_score(total_time_spend_out_of_home_seconds, bl_rec_total_time_spend_out_of_home_seconds.get('baseline_median'), bl_rec_total_time_spend_out_of_home_seconds.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for total time spend out of home seconds for user {user_uid}")
            
            # --- Total Distance Traveled KM ---
            bl_rec_total_distance_traveled_km = self.supabase_service.get_user_baseline_metric_values(user_uid, 'DISTANCE_TRAVELLED')
            z_score_total_distance_traveled_km = None
            if bl_rec_total_distance_traveled_km is not None:
                z_score_total_distance_traveled_km = self._calc_modified_z_score(total_distance_traveled_km, bl_rec_total_distance_traveled_km.get('baseline_median'), bl_rec_total_distance_traveled_km.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for total distance traveled km for user {user_uid}")
            
            # --- Average Time Spend in Locations Hours ---
            bl_rec_average_time_spend_in_locations_hours = self.supabase_service.get_user_baseline_metric_values(user_uid, 'AVERAGE_TIME_SPEND_IN_LOCATIONS')
            z_score_average_time_spend_in_locations_hours = None
            if bl_rec_average_time_spend_in_locations_hours is not None:
                z_score_average_time_spend_in_locations_hours = self._calc_modified_z_score(average_time_spend_in_locations_hours, bl_rec_average_time_spend_in_locations_hours.get('baseline_median'), bl_rec_average_time_spend_in_locations_hours.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for average time spend in locations hours for user {user_uid}")

            # --- Number of Unique Locations ---
            bl_rec_number_of_unique_locations = self.supabase_service.get_user_baseline_metric_values(user_uid, 'NUMBER_OF_UNIQUE_LOCATIONS')
            z_score_number_of_unique_locations = None
            if bl_rec_number_of_unique_locations is not None:
                z_score_number_of_unique_locations = self._calc_modified_z_score(number_of_unique_locations, bl_rec_number_of_unique_locations.get('baseline_median'), bl_rec_number_of_unique_locations.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for number of unique locations for user {user_uid}")

            # --- Convex Hull Area M2 ---
            bl_rec_convex_hull_area_m2 = self.supabase_service.get_user_baseline_metric_values(user_uid, 'CONVEX_HULL_AREA')
            z_score_convex_hull_area_m2 = None
            if bl_rec_convex_hull_area_m2 is not None:
                z_score_convex_hull_area_m2 = self._calc_modified_z_score(convex_hull_area_m2, bl_rec_convex_hull_area_m2.get('baseline_median'), bl_rec_convex_hull_area_m2.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for convex hull area m2 for user {user_uid}")

            # --- Standard Deviation Ellipse Area M2 ---
            bl_rec_standard_deviation_ellipse_area_m2 = self.supabase_service.get_user_baseline_metric_values(user_uid, 'SDE_AREA_M2')
            z_score_standard_deviation_ellipse_area_m2 = None
            if bl_rec_standard_deviation_ellipse_area_m2 is not None:
                z_score_standard_deviation_ellipse_area_m2 = self._calc_modified_z_score(standard_deviation_ellipse_area_m2, bl_rec_standard_deviation_ellipse_area_m2.get('baseline_median'), bl_rec_standard_deviation_ellipse_area_m2.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for standard deviation ellipse area m2 for user {user_uid}")

            # --- Max Distance Reached From Home Timestamp ---
            def _to_minutes_since_midnight(t) -> int:
                """Convert timestamp to minutes since midnight"""
                from datetime import datetime
                
                if t is None:
                    return 0
                    
                # Handle string timestamps (ISO format)
                if isinstance(t, str):
                    try:
                        t = datetime.fromisoformat(t.replace('Z', '+00:00'))
                    except ValueError:
                        logger.error(f"Failed to parse timestamp string: {t}")
                        return 0
                
                # Handle datetime objects
                if hasattr(t, 'hour') and hasattr(t, 'minute'):
                    return t.hour * 60 + t.minute
                
                logger.error(f"Unexpected timestamp format: {type(t)} - {t}")
                return 0
            
            bl_rec_max_distance_from_home_timestamp = self.supabase_service.get_user_baseline_metric_values(user_uid, 'MAX_DISTANCE_FROM_HOME_TIMESTAMP')
            z_score_max_distance_from_home_timestamp = None
            
            if max_distance_from_home_timestamp is None:
                logger.info(f"Max distance from home timestamp is None for user {user_uid}")
            elif bl_rec_max_distance_from_home_timestamp is not None:
                try:
                    minutes_since_midnight = _to_minutes_since_midnight(max_distance_from_home_timestamp)
                    z_score_max_distance_from_home_timestamp = self._calc_modified_z_score(
                        minutes_since_midnight,
                        bl_rec_max_distance_from_home_timestamp.get('baseline_median'),
                        bl_rec_max_distance_from_home_timestamp.get('baseline_mad')
                    )
                    logger.info(f"GPS max distance timestamp converted to {minutes_since_midnight} minutes since midnight")
                except Exception as e:
                    logger.error(f"Error processing max distance timestamp {max_distance_from_home_timestamp}: {e}")
                    z_score_max_distance_from_home_timestamp = None
            else:
                logger.info(f"No baseline record found for max distance from home timestamp for user {user_uid}")
            
            # --- Entropy ---
            bl_rec_entropy = self.supabase_service.get_user_baseline_metric_values(user_uid, 'ENTROPY')
            z_score_entropy = None
            if bl_rec_entropy is not None:
                z_score_entropy = self._calc_modified_z_score(entropy, bl_rec_entropy.get('baseline_median'), bl_rec_entropy.get('baseline_mad'))
            else:
                logger.info(f"No baseline record found for entropy for user {user_uid}")

            # Check which z-scores are missing and log them
            missing_z_scores = []
            z_score_dict = {
                'total_time_spend_in_home_seconds': z_score_total_time_spend_in_home_seconds,
                'total_time_spend_traveling_seconds': z_score_total_time_spend_traveling_seconds,
                'total_time_spend_out_of_home_seconds': z_score_total_time_spend_out_of_home_seconds,
                'total_distance_traveled_km': z_score_total_distance_traveled_km,
                'average_time_spend_in_locations_hours': z_score_average_time_spend_in_locations_hours,
                'number_of_unique_locations': z_score_number_of_unique_locations,
                'convex_hull_area_m2': z_score_convex_hull_area_m2,
                'sde_area_m2': z_score_standard_deviation_ellipse_area_m2,
                'max_distance_from_home_timestamp': z_score_max_distance_from_home_timestamp,
                'entropy': z_score_entropy
            }
            
            for metric_name, z_score_value in z_score_dict.items():
                if z_score_value is None:
                    missing_z_scores.append(metric_name)
            
            if missing_z_scores:
                logger.warning(f"GPS Z-scores missing baseline data for user {user_uid}: {missing_z_scores}")
                logger.warning(f"Proceeding with available z-scores, using 0.0 for missing ones")
                
                # Replace None values with 0.0 to allow partial GPS Z-score storage
                z_score_total_time_spend_in_home_seconds = z_score_total_time_spend_in_home_seconds or 0.0
                z_score_total_time_spend_traveling_seconds = z_score_total_time_spend_traveling_seconds or 0.0
                z_score_total_time_spend_out_of_home_seconds = z_score_total_time_spend_out_of_home_seconds or 0.0
                z_score_total_distance_traveled_km = z_score_total_distance_traveled_km or 0.0
                z_score_average_time_spend_in_locations_hours = z_score_average_time_spend_in_locations_hours or 0.0
                z_score_number_of_unique_locations = z_score_number_of_unique_locations or 0.0
                z_score_convex_hull_area_m2 = z_score_convex_hull_area_m2 or 0.0
                z_score_standard_deviation_ellipse_area_m2 = z_score_standard_deviation_ellipse_area_m2 or 0.0
                z_score_max_distance_from_home_timestamp = z_score_max_distance_from_home_timestamp or 0.0
                z_score_entropy = z_score_entropy or 0.0
            else:
                logger.info(f"All GPS Z-scores calculated successfully for user {user_uid}")

            # Create the z-scores for the GPS data
            logger.info(f"Saving GPS Z-scores to database for user {user_uid}")
            status = self.supabase_service.create_z_scores_for_gps_data(user_uid, gps_data_analysis_id, z_score_total_time_spend_in_home_seconds, z_score_total_time_spend_traveling_seconds, z_score_total_time_spend_out_of_home_seconds, z_score_total_distance_traveled_km, z_score_average_time_spend_in_locations_hours, z_score_number_of_unique_locations, z_score_convex_hull_area_m2, z_score_standard_deviation_ellipse_area_m2, z_score_max_distance_from_home_timestamp, z_score_entropy)
            if status is False:
                logger.error(f"Failed to create the z-scores for GPS data for user {user_uid}")
            else:
                logger.info(f"Successfully created GPS Z-scores for user {user_uid}")
            return status
        except Exception as e:
            logger.error(f"Error creating the z-scores for GPS data for user {user_uid}: {e}")

    def _update_behavioral_baseline_metrics(self, user_uid: str) -> dict[str, bool]:
        """
        This function updates the behavioral baseline metrics for a user.
        NOTE: This is will be placed inside the analysis service because we will not call any RPC function from supabase.
        Args:
            user_uid: str - The user's unique identifier
        Returns:
            dict[str, bool] - True if the baseline metrics were updated successfully, False otherwise
        """
        logger.info(f"\n\nUpdating the behavioral baseline metrics for user {user_uid}\n\n")

        # Sleep Data Analysis metrics (corresponding main table: Sleep_Data_Analysis)
        sleep_metrics = [
            ("SQS", "sqs", "std_sqs", "median_sqs", "mad_sqs"),
            ("SLEEP_START_TIME", "sleep_start_time", "std_sleep_start_time", "median_sleep_start_time", "mad_sleep_start_time"),
            ("SLEEP_END_TIME", "sleep_end_time", "std_sleep_end_time", "median_sleep_end_time", "mad_sleep_end_time"),
        ]

        # Daily Device Interaction Analysis metrics (corresponding main table: Device_Interaction_Data_Analysis)
        device_interaction_metrics = [
            ("SCREEN_TIME", "total_screen_time_sec", "std_screen_time", "median_screen_time", "mad_screen_time"),
            ("LOW_LIGHT_TIME", "total_low_light_time_sec", "std_low_light_time", "median_low_light_time", "mad_low_light_time"),
            ("DEVICE_DROP_EVENTS", "total_device_drop_events", "std_device_drop_events", "median_device_drop_events", "mad_device_drop_events"),
        ]

        # Activity Behavior Analysis metrics (corresponding main table: Activity_Data_Analysis)
        activity_metrics = [
            ("ACTIVE_MINUTES", "daily_active_minutes", "std_active_minutes", "median_active_minutes", "mad_active_minutes"),
        ]

        # Call Behavior Analysis metrics (corresponding main table: Call_Data_Analysis)
        call_metrics = [
            ("MISSED_CALL_RATIO", "missed_call_ratio", "std_missed_call_ratio", "median_missed_call_ratio", "mad_missed_call_ratio"),
            ("AVG_CALL_DURATION", "avg_call_duration", "std_avg_call_duration", "median_avg_call_duration", "mad_avg_call_duration"),
            ("TOTAL_CALLS_IN_A_DAY", "total_calls_in_a_day", "std_total_calls_in_a_day", "median_total_calls_in_a_day", "mad_total_calls_in_a_day"),
        ]

        # GPS Data Analysis metrics (corresponding main table: GPS_Data_Analysis)
        gps_metrics = [
            ("TIME_SPEND_IN_HOME", "total_time_spend_in_home_seconds", "std_time_spend_in_home", "median_time_spend_in_home", "mad_time_spend_in_home"),
            ("TIME_SPEND_TRAVELLING", "total_time_spend_travelling_seconds", "std_time_spend_traveling", "median_time_spend_traveling", "mad_time_spend_traveling"),
            ("TIME_SPEND_OUT_OF_HOME", "total_time_spend_out_of_home_seconds", "std_time_spend_out_of_home", "median_time_spend_out_of_home", "mad_time_spend_out_of_home"),
            ("DISTANCE_TRAVELLED", "total_distance_traveled_km", "std_distance_traveled", "median_distance_traveled", "mad_distance_traveled"),
            ("AVERAGE_TIME_SPEND_IN_LOCATIONS", "average_time_spend_in_locations_hours", "std_average_time_spend_in_locations", "median_average_time_spend_in_locations", "mad_average_time_spend_in_locations"),
            ("NUMBER_OF_UNIQUE_LOCATIONS", "number_of_unique_locations", "std_number_of_unique_locations", "median_number_of_unique_locations", "mad_number_of_unique_locations"),
            ("CONVEX_HULL_AREA", "convex_hull_area_m2", "std_convex_hull_area", "median_convex_hull_area", "mad_convex_hull_area"),
            ("SDE_AREA_M2", "sde_area_m2", "std_sde_area_m2", "median_sde_area_m2", "mad_sde_area_m2"),
            ("MAX_DISTANCE_FROM_HOME_TIMESTAMP", "max_distance_timestamp", "std_max_distance_from_home_timestamp", "median_max_distance_from_home_timestamp", "mad_max_distance_from_home_timestamp"),
            ("ENTROPY", "entropy", "std_entropy", "median_entropy", "mad_entropy"),
        ]

        # Combine all metrics
        # Example:
        # [(
        # name of the category, 
        # name of the main table this category corresponds to, 
        # list of statistical metrics for this category
        # )]
        metrics = [
            ("SLEEP_DATA", "Sleep_Data_Analysis", sleep_metrics),
            ("DAILY_DEVICE_INTERACTION", "Device_Interaction_Data_Analysis", device_interaction_metrics),
            ("ACTIVITY_BEHAVIOR", "Activity_Data_Analysis", activity_metrics),
            ("CALL_BEHAVIOR", "Call_Data_Analysis", call_metrics),
            ("GPS_DATA", "GPS_Data_Analysis", gps_metrics)
        ]

        try:
            select_query = "date_created, sess_end_date, Users(user_uid)"
            baseline_metrics_existed = self.supabase_service.client.table('Baseline_Metrics') \
                .select(select_query) \
                .eq("user_uid", user_uid) \
                .eq("data_category", "BEHAVIORAL_METRIC") \
                .order('date_created', desc=True) \
                .limit(1) \
                .execute()

            if not baseline_metrics_existed.data:
                logger.warning(f"No baseline metrics found for user {user_uid}")
                if not self._handle_no_baseline_behavioral_data(user_uid, metrics):
                    return {"success": False, "isFirstTime": True} # This is an error
                else:
                    return {"success": True, "isFirstTime": True} # Successfully created baseline data, this is the first time
            else:
                logger.warning(f"Baseline data already exists for user {user_uid}")
                if not self._handle_existing_baseline_behavioral_data(user_uid, baseline_metrics_existed.data, metrics):
                    return {"success": False, "isFirstTime": False} # This is an error
                else:
                    return {"success": True, "isFirstTime": False} # Successfully updated baseline data, this is not the first time
        except Exception as e:
            logger.error(f"Error updating behavioral baseline metrics for user {user_uid}: {e}")
            return {"success": False, "isFirstTime": False}

    def _handle_existing_baseline_behavioral_data(self, user_uid: str, baseline_data: list, metrics: list) -> bool:
        """Handle case when baseline behavioral data already exists for a user."""
        
        MIN_DAYS_SINCE_LAST_SESSION = 15

        try:
            for metric_category in metrics:
                metric_category_name, main_table_name, statistical_metrics_list = metric_category

                # Check if the last updated date is older than some days
                date_created = baseline_data[0]['date_created']

                if isinstance(date_created, str):
                    date_created = datetime.fromisoformat(date_created)
                
                current_date_time = datetime.now()
                time_check_passed = (current_date_time - date_created).days >= MIN_DAYS_SINCE_LAST_SESSION
                
                # Check if any baseline values are NULL for this metric category
                null_values_exist = self._check_for_null_baseline_values(user_uid, metric_category_name, statistical_metrics_list)
                
                # Skip update ONLY if time hasn't passed AND no NULL values exist
                if not time_check_passed and not null_values_exist:
                    print(f"\033[91mNot enough time has passed ({current_date_time} - {date_created}) and no NULL values found, baseline data are still valid for user {user_uid}.\033[0m")
                    continue  # Continue to next metric category instead of returning
                
                # Update baseline data if EITHER condition is met:
                # 1. Enough time has passed, OR
                # 2. There are NULL values that need to be recalculated
                if time_check_passed:
                    logger.info(f"\n\nEnough time has passed ({current_date_time} - {date_created}) to update the baseline behavioral data for user {user_uid}.\n\n")
                if null_values_exist:
                    logger.info(f"\n\nFound NULL baseline values for user {user_uid} in category {metric_category_name}, recalculating...\n\n")

                sess_end_date = baseline_data[0]['sess_end_date']
                
                # Convert string to datetime if needed
                if isinstance(sess_end_date, str):
                    sess_end_date = datetime.fromisoformat(sess_end_date)
                
                current_date = datetime.now()

                # Create new baseline data
                if self._calc_and_store_baseline_metrics(user_uid, sess_end_date, current_date, metrics, statistical_metrics_list, metric_category_name) is False:
                    logger.error(f"Error calculating baseline metrics for user {user_uid} and metric category {metric_category_name}")
            return True
        except Exception as e:
            logger.error(f"Error handling existing baseline behavioral data for user {user_uid}: {e}")
            return False

    def _check_for_null_baseline_values(self, user_uid: str, metric_category_name: str, statistical_metrics_list: list) -> bool:
        """Check if any baseline values are NULL for the given metric category."""
        try:
            for metric in statistical_metrics_list:
                metric_name = metric[0]  # e.g., "SQS", "SCREEN_TIME", etc.
                
                # Get the latest baseline values for this metric
                baseline_data = self.supabase_service.get_user_baseline_metric_values(user_uid, metric_name)
                
                if not baseline_data:
                    logger.info(f"No baseline data found for user {user_uid} and metric {metric_name}")
                    return True  # No data counts as NULL
                
                # Check if any of the key baseline fields are NULL
                if (baseline_data.get('baseline_median') is None or 
                    baseline_data.get('baseline_mad') is None):
                    logger.info(f"Found NULL baseline values for user {user_uid}, metric {metric_name}")
                    return True
                    
            return False  # No NULL values found
        except Exception as e:
            logger.error(f"Error checking for NULL baseline values for user {user_uid}: {e}")
            return True  # Assume NULL values exist if we can't check

    def _handle_no_baseline_behavioral_data(self, user_uid: str, metrics: list) -> bool:

        MIN_SESSION_SPAN_DAYS = 14
        MIN_DAYS_SINCE_FIRST_SESSION = 15

        try:
            for metric_category in metrics:
                metric_category_name, main_table_name, statistical_metrics_list = metric_category

                # Get the first type of data for the user and the behavioral metric category
                # Note: All have the day_analyzed as an indicator of when they where created as data in the db
                first_data_response = self.supabase_service.client.table(main_table_name) \
                    .select('day_analyzed') \
                    .eq("user_uid", user_uid) \
                    .order('day_analyzed', desc=False) \
                    .limit(1) \
                    .execute()
                
                if not first_data_response.data:
                    logger.info(f"No {metric_category_name} data found for user {user_uid}")
                    return False
                
                first_date = first_data_response.data[0]['day_analyzed']
                if first_date is None:
                    logger.info(f"No valid {metric_category_name} date found for user {user_uid}")
                    return False
                
                if isinstance(first_date, str):
                    first_date = datetime.fromisoformat(first_date)
                
                # Get the last type of data for the user and the behavioral metric category
                last_data_response = self.supabase_service.client.table(main_table_name) \
                    .select('day_analyzed') \
                    .eq("user_uid", user_uid) \
                    .order('day_analyzed', desc=True) \
                    .limit(1) \
                    .execute()

                if not last_data_response.data:
                    logger.info(f"No {metric_category_name} data found for user {user_uid}")
                    return False
                
                last_date = last_data_response.data[0]['day_analyzed']
                if isinstance(last_date, str):
                    last_date = datetime.fromisoformat(last_date)
                
                # Check if enough time has passed between first and last date
                date_span_days = (last_date - first_date).days
                if date_span_days < MIN_SESSION_SPAN_DAYS:
                    logger.info(f"Not enough time between {metric_category_name} dates ({date_span_days} days) to create baseline for user {user_uid}.")
                    return False
                
                # Check if first date is old enough
                current_date = datetime.now()
                days_since_first = (current_date - first_date).days
                if days_since_first < MIN_DAYS_SINCE_FIRST_SESSION:
                    logger.info(f"First {metric_category_name} date too recent ({days_since_first} days ago) to create baseline for user {user_uid}.")
                    return False
                
                # Create new baseline data
                if not self._calc_and_store_baseline_metrics(user_uid, first_date, current_date, metrics,
                                                             statistical_metrics_list, metric_category_name):
                    logger.error(f"Error calculating baseline metrics for user {user_uid} and metric category {metric_category_name}")
            return True
        except Exception as e:
            logger.error(f"Error handling no baseline behavioral data for user {user_uid}: {e}")
            return False
    
    def _calc_and_store_baseline_metrics(self, user_uid: str, start_date: datetime, end_date: datetime, metrics: list, statistical_metrics_list: list, metric_category_name: str) -> bool:
        """
        Calculates baseline metrics (mean, std, median, mad) for a given data.
        Returns a list with one dict so _save_baseline_data can consume it.
        Args:
            user_uid: str - The user's unique identifier
            start_date: datetime - The start date of the time range
            end_date: datetime - The end date of the time range
            metrics: list - The list of metrics to calculate the baseline metrics for
            statistical_metrics_list: list - The list of statistical metrics to calculate the baseline metrics for
            metric_category_name: str - The name of the metric category
        """
        try:
            logger.info(f"\n\nCalculating and storing baseline metrics for user {user_uid} and metric category {metric_category_name}\n\n")

            if metric_category_name == "SLEEP_DATA":
                baseline_response = self._calc_sleep_baseline_metrics(user_uid, start_date, end_date, statistical_metrics_list)
                if baseline_response is None:
                    logger.error(f"Error calculating sleep baseline metrics for user {user_uid}")
                    return False
                self.supabase_service._save_baseline_data(user_uid, baseline_response, statistical_metrics_list, end_date, 'BEHAVIORAL_METRIC')
            elif metric_category_name == "DAILY_DEVICE_INTERACTION":
                baseline_response = self._calc_device_interaction_baseline_metrics(user_uid, start_date, end_date, statistical_metrics_list)
                if baseline_response is None:
                    logger.error(f"Error calculating device interaction baseline metrics for user {user_uid}")
                    return False
                self.supabase_service._save_baseline_data(user_uid, baseline_response, statistical_metrics_list, end_date, 'BEHAVIORAL_METRIC')
            elif metric_category_name == "ACTIVITY_BEHAVIOR":
                baseline_response = self._calc_activity_baseline_metrics(user_uid, start_date, end_date, statistical_metrics_list)
                if baseline_response is None:
                    logger.error(f"Error calculating activity baseline metrics for user {user_uid}")
                    return False
                self.supabase_service._save_baseline_data(user_uid, baseline_response, statistical_metrics_list, end_date, 'BEHAVIORAL_METRIC')
            elif metric_category_name == "CALL_BEHAVIOR":
                baseline_response = self._calc_call_baseline_metrics(user_uid, start_date, end_date, statistical_metrics_list)
                if baseline_response is None:
                    logger.error(f"Error calculating call baseline metrics for user {user_uid}")
                    return False
                self.supabase_service._save_baseline_data(user_uid, baseline_response, statistical_metrics_list, end_date, 'BEHAVIORAL_METRIC')
            elif metric_category_name == "GPS_DATA":
                baseline_response = self._calc_gps_baseline_metrics(user_uid, start_date, end_date, statistical_metrics_list)
                if baseline_response is None:
                    logger.error(f"Error calculating gps baseline metrics for user {user_uid}")
                    return False
                self.supabase_service._save_baseline_data(user_uid, baseline_response, statistical_metrics_list, end_date, 'BEHAVIORAL_METRIC')
            return True
        except Exception as e:
            logger.error(f"Error calculating baseline metrics for user {user_uid}: {e}")
            return False

    def _calc_sleep_baseline_metrics(self, user_uid: str, start_date: datetime, end_date: datetime, stat_metrics: list) -> list:
        """
        Calculates baseline metrics (mean, std, median, mad) for sleep-related data.
        Returns a list with one dict so _save_baseline_data can consume it.
        """
        try:
            sleep_data = self.supabase_service.client.table("Sleep_Data_Analysis") \
                .select("*") \
                .eq("user_uid", user_uid) \
                .gte("day_analyzed", start_date.isoformat()) \
                .lte("day_analyzed", end_date.isoformat()) \
                .execute()

            if sleep_data is None or len(sleep_data.data) == 0:
                logger.error(f"No sleep data found for user {user_uid} in range {start_date} - {end_date}")
                return None

            rows = sleep_data.data

            # First/last session boundaries
            first_session = min(row["day_analyzed"] for row in rows)
            last_session = max(row["day_analyzed"] for row in rows)

            baseline_row = {
                "first_session": first_session,
                "last_session": last_session
            }

            for metric in stat_metrics:
                (
                    metric_name,      # e.g. "SQS"
                    field_name,       # baseline mean key (e.g. "sqs", "sleep_start_time")
                    std_field_name,   # e.g. "std_sqs"
                    median_field_name,# e.g. "median_sqs"
                    mad_field_name    # e.g. "mad_sqs"
                ) = metric

                # Map baseline field names to actual DB column names for sleep data
                db_field_name = field_name
                if field_name == "sqs":
                    db_field_name = "sleep_quality_score"
                elif field_name == "sleep_start_time":
                    db_field_name = "estimated_start_date_time"
                elif field_name == "sleep_end_time":
                    db_field_name = "estimated_end_date_time"

                raw_values = [row.get(db_field_name) for row in rows if row.get(db_field_name) is not None]

                # Convert datetime-like strings to timestamps for numerical stats
                values = []
                if field_name in ("sleep_start_time", "sleep_end_time"):
                    for v in raw_values:
                        try:
                            # Expecting ISO string; convert to POSIX timestamp (seconds)
                            ts = pd.to_datetime(v).timestamp()
                            values.append(ts)
                        except Exception:
                            continue
                else:
                    values = raw_values

                if not values:
                    logger.warning(f"No values for {metric_name} in user {user_uid}")
                    baseline_row[metric_name.lower()] = 0.0
                    baseline_row[std_field_name] = 0.0
                    baseline_row[median_field_name] = 0.0
                    baseline_row[mad_field_name] = 0.0
                    continue

                arr = np.array(values, dtype=float)

                baseline_row[metric_name.lower()] = float(np.mean(arr))  # mean
                baseline_row[std_field_name] = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
                baseline_row[median_field_name] = float(np.median(arr))
                baseline_row[mad_field_name] = float(np.median(np.abs(arr - baseline_row[median_field_name])))

            logger.info(f"Sleep baseline metrics for user {user_uid}: {baseline_row}")
            return [baseline_row]
        except Exception as e:
            logger.error(f"Error calculating sleep baseline metrics for user {user_uid}: {e}")
            return None

    def _calc_device_interaction_baseline_metrics(self, user_uid: str, start_date: datetime, end_date: datetime, stat_metrics: list) -> list:
        try:
            device_interaction_data = self.supabase_service.client.table("Device_Interaction_Data_Analysis") \
                .select("*") \
                .eq("user_uid", user_uid) \
                .gte("day_analyzed", start_date.isoformat()) \
                .lte("day_analyzed", end_date.isoformat()) \
                .execute()

            if device_interaction_data is None or len(device_interaction_data.data) == 0:
                logger.error(f"No device interaction data found for user {user_uid} in range {start_date} - {end_date}")
                return None

            rows = device_interaction_data.data
            first_session = min(row["day_analyzed"] for row in rows)
            last_session = max(row["day_analyzed"] for row in rows)

            baseline_row = {
                "first_session": first_session,
                "last_session": last_session
            }

            for metric in stat_metrics:
                metric_name, field_name, std_key, median_key, mad_key = metric
                values = [row[field_name] for row in rows if row.get(field_name) is not None]

                if not values:
                    baseline_row[field_name] = 0.0
                    baseline_row[std_key] = 0.0
                    baseline_row[median_key] = 0.0
                    baseline_row[mad_key] = 0.0
                    continue

                arr = np.array(values, dtype=float)
                baseline_row[field_name] = float(np.mean(arr))
                baseline_row[std_key] = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
                baseline_row[median_key] = float(np.median(arr))
                baseline_row[mad_key] = float(np.median(np.abs(arr - baseline_row[median_key])))
            
            logger.info(f"\n\nDevice interaction baseline metrics for user {user_uid}: {baseline_row}\n\n")
            return [baseline_row]
        except Exception as e:
            logger.error(f"Error calculating device interaction baseline metrics for user {user_uid}: {e}")
            return None
    
    def _calc_activity_baseline_metrics(self, user_uid: str, start_date: datetime, end_date: datetime, stat_metrics: list) -> list:
        try:
            activity_data = self.supabase_service.client.table("Activity_Data_Analysis") \
                .select("*") \
                .eq("user_uid", user_uid) \
                .gte("day_analyzed", start_date.isoformat()) \
                .lte("day_analyzed", end_date.isoformat()) \
                .execute()

            if activity_data is None or len(activity_data.data) == 0:
                logger.error(f"No activity data found for user {user_uid} in range {start_date} - {end_date}")
                return None

            rows = activity_data.data
            first_session = min(row["day_analyzed"] for row in rows)
            last_session = max(row["day_analyzed"] for row in rows)

            baseline_row = {"first_session": first_session, "last_session": last_session}

            for metric in stat_metrics:
                metric_name, field_name, std_key, median_key, mad_key = metric
                values = [row[field_name] for row in rows if row.get(field_name) is not None]

                if not values:
                    baseline_row[field_name] = 0.0
                    baseline_row[std_key] = 0.0
                    baseline_row[median_key] = 0.0
                    baseline_row[mad_key] = 0.0
                    continue

                arr = np.array(values, dtype=float)
                baseline_row[field_name] = float(np.mean(arr))
                baseline_row[std_key] = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
                baseline_row[median_key] = float(np.median(arr))
                baseline_row[mad_key] = float(np.median(np.abs(arr - baseline_row[median_key])))

            logger.info(f"\n\nActivity baseline metrics for user {user_uid}: {baseline_row}\n\n")
            return [baseline_row]
        except Exception as e:
            logger.error(f"Error calculating activity baseline metrics for user {user_uid}: {e}")
            return None

    
    def _calc_call_baseline_metrics(self, user_uid: str, start_date: datetime, end_date: datetime, stat_metrics: list) -> list:
        try:
            call_data = self.supabase_service.client.table("Call_Data_Analysis") \
                .select("*") \
                .eq("user_uid", user_uid) \
                .gte("day_analyzed", start_date.isoformat()) \
                .lte("day_analyzed", end_date.isoformat()) \
                .execute()

            if call_data is None or len(call_data.data) == 0:
                logger.error(f"No call data found for user {user_uid} in range {start_date} - {end_date}")
                return None

            rows = call_data.data
            first_session = min(row["day_analyzed"] for row in rows)
            last_session = max(row["day_analyzed"] for row in rows)

            baseline_row = {"first_session": first_session, "last_session": last_session}

            for metric in stat_metrics:
                metric_name, field_name, std_key, median_key, mad_key = metric
                values = [row[field_name] for row in rows if row.get(field_name) is not None]

                if not values:
                    baseline_row[field_name] = 0.0
                    baseline_row[std_key] = 0.0
                    baseline_row[median_key] = 0.0
                    baseline_row[mad_key] = 0.0
                    continue

                arr = np.array(values, dtype=float)
                baseline_row[field_name] = float(np.mean(arr))
                baseline_row[std_key] = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
                baseline_row[median_key] = float(np.median(arr))
                baseline_row[mad_key] = float(np.median(np.abs(arr - baseline_row[median_key])))

            logger.info(f"\n\nCall baseline metrics for user {user_uid}: {baseline_row}\n\n")
            return [baseline_row]
        except Exception as e:
            logger.error(f"Error calculating call baseline metrics for user {user_uid}: {e}")
            return None
    
    def _calc_gps_baseline_metrics(self, user_uid: str, start_date: datetime, end_date: datetime, stat_metrics: list) -> list:
        try:
            gps_data = self.supabase_service.client.table("GPS_Data_Analysis") \
                .select("*") \
                .eq("user_uid", user_uid) \
                .gte("day_analyzed", start_date.isoformat()) \
                .lte("day_analyzed", end_date.isoformat()) \
                .execute()

            if gps_data is None or len(gps_data.data) == 0:
                logger.error(f"No GPS data found for user {user_uid} in range {start_date} - {end_date}")
                return None
            
            # Get spatial features for the GPS data records
            # GPS_Spatial_Features table has gps_data_analysis_id that references GPS_Data_Analysis.id
            gps_spatial_features = self.supabase_service.client.table("GPS_Spatial_Features") \
                .select("gps_data_analysis_id, convex_hull_area_m2, sde_area_m2, max_distance_timestamp") \
                .in_("gps_data_analysis_id", [row["id"] for row in gps_data.data]) \
                .execute()
            
            # Create a lookup dictionary for spatial features
            spatial_features_lookup = {}
            if gps_spatial_features and gps_spatial_features.data:
                for feature in gps_spatial_features.data:
                    spatial_features_lookup[feature["gps_data_analysis_id"]] = feature
            
            # Add spatial metrics to GPS data rows
            for row in gps_data.data:
                gps_id = row["id"]
                spatial_feature = spatial_features_lookup.get(gps_id, {})
                row["convex_hull_area_m2"] = spatial_feature.get("convex_hull_area_m2", 0.0)
                row["sde_area_m2"] = spatial_feature.get("sde_area_m2", 0.0)
                row["max_distance_timestamp"] = spatial_feature.get("max_distance_timestamp", None)

            rows = gps_data.data
            first_session = min(row["day_analyzed"] for row in rows)
            last_session = max(row["day_analyzed"] for row in rows)

            baseline_row = {"first_session": first_session, "last_session": last_session}

            for metric in stat_metrics:
                metric_name, field_name, std_key, median_key, mad_key = metric
                raw_values = [row.get(field_name) for row in rows if row.get(field_name) is not None]

                # Convert datetime-like strings to timestamps for numerical stats
                values = []
                if field_name == "max_distance_timestamp":
                    def _to_minutes_since_midnight(dt):
                        """Convert datetime to minutes since midnight for daily pattern analysis"""
                        if isinstance(dt, str):
                            dt = pd.to_datetime(dt)
                        elif not isinstance(dt, datetime):
                            # Handle timestamp case
                            dt = pd.to_datetime(dt, unit='s')
                        return dt.hour * 60 + dt.minute
                    
                    for v in raw_values:
                        try:
                            # Convert to minutes since midnight for consistent daily pattern analysis
                            minutes = _to_minutes_since_midnight(v)
                            values.append(minutes)
                        except Exception:
                            continue
                else:
                    values = raw_values

                if not values:
                    baseline_row[field_name] = 0.0
                    baseline_row[std_key] = 0.0
                    baseline_row[median_key] = 0.0
                    baseline_row[mad_key] = 0.0
                    continue

                arr = np.array(values, dtype=float)
                baseline_row[field_name] = float(np.mean(arr))
                baseline_row[std_key] = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
                baseline_row[median_key] = float(np.median(arr))
                baseline_row[mad_key] = float(np.median(np.abs(arr - baseline_row[median_key])))

            logger.info(f"\n\nGPS baseline metrics for user {user_uid}: {baseline_row}\n\n")
            return [baseline_row]
        except Exception as e:
            logger.error(f"Error calculating gps baseline metrics for user {user_uid}: {e}")
            return None
    
    def _update_typing_baseline_metrics(self, user_uid: str):
        logger.info(f"Updating baseline metrics for user {user_uid}")

        metrics = [
            ("COGNITIVE_PROCESSING_EFFICIENCY", "avg_cpe", "std_cpe", "median_cpe", "mad_cpe"),
            ("NET_PRODUCTION_RATE", "avg_npr", "std_npr", "median_npr", "mad_npr"),
            ("COGNITIVE_PROCESSING_INDEX", "avg_cpi", "std_cpi", "median_cpi", "mad_cpi"),
            ("CORRECTION_EFFICIENCY", "avg_ce", "std_ce", "median_ce", "mad_ce"),
            ("EFFORT_TO_OUTPUT_RATIO", "avg_eto", "std_eto", "median_eto", "mad_eto"),
            ("PAUSE_TO_PRODUCTION_RATIO", "avg_ppr", "std_ppr", "median_ppr", "mad_ppr"),
            ("PRESSURE_INTENSITY", "avg_pi", "std_pi", "median_pi", "mad_pi"),
            ("TYPING_RHYTHM_STABILITY", "avg_trs", "std_trs", "median_trs", "mad_trs"),
        ]

        try:
            select_query = "date_created, sess_end_date, Users(user_uid)"
            baseline_metrics_existed = self.supabase_service.client.table('Baseline_Metrics') \
                .select(select_query) \
                .eq("user_uid", user_uid) \
                .eq("data_category", "TYPING_METRIC") \
                .order('date_created', desc=True) \
                .limit(1) \
                .execute()

            if not baseline_metrics_existed.data:
                logger.warning(f"No baseline metrics found for user {user_uid}")
                if not self._handle_no_baseline_typing_data(user_uid, metrics):
                    return False
            else:
                logger.warning(f"Baseline data already exists for user {user_uid}")
                if not self._handle_existing_baseline_typing_data(user_uid, baseline_metrics_existed.data, metrics):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error updating baseline metrics for user {user_uid}: {e}")
            return False

    def _handle_no_baseline_typing_data(self, user_uid: str, metrics: list) -> bool:
    
        MIN_SESSION_SPAN_DAYS = 14
        MIN_DAYS_SINCE_FIRST_SESSION = 15
        
        try:
            # Get the first typing session date for the user
            first_session_response = self.supabase_service.client.table("Typing_Sessions") \
                .select('session_date') \
                .eq("user_uid", user_uid) \
                .limit(1) \
                .order("session_date", desc=False) \
                .execute()
            
            if not first_session_response.data:
                logger.info(f"No typing sessions found for user {user_uid}.")
                return False
            
            first_date = first_session_response.data[0]["session_date"]
            if first_date is None:
                logger.info(f"No valid session date found for user {user_uid}.")
                return False
            
            # Convert string to datetime if needed
            if isinstance(first_date, str):
                first_date = datetime.fromisoformat(first_date)

            # Get the last typing session date
            last_session_response = self.supabase_service.client.table("Typing_Sessions") \
                .select('session_date') \
                .eq("user_uid", user_uid) \
                .limit(1) \
                .order("session_date", desc=True) \
                .execute()

            if not last_session_response.data:
                logger.info(f"No last session found for user {user_uid}.")
                return False

            last_date = last_session_response.data[0]["session_date"]
            if isinstance(last_date, str):
                last_date = datetime.fromisoformat(last_date)

            # Check if enough time has passed between first and last session
            session_span_days = (last_date - first_date).days
            if session_span_days < MIN_SESSION_SPAN_DAYS:
                logger.info(f"Not enough time between sessions ({session_span_days} days) to create baseline for user {user_uid}.")
                return False

            # Check if first session is old enough
            current_date = datetime.now()
            days_since_first = (current_date - first_date).days
            if days_since_first < MIN_DAYS_SINCE_FIRST_SESSION:
                logger.info(f"First session too recent ({days_since_first} days ago) to create baseline for user {user_uid}.")
                return False

            # Create new baseline data
            logger.info(f"Creating new baseline data for user {user_uid}...")
            # baseline_response = self.supabase_service.client.rpc('get_baseline_metrics', {
            #     "input_user_uid_param": user_uid,
            #     "start_date_param": first_date.isoformat(),
            #     "end_date_param": current_date.isoformat()
            # }).execute()
            baseline_response = self.supabase_service._get_baseline_metrics_rpc_function(user_uid, first_date, current_date)

            if baseline_response is None:
                logger.error(f"Failed to get baseline metrics for user {user_uid}")
                return False

            self.supabase_service._save_baseline_data(user_uid, baseline_response, metrics, current_date, 'TYPING_METRIC')
            return True
        except Exception as e:
            logger.error(f"Error handling no baseline data for user {user_uid}: {e}")
            return False

    def _handle_existing_baseline_typing_data(self, user_uid: str, baseline_data: list, metrics: list) -> bool:
        """Handle case when baseline typing data already exists for a user."""
        
        MIN_DAYS_SINCE_LAST_SESSION = 15

        try:
            # Check if the last updated date is older than 30 days
            date_created = baseline_data[0]['date_created']

            if isinstance(date_created, str):
                date_created = datetime.fromisoformat(date_created)
            
            current_date_time = datetime.now()
            if (current_date_time - date_created).days < MIN_DAYS_SINCE_LAST_SESSION:
                print(f"\033[91mNot enough time has passed ({current_date_time} - {date_created}) to update the baseline typing data for user, baseline data are still valid for user {user_uid}.\033[0m")
                # This is not an error, just means that the baseline data are still valid
                return True
            
            # Else, update the baseline data
            logger.info(f"Enough time has passed ({current_date_time} - {date_created}) to update the baseline data for user {user_uid}.")

            sess_end_date = baseline_data[0]['sess_end_date']
            # response_new = self.supabase_service.client.rpc('get_baseline_metrics', {
            #     "input_user_uid": user_uid,
            #     "start_date": sess_end_date,
            #     "end_date": current_date_time.isoformat()
            # }).execute()
            response_new = self.supabase_service._get_baseline_metrics_rpc_function(user_uid, sess_end_date, current_date_time)

            if response_new is None:
                logger.error(f"Failed to get baseline metrics for user {user_uid}")
                return False

            self.supabase_service._save_baseline_data(user_uid, response_new, metrics, current_date_time, 'TYPING_METRIC')

            return True
        except Exception as e:
            logger.error(f"Error handling existing baseline data for user {user_uid}: {e}")
            return False

    def _calculate_typing_score_and_decision(self, user_uid: str, analysis_start_datetime: datetime, analysis_end_datetime: datetime):
        logger.info(f"Updating the cognitive score and final decision for user {user_uid}")

        # Bad Direction definition for metrics
        metrics_direction = {
            'Cognitive_Processing_Efficiency_Data': 'low',
            'Cognitive_Processing_Index_Data': 'high',
            'Correction_Efficiency_Data': 'low',
            'Effort_To_Output_Ratio_Data': 'high',
            'Net_Production_Rate_Data': 'low',
            'Pause_To_Production_Ratio_Data': 'high',
            'Pressure_Intensity_Data': 'high',
            'Typing_Rhythm_Stability_Data': 'low'
        }

        weights = {metric: 1 / len(metrics_direction) for metric in metrics_direction}

        try:
            results = self.db_service.get_typing_sessions_of_a_user(user_uid, analysis_start_datetime, analysis_end_datetime)
            
            if len(results) == 0:
                logger.info(f"No typing sessions found for user {user_uid}.")
                return False
            
            session_ids = [record.typing_session_id for record in results]

            # Calculate the cognitive score for each session
            for session_id in session_ids:
                score = 0
                
                # For the session get all the z-scores calculated for each metric from Supabase
                z_scores = self.supabase_service.get_z_scores_of_a_typing_session(session_id)
                if z_scores is None:
                    logger.error(f"No z-scores found for session {session_id}.")
                    return False

                for metric, z_score in z_scores.items():
                    if pd.isna(z_score):
                        continue
                    # Normalize based on bad direction
                    normalized_score = z_score if metrics_direction[metric] == 'low' else -z_score
                    score += weights[metric] * normalized_score

                logger.info(f"Cognitive score for session {session_id} is {score:.4f}")
                decision = self._classify_decision(score)

                # Update the score and decision in the Supabase
                status = self.supabase_service.update_scores_and_decisions_of_a_typing_session(session_id, score, decision)

                if status is not True:
                    logger.error(f"Failed to update the cognitive score and final decision for session {session_id}.")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error updating the cognitive score and final decision for user {user_uid}: {e}")
            return False

    def _classify_decision(self, score: float):
        if score > 0.965:
            return "Excellent"
        if score > 0.586:
            return "Very Good"
        if score < -0.952:
            return "Critical"
        if score < -0.575:
            return "Very Bad"
        return "Normal"

    def _calculate_behavioral_score_and_decision(self, user_uid: str, day_analyzed: datetime):
        logger.info(f"Updating the behavioral score and final decision for user {user_uid}")

        # Bad Direction definition for metrics
        # Note some metrics will not be include in the score and decision calculation
        # (sleep start and end time, average_time_spend_in_locations and avg_call_duration)
        metrics = [
            ("SLEEP_DATA", (("sqs", "low"),)),
            ("DAILY_DEVICE_INTERACTION", (("screen_time", "high"), ("low_light_day_time", "high"), ("device_drop_events", "high"))),
            ("ACTIVITY_BEHAVIOR", (("daily_active_minutes", "low"),)),
            ("CALL_METRICS", (("missed_call_ratio", "high"), ("total_calls_in_a_day", "low"))),
            ("GPS_METRICS", (("total_time_spend_in_home_seconds", "high"), ("total_time_spend_travelling_seconds", "low"), ("total_time_spend_out_of_home_seconds", "low"), ("total_distance_traveled_km", "low"), ("number_of_unique_locations", "low"), ("convex_hull_area_m2", "low"), ("sde_area_m2", "low")))
        ]

        # Here for each metric category, we will take the info about the z-scores for each category from Supabase.
        # Then we will calculate the score and decision for each metric in the category.
        # Note if a metric is alone then the weights will be adapted accordingly.

        try:
            for metric_category in metrics: # for each metric category
                logger.info(f"Processing metric category: {metric_category}")
                metric_category_name, metrics_list = metric_category # ex. (SLEEP_DATA, ({"sqs", "low"})

                # extract from metrics_list the names of the metrics
                metrics_names = [metric[0] for metric in metrics_list] # ex. ["sqs", "screen_time"]

                # Find the weigh based on the number of metrics in the category (equal weights for all metric in each category)
                weight = 1 / len(metrics_list)

                z_scores_info = {} # dictionary to store the z-scores info for the metrics in the category
                if metric_category_name == "SLEEP_DATA":
                    main_table_id_name = "sleep_data_analysis_id" # the name of the id field that references the main table
                    z_scores_info = self.supabase_service.get_z_scores_info_for_sleep_data(user_uid, day_analyzed, metrics_names) # ex. [{"id": 1, "sleep_data_analysis_id": 1, "sqs_z_score": 0.5}]
                    if z_scores_info is None:
                        logger.error(f"No z-scores info found for metric category {metric_category_name} for user {user_uid}")
                        continue # continue to the next metric category
                elif metric_category_name == "DAILY_DEVICE_INTERACTION":
                    main_table_id_name = "device_interaction_data_analysis_id" # the name of the id field that references the main table
                    z_scores_info = self.supabase_service.get_z_scores_info_for_device_interaction_data(user_uid, day_analyzed, metrics_names) # ex. [{"id": 1, "device_interaction_data_analysis_id": 1, "screen_time_z_score": 0.5 ...}]
                    if z_scores_info is None:
                        logger.error(f"No z-scores info found for metric category {metric_category_name} for user {user_uid}")
                        continue # continue to the next metric category
                elif metric_category_name == "ACTIVITY_BEHAVIOR":
                    main_table_id_name = "activity_data_analysis_id" # the name of the id field that references the main table
                    z_scores_info = self.supabase_service.get_z_scores_info_for_activity_data(user_uid, day_analyzed, metrics_names) # ex. [{"id": 1, "activity_data_analysis_id": 1, "daily_active_minutes_z_score": 0.5}]
                    if z_scores_info is None:
                        logger.error(f"No z-scores info found for metric category {metric_category_name} for user {user_uid}")
                        continue # continue to the next metric category
                elif metric_category_name == "CALL_METRICS":
                    main_table_id_name = "call_data_analysis_id" # the name of the id field that references the main table
                    z_scores_info = self.supabase_service.get_z_scores_info_for_call_data(user_uid, day_analyzed, metrics_names) # ex. [{"id": 1, "call_data_analysis_id": 1, "missed_call_ratio_z_score": 0.5 ...}]
                    if z_scores_info is None:
                        logger.error(f"No z-scores info found for metric category {metric_category_name} for user {user_uid}")
                        continue # continue to the next metric category
                elif metric_category_name == "GPS_METRICS":
                    main_table_id_name = "gps_data_analysis_id" # the name of the id field that references the main table
                    z_scores_info = self.supabase_service.get_z_scores_info_for_gps_data(user_uid, day_analyzed, metrics_names)
                    if z_scores_info is None:
                        logger.error(f"No z-scores info found for metric category {metric_category_name} for user {user_uid}")
                        continue # continue to the next metric category
                else:
                    logger.error(f"Invalid metric name: {metric_category_name}")
                    return False

                score = 0
                z_score_values = {}  # Dictionary to store extracted z-score values
                
                for metric in metrics_list: # for each metric in each category (ex. sqs, screen_time etc.)
                    metric_name, metric_direction = metric # ex. (sqs, low)
                    logger.info(f"Processing metric: {metric_name}")
                    if not z_scores_info or f"{metric_name}_z_score" not in z_scores_info[0]:
                        logger.error(f"Missing z-score for metric {metric_name} in category {metric_category_name}")
                        continue

                    z_score_values[metric_name] = z_scores_info[0][f"{metric_name}_z_score"] # ex. 0.5

                    # Calculate the score for the metric
                    if pd.isna(z_score_values[metric_name]):
                        logger.warning(f"Z-score for {metric_name} is NaN, skipping")
                        continue
                    
                    # Normalize based on bad direction
                    normalized_score = z_score_values[metric_name] if metric_direction == 'low' else -z_score_values[metric_name]
                    score += weight * normalized_score
                    logger.debug(f"Metric {metric_name}: z_score={z_score_values[metric_name]}, direction={metric_direction}, normalized={normalized_score}, weight={weight}")

                logger.info(f"Score for metric category {metric_category_name} is {score:.4f}")
                decision = self._classify_decision(score)
                logger.info(f"Decision for metric category {metric_category_name} is {decision}")

                # Update the score and decision in the Supabase
                if not z_scores_info or len(z_scores_info) == 0:
                    logger.error(f"No valid z_scores_info available for updating score and decision for category {metric_category_name}")
                    continue

                if main_table_id_name is None:
                    logger.error(f"No main table id name found for metric category {metric_category_name}")
                    continue
                
                main_data_analysis_id = z_scores_info[0][main_table_id_name]
                logger.info(f"Updating behavioral score for category {metric_category_name} with ID {main_data_analysis_id}, score: {score:.4f}, decision: {decision}")
                
                status = self.supabase_service.update_scores_and_decisions_of_a_behavioral_data_analysis(main_data_analysis_id, metric_category_name, score, decision)
                if status is not True:
                    logger.error(f"Failed to update the score and decision for metric category {metric_category_name} for user {user_uid}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error updating the behavioral score and final decision for user {user_uid}: {e}")
            return False

    def _compute_and_store_pressure_intensity(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the pressure intensity for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing pressure intensity for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")

                total_pressure = typing_session.total_pressure_by_times_counter
                characters_typed = typing_session.characters_typed

                if characters_typed and characters_typed > 0:
                    pressure_intensity = total_pressure / characters_typed

                    if baseline_values_for_metric is not None:
                        z_score = self._calc_modified_z_score(
                            pressure_intensity,
                            baseline_values_for_metric.get('baseline_median'),
                            baseline_values_for_metric.get('baseline_mad')
                        )
                    else: 
                        z_score = 0

                    payload =  { # Return the payload
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': pressure_intensity,
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }

                    # Store the result in Supabase
                    result = self.supabase_service.send_data(
                        "Pressure_Intensity_Data",
                        "session_uid",
                        typing_session.typing_session_id,
                        payload
                    )

                    if result:
                        logger.info(f"Pressure intensity for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(f"Failed to store pressure intensity for session {typing_session.typing_session_id}.")

                else:
                    logger.info(f"No characters typed in session {typing_session.typing_session_id} for user {user_uid}. Skipping pressure intensity computation.")
        except Exception as e:
            logger.error(f"Error computing pressure intensity for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    def _compute_and_store_effort_to_output_ratio(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the effort to output ratio for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing Effort to Output Ratio for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")

                total_pressure = typing_session.total_pressure_by_times_counter
                characters_typed = typing_session.characters_typed
                characters_deleted = typing_session.total_characters_deleted

                if characters_typed and characters_typed > 0 and characters_deleted and characters_deleted > 0:
                    effort_to_output_ratio = total_pressure / (characters_typed - characters_deleted)
                    
                    if baseline_values_for_metric is not None:
                        z_score = self._calc_modified_z_score(
                            effort_to_output_ratio,
                            baseline_values_for_metric.get('baseline_median'),
                            baseline_values_for_metric.get('baseline_mad')
                        )
                    else:
                        z_score = 0

                    payload =  {
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': effort_to_output_ratio,
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }

                    result = self.supabase_service.send_data(
                        "Effort_To_Output_Ratio_Data",
                        'session_uid',
                        typing_session.typing_session_id,
                        payload
                    )

                    if result:
                        logger.info(f"Effort to Output Ratio for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(f"Failed to store Effort to Output Ratio for session {typing_session.typing_session_id}.")

                else:
                    logger.info(f"Insufficient data in session {typing_session.typing_session_id} for user {user_uid}. Skipping Effort to Output Ratio computation.")
            return None
        except Exception as e:
            logger.error(f"Error computing Effort to Output Ratio for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    def _compute_and_store_typing_rhythm_stability(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the typing rhythm stability for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing Typing Rhythm Stability for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")

                mean_iki = typing_session.mean_iki
                std_dev_iki = typing_session.std_dev_iki

                if mean_iki and std_dev_iki and (mean_iki + std_dev_iki) > 0:
                    trs = mean_iki / (mean_iki + std_dev_iki)

                    if baseline_values_for_metric is not None:
                        z_score = self._calc_modified_z_score(trs, baseline_values_for_metric.get('baseline_median'), baseline_values_for_metric.get('baseline_mad'))
                    else:
                        z_score = 0

                    payload = {
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': trs,
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }

                    result = self.supabase_service.send_data(
                        "Typing_Rhythm_Stability_Data",
                        'session_uid',
                        typing_session.typing_session_id,
                        payload
                    )

                    if result:
                        logger.info(f"Typing Rhythm Stability for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(f"Failed to store Typing Rhythm Stability for session {typing_session.typing_session_id}.")
                else:
                    logger.info(f"Insufficient data in session {typing_session.typing_session_id} for user {user_uid}. Skipping Typing Rhythm Stability computation.")
        except Exception as e:
            logger.error(f"Error computing Typing Rhythm Stability for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    def _compute_and_store_cognitive_processing_index(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the cognitive processing index for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing Cognitive Processing Index for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")
                max_pause_wtw = typing_session.max_pause_wtw_duration
                avg_pause_wtw = typing_session.avg_pause_wtw_duration
                max_pause_ctc = typing_session.max_pause_ctc_duration
                avg_pause_ctc = typing_session.avg_pause_ctc_duration

                if max_pause_wtw and avg_pause_wtw and max_pause_ctc and avg_pause_ctc:
                    cpi = log(1 + (max_pause_wtw / avg_pause_wtw)) + log(1 + (max_pause_ctc / avg_pause_ctc))

                    if baseline_values_for_metric is not None:
                        z_score = self._calc_modified_z_score(cpi.real, baseline_values_for_metric.get('baseline_median'),
                                                          baseline_values_for_metric.get('baseline_mad'))
                    else:
                        z_score = 0

                    payload = {
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': cpi.real,  # keep the real part
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }

                    result = self.supabase_service.send_data(
                        "Cognitive_Processing_Index_Data",
                        'session_uid',
                        typing_session.typing_session_id,
                        payload
                    )

                    if result:
                        logger.info(
                            f"Cognitive Processing Index for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(
                            f"Failed to store Cognitive Processing Index for session {typing_session.typing_session_id}.")
                else:
                    logger.info(f"Insufficient data in session {typing_session.typing_session_id} for user {user_uid}. Skipping Cognitive Processing Index computation.")
        except Exception as e:
            logger.error(f"Error computing Cognitive Processing Index for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    def _compute_and_store_pause_to_production_ratio(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the pause to production ratio for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing Pause to Production Ratio for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")

                iki_list_size = typing_session.iki_list_size
                avg_iki = typing_session.mean_iki
                session_duration = typing_session.duration

                if iki_list_size and avg_iki and session_duration and session_duration > 0:
                    ppr = iki_list_size * avg_iki / session_duration

                    if baseline_values_for_metric is not None:
                        z_score = self._calc_modified_z_score(ppr, baseline_values_for_metric.get('baseline_median'), baseline_values_for_metric.get("baseline_mad"))
                    else:
                        z_score = 0

                    payload = {
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': ppr,
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }

                    result = self.supabase_service.send_data(
                        "Pause_To_Production_Ratio_Data",
                        "session_uid",
                        typing_session.typing_session_id,
                        payload
                    )

                    if result:
                        logger.info(f"Pause to Production Ratio for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(f"Failed to store Pause to Production Ratio for session {typing_session.typing_session_id}.")
                else:
                    logger.info(f"Insufficient data in session {typing_session.typing_session_id}. Skipping Pause to Production Ratio computation.")
        except Exception as e:
            logger.error(f"Error computing Pause to Production Ratio for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    def _compute_and_store_correction_efficiency(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the correction efficiency for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing Correction Efficiency for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")

                total_chars_deleted = typing_session.total_characters_deleted
                total_chars_typed = typing_session.characters_typed

                if total_chars_typed and total_chars_typed > 0 and total_chars_deleted:
                    ce = 1 - (total_chars_deleted / total_chars_typed)

                    if baseline_values_for_metric is not None:
                        z_score = self._calc_modified_z_score(ce, baseline_values_for_metric.get('baseline_median'), baseline_values_for_metric.get('baseline_mad'))
                    else:
                        z_score = 0

                    payload = {
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': ce,
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }

                    result = self.supabase_service.send_data(
                        "Correction_Efficiency_Data",
                        "session_uid",
                        typing_session.typing_session_id,
                        payload
                    )

                    if result:
                        logger.info(f"Correction Efficiency for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(f"Failed to store Correction Efficiency for session {typing_session.typing_session_id}.")
                else:
                    logger.info(f"Insufficient data in session {typing_session.typing_session_id}. Skipping Correction Efficiency computation.")
        except Exception as e:
            logger.error(f"Error computing Correction Efficiency for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    def _compute_and_store_cognitive_processing_efficiency(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the cognitive processing efficiency for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing Cognitive Processing Efficiency for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")

                words_typed = typing_session.words_typed
                session_duration = typing_session.duration
                std_dev_iki = typing_session.std_dev_iki

                if session_duration and session_duration > 0 and words_typed and words_typed > 0:
                    cpe = words_typed / (session_duration * (1 + std_dev_iki))
                
                    if baseline_values_for_metric is None:
                        logger.warning(f"\033[93mNo baseline data found for user {user_uid} about the metric COGNITIVE_PROCESSING_EFFICIENCY.\033[0m")
                        z_score = 0
                    else:
                        # Calculate the modified z-score
                        z_score = self._calc_modified_z_score(cpe, baseline_values_for_metric.get('baseline_median'), baseline_values_for_metric.get('baseline_mad'))
                    
                    # Send to Supabase
                    payload = {
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': cpe,
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }
                    result = self.supabase_service.send_data(
                        "Cognitive_Processing_Efficiency_Data",
                        'session_uid',
                        typing_session.typing_session_id,
                        payload
                    )
                    if result:
                        logger.info(f"Cognitive Processing Efficiency for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(f"Failed to store Cognitive Processing Efficiency for session {typing_session.typing_session_id}.")
                else:
                    logger.info(f"Insufficient data in session {typing_session.typing_session_id} for user {user_uid}. Skipping Cognitive Processing Efficiency computation.")
        except Exception as e:
            logger.error(f"Error computing Cognitive Processing Efficiency for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    def _compute_and_store_net_production_rate(self, user_uid: str, typing_sessions, baseline_values_for_metric):
        """
        This function computes the net production rate for a user.
        Args:
            user_uid: str - The user's unique identifier
            typing_sessions: list - A list of typing sessions
            baseline_values_for_metric: dict - A dictionary containing the baseline values for the metric
        Returns:
            dict - A dictionary containing the status and error message
        """
        logger.info(f"Computing Net Production Rate for user {user_uid}")

        try:
            for typing_session in typing_sessions:
                logger.info(f"Processing session {typing_session.typing_session_id} for user {user_uid}")

                characters_typed = typing_session.characters_typed
                characters_deleted = typing_session.total_characters_deleted
                session_duration = typing_session.duration

                if session_duration and session_duration > 0 and characters_deleted <= characters_typed:
                    npr = (characters_typed - characters_deleted) / session_duration

                    if baseline_values_for_metric is not None:
                        z_score = self._calc_modified_z_score(npr, baseline_values_for_metric.get('baseline_median'), baseline_values_for_metric.get('baseline_mad'))
                    else:
                        z_score = 0

                    payload = {
                        'session_uid': typing_session.typing_session_id,
                        'analysis_date': datetime.now().isoformat(),
                        'value': npr,
                        'modified_z_score': z_score,
                        'included_baseline_metric': baseline_values_for_metric.get('id') if baseline_values_for_metric is not None else None
                    }

                    result = self.supabase_service.send_data(
                        "Net_Production_Rate_Data",
                        "session_uid",
                        typing_session.typing_session_id,   
                        payload
                    )

                    if result:
                        logger.info(f"Net Production Rate for session {typing_session.typing_session_id} stored successfully.")
                    else:
                        logger.error(f"Failed to store Net Production Rate for session {typing_session.typing_session_id}.")
                else:
                    logger.info(f"Insufficient data in session {typing_session.typing_session_id}. Skipping Net Production Rate computation.")
        except Exception as e:
            logger.error(f"Error computing Net Production Rate for user {user_uid}: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _calc_modified_z_score(value: float, median: float, mad: float) -> float:
        try:
            # Validate input parameters
            if value is None:
                logger.warning("Z-score calculation: value is None, returning 0.0")
                return 0.0
            if median is None:
                logger.warning("Z-score calculation: median is None, returning 0.0")
                return 0.0
            if mad is None:
                logger.warning("Z-score calculation: mad is None, returning 0.0")
                return 0.0
            
            # Convert to float to ensure proper type
            value = float(value)
            median = float(median)
            mad = float(mad)
            
            if mad == 0:
                mad = 1e-10
            # Modified z-score: (x - median) / (MAD * 1.4826)
            z_score = (value - median) / (mad * 1.4826)
            return z_score
        except Exception as e:
            logger.error(f"Error calculating modified z-score: {e}")
            logger.error(f"Input values: value={value} (type: {type(value)}), median={median} (type: {type(median)}), mad={mad} (type: {type(mad)})")
            return 0.0
    
    def _calc_device_interaction_data(self, user_uid: str, analysis_start_datetime: datetime, analysis_end_datetime: datetime) -> dict | None:
        """
        This function calculates the device interaction data.
        Args:
            None
        Returns:
            Dictionary with the device interaction data
        """
        try:
            screen_time_analysis_result = self._calc_screen_time_stat(user_uid, analysis_start_datetime, analysis_end_datetime) # [total_screen_on_time_sec, hybrid_intervals]
            
            # Check if screen_time_analysis_result is None before accessing its elements
            if screen_time_analysis_result is None:
                logger.info("No screen time data available for device interaction analysis")
                return {
                    "screen_time_analysis_result": 0,
                    "screen_time_circadian_hours_result": None,
                    "low_light_day_time_result": self._calc_low_light_day_time(user_uid, analysis_start_datetime, analysis_end_datetime),
                    "device_drop_events_result": self._calc_device_drop_events(user_uid, analysis_start_datetime, analysis_end_datetime),
                    "app_usage_result": self._calc_app_usage(user_uid, analysis_start_datetime, analysis_end_datetime)
                }
            
            screen_time_circadian_hours_result = self._calc_screen_time_in_circadian_hours(screen_time_analysis_result[1], screen_time_analysis_result[0])
            low_light_day_time_result = self._calc_low_light_day_time(user_uid, analysis_start_datetime, analysis_end_datetime)
            device_drop_events_result = self._calc_device_drop_events(user_uid, analysis_start_datetime, analysis_end_datetime)
            app_usage_result = self._calc_app_usage(user_uid, analysis_start_datetime, analysis_end_datetime)

            extract_user_device_interaction_insights = {
                "screen_time_analysis_result": screen_time_analysis_result[0], # total screen on time in seconds
                "screen_time_circadian_hours_result": screen_time_circadian_hours_result,
                "low_light_day_time_result": low_light_day_time_result,
                "device_drop_events_result": device_drop_events_result,
                "app_usage_result": app_usage_result
            }

            return extract_user_device_interaction_insights
        except Exception as e:
            logger.error(f"Error calculating device interaction data: {e}")
            return None

    def _calc_sleep_data(self, user_uid: str, analysis_start_datetime: datetime, analysis_end_datetime: datetime) -> dict | None:
        logger.info(f"Computing sleep data for user {user_uid}")

        try:
            analysis_end_datetime = (analysis_end_datetime + timedelta(days=1)).replace(hour=17, minute=59, second=59, microsecond=999999)
            
            # Fetch the sleep data for the user in the given time range
            sleep_events_df = self.db_service.get_sleep_data_of_a_user(user_uid, analysis_start_datetime, analysis_end_datetime)

            if sleep_events_df is None:
                logger.info(f"No sleep events found for user {user_uid} in the given time range.")
                return None
            
            sleep_events_df.sort_values(by='timestamp_now', inplace=True)

            sleep_windows = []
            in_sleep = False
            sleep_start = None

            # Iterate through rows of sleep events to detect sleep windows
            for i, row in sleep_events_df.iterrows():
                confidence = row["confidence"]
                motion = row["motion"]
                start_time = row["timestamp_previous"]
                end_time = row["timestamp_previous"]

                if not in_sleep and confidence >= 75 and motion <= 2:
                    sleep_start = start_time
                    in_sleep = True
                elif in_sleep and confidence <= 75:
                    sleep_end = end_time
                    duration = (sleep_end - sleep_start).total_seconds() / 60.0  # in minutes
                    if duration >= 25:
                        sleep_windows.append({"start": sleep_start, "end": sleep_end, "duration": duration})
                    # Reset state
                    in_sleep = False
                    sleep_start = None
            
            if not sleep_windows:
                logger.info(f"No sleep windows found for user {user_uid} in the given time range.")
                return None
            
            merged_windows = self._merge_sleep_windows(sleep_windows)
            if merged_windows:
                # Filter sleep windows that belong to the analysis day
                analysis_day = analysis_start_datetime.date()
                filtered_windows = []
                for window in merged_windows:
                    if self._assign_sleep_to_day(window["start"], window["end"], analysis_day):
                        filtered_windows.append(window)
                    else:
                        logger.info(f"Excluding sleep window from analysis day {analysis_day}: {window['start']} -> {window['end']}")
                
                merged_windows = filtered_windows
                logger.info(f"After filtering for day {analysis_day}: {len(merged_windows)} sleep windows remain")
                
                if merged_windows:
                    max_duration = max(w["duration"] for w in merged_windows)
                    logger.info(f"Assigning sleep types - max duration: {max_duration} minutes")
                    for merge_window in merged_windows:
                        sleep_type = "main_sleep" if merge_window["duration"] == max_duration else "nap_sleep"
                        merge_window["type"] = sleep_type
                        logger.info(f"   Sleep window {merge_window['start']} -> {merge_window['end']}: duration={merge_window['duration']}min, type={sleep_type}")
                else:
                    logger.info(f"No sleep windows belong to analysis day {analysis_day}")
                    return None
            
            logger.info(f"\n\nMerged sleep windows info: {merged_windows}\n\n")
            
            # For every merged sleep window (main and naps), calculate the sleep data info
            logger.info(f"Found {len(merged_windows)} sleep windows for user {user_uid}, calculating data and sending them to Supabase")
            all_sleep_data = []
            
            for merge_window in merged_windows:
                sleep_data = {
                    "estimated_start_date_time": merge_window["start"] if merge_window["type"] == "nap_sleep" else None,
                    "estimated_end_date_time": merge_window["end"] if merge_window["type"] == "nap_sleep" else None,
                    "duration": merge_window["duration"],
                    "actual_duration": merge_window.get("actual_duration", None),
                    "sleep_screen_time": None,
                    "nts": None,
                    "nse": None,
                    "nst": None,
                    "nta": None,
                    "sqs": None,
                    "type": merge_window.get("type")
                }
                
                if merge_window["type"] == "main_sleep":
                    logger.info(f"Processing main_sleep with duration: {merge_window.get('duration')}, actual_duration: {merge_window.get('actual_duration')}")
                    sleep_scoring = self._calculate_sleep_data_info(merge_window, user_uid)
                    
                    if sleep_scoring is None:
                        logger.error(f"   CRITICAL: Could not calculate sleep data info for main sleep")
                        logger.error(f"   merge_window: {merge_window}")
                        continue  # Skip this main sleep but continue with others
                     
                    sleep_data.update({
                        "estimated_start_date_time": sleep_scoring[0],
                        "estimated_end_date_time": sleep_scoring[1],
                        "sleep_screen_time": sleep_scoring[4],
                        "nts": sleep_scoring[5],
                        "nse": sleep_scoring[6],
                        "nst": sleep_scoring[7],
                        "nta": sleep_scoring[8],
                        "sqs": sleep_scoring[9]
                    })
                
                logger.info(f"\n\nProcessed sleep data for {merge_window.get('type')}: {sleep_data}\n\n")
                all_sleep_data.append(sleep_data)
            
            # Return all sleep data (list) instead of just one
            return all_sleep_data if all_sleep_data else None
        except Exception as e:
            logger.error(f"Error computing sleep data for user {user_uid}: {e}")
            return None

    def _assign_sleep_to_day(self, sleep_start, sleep_end, analysis_day):
        """
        Assign sleep to analysis day based on start/end times.
        
        Args:
            sleep_start: Sleep start datetime
            sleep_end: Sleep end datetime  
            analysis_day: Date being analyzed
            
        Returns:
            bool: True if sleep belongs to analysis day, False otherwise
        """
        try:
            sleep_start_date = sleep_start.date()
            sleep_end_date = sleep_end.date()
            
            # Rule 1: Sleep ends on analysis day → belongs to analysis day
            # This captures the main overnight sleep that you wake up from
            if sleep_end_date == analysis_day:
                return True
            
            # Rule 2: Sleep both starts AND ends on analysis day → belongs to analysis day
            # This captures same-day naps
            if sleep_start_date == analysis_day and sleep_end_date == analysis_day:
                return True  # This is actually redundant given Rule 1, but explicit for clarity
            
            return False
        except Exception as e:
            logger.error(f"Error assigning sleep to day: {e}")
            return False

    def _calculate_sleep_data_info(self, detected_sleep_window, user_uid: str):
        """
        This function calculates the sleep data info for a detected sleep window:
        - Sleep efficiency
        - Sleep screen time
        - Sleep quality score
        Args:
            detected_sleep_window: Detected sleep window
            user_uid: User ID
        Returns:
            List of sleep data info
        """

        if not detected_sleep_window:
            logger.error("No detected sleep window found")
            return None

        logger.info(f"Calculating sleep data info for window: duration={detected_sleep_window.get('duration')}, actual_duration={detected_sleep_window.get('actual_duration')}")

        # Sleep efficiency
        main_sleep_efficiency = self._calculate_sleep_efficiency(detected_sleep_window)

        if main_sleep_efficiency is None:
            logger.error(f"   Could not calculate sleep efficiency for window: {detected_sleep_window}")
            logger.error(f"   Duration: {detected_sleep_window.get('duration')}")
            logger.error(f"   Actual Duration: {detected_sleep_window.get('actual_duration')}")
            return None
        
        logger.info(f"   Sleep efficiency calculated: {main_sleep_efficiency}%")
        detected_sleep_window["sleep_efficiency"] = main_sleep_efficiency

        # Sleep screen time
        logger.info(f"   Calculating screen time for sleep window from {detected_sleep_window['start']} to {detected_sleep_window['end']}")
        screen_time_analysis_result = self._calc_screen_time_stat(user_uid, detected_sleep_window["start"], detected_sleep_window["end"]) 
        
        # Check if screen_time_analysis_result is None before accessing its elements
        if screen_time_analysis_result is None:
            logger.info("   No screen time events found during sleep window, using 0 for screen time")
            sleep_screen_time_sec = 0
        else:
            sleep_screen_time_sec = screen_time_analysis_result[0] # total screen time for the duration of the sleep analysis in seconds
            if sleep_screen_time_sec is None:
                logger.error("   Could not calculate sleep screen time - result[0] is None")
                return None
            else:
                sleep_screen_time_sec = sleep_screen_time_sec * 1000 # convert to milliseconds

        logger.info(f"   Total screen on time during sleep: {sleep_screen_time_sec} ms of type {detected_sleep_window['type']}")

        # Sleep quality score
        logger.info(f"   Calculating sleep quality scores...")
        sleep_quality_scores = self._calculate_sleep_quality(detected_sleep_window, sleep_screen_time_sec)

        if sleep_quality_scores is not None:
            logger.info(f"   Sleep quality scores calculated successfully: SQS={sleep_quality_scores[4]}")
            return [
                detected_sleep_window["start"], 
                detected_sleep_window["end"], 
                detected_sleep_window["duration"], 
                detected_sleep_window["actual_duration"], 
                sleep_screen_time_sec, sleep_quality_scores[0],
                sleep_quality_scores[1], 
                sleep_quality_scores[2],
                sleep_quality_scores[3],
                sleep_quality_scores[4]
            ]
        else:
            logger.error("   CRITICAL: Could not calculate sleep quality score")
            logger.error(f"   detected_sleep_window: {detected_sleep_window}")
            return None

    def _calculate_sleep_quality(self, detected_sleep_window, total_screen_on_time_ms=0) -> list | None:

        if detected_sleep_window is None:
            logger.error("   No main sleep window found.")
            return None

        ts = detected_sleep_window.get("duration", 0) # total sleep in minutes
        se = detected_sleep_window.get("sleep_efficiency", 0) # sleep efficiency in percentage
        st = total_screen_on_time_ms # screen on time in milliseconds

        start_time_str = detected_sleep_window.get('start', '')
        end_time_str = detected_sleep_window.get('end', '')

        nta = self._normalize_time_alignment(start_time_str, end_time_str)
        nts = self._normalize_total_sleep(ts) # normalize total sleep, closer to 1 the better
        nse = min(1.0, se / 90) # normalize sleep efficiency
        nst = max(0.0, 1 - (st / (10 * 60 * 1000)))  # if > 10min, penalized heavily
        sqs = (0.35 * nts) + (0.35 * nse) + (0.15 * nst) + (0.15 * nta)

        return [nts, nse, nst, nta, sqs]

    def _normalize_time_alignment(self, start, end) -> float:
        bedtime = start.time()
        waketime = end.time()

        # Optimal ranges
        optimal_bed_start = time(20, 0)   # 8:00 PM
        optimal_bed_end = time(0, 0)      # 12:00 AM
        optimal_wake_start = time(5, 0)   # 5:00 AM
        optimal_wake_end = time(9, 0)     # 9:00 AM

        # The goal is to score how close bedtime is to 23:00 (11:00 PM) and wake time is to 07:00 (7:00 AM).
        # The closer they are to those target times, the higher the score (max 1.0).
        # The farther away they are (up to 4+ hours difference), the lower the score (down to 0.0).

        # Check bedtime
        if bedtime >= optimal_bed_start or bedtime <= optimal_bed_end:
            bed_score = 1.0
        else:
            bed_score = max(0.0, 1 - abs((datetime.combine(start.date(), bedtime) - datetime.combine(start.date(), time(23, 0))).seconds / 3600) / 4)

        # Check wake time
        if optimal_wake_start <= waketime <= optimal_wake_end:
            wake_score = 1.0
        else:
            wake_score = max(0.0, 1 - abs((datetime.combine(end.date(), waketime) - datetime.combine(end.date(), time(7, 0))).seconds / 3600) / 4)

        return (bed_score + wake_score) / 2

    def _normalize_total_sleep(self, total_sleep_min) -> float:
        if 510 <= total_sleep_min <= 540:
            return 1.0
        elif 450 <= total_sleep_min < 510:
            return 0.9 + 0.1 * ((total_sleep_min - 450) / 60)  # Linear: 0.9 → 1.0
        elif 420 <= total_sleep_min < 450:
            return 0.75 + 0.14 * ((total_sleep_min - 420) / 30)  # Linear: 0.75 → 0.89
        elif 360 <= total_sleep_min < 420:
            return 0.5 + 0.24 * ((total_sleep_min - 360) / 60)  # Linear: 0.5 → 0.74
        elif total_sleep_min < 360:
            return max(0.0, total_sleep_min / 360 * 0.49)  # Steep drop to 0 below 6 hours
        elif 540 < total_sleep_min <= 600:
            return 1.0 - ((total_sleep_min - 540) / 60) * 0.2  # Drops from 1.0 to 0.8
        else:
            return 0.8  # Cap score for > 600 min

    def _calculate_sleep_efficiency(self, sleep_window) -> float | None:
        duration = sleep_window.get("duration", 0)
        actual_duration = sleep_window.get("actual_duration")
        
        logger.info(f"Sleep efficiency calculation: duration={duration}, actual_duration={actual_duration}")
        
        if duration == 0:
            logger.error("Sleep efficiency calculation failed: duration is 0")
            return None
            
        if actual_duration is None:
            logger.error("Sleep efficiency calculation failed: actual_duration is None")
            return None
            
        if actual_duration < 0:
            logger.error(f"Sleep efficiency calculation failed: actual_duration is negative ({actual_duration})")
            return None
            
        efficiency = (actual_duration / duration) * 100
        logger.info(f"Sleep efficiency: {efficiency}%")
        return efficiency
    
    def _calc_gps_data(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> dict | None:
        """
        This function calculates the GPS data.
        Args:
            user_uid: str - The user's unique identifier
            start_datetime: datetime - Start datetime for the analysis
            end_datetime: datetime - End datetime for the analysis
        Returns:
            Dictionary with the GPS data
        """
        try:
            # Fetch the GPS data from the local database for the current day analyzed
            gps_data = self.db_service.get_gps_data(user_uid, start_datetime, end_datetime)

            if gps_data is None or len(gps_data) == 0:
                logger.info("No GPS data found.")
                return None
            
            # Convert list of objects to DataFrame with proper column names
            gps_data_df = pd.DataFrame([
                {
                    'id': event.id,
                    'gps_event_id': event.gps_event_id,
                    'user_uid': event.user_uid,
                    'latitude': event.latitude,
                    'longitude': event.longitude,
                    'accuracy': event.accuracy,
                    'bearing': event.bearing,
                    'speed': event.speed,
                    'speed_accuracy_meters_per_second': event.speed_accuracy_meters_per_second,
                    'timestamp_now': event.timestamp_now
                }
                for event in gps_data
            ])
            
            EPS_METERS = 50
            MIN_SAMPLES = 60
            ACCURACY_EXCL = 50
            GPS_POINTS_SAMPLE_RATE = 30

            # Sort the data by timestamp
            gps_data_df.sort_values(by='timestamp_now', ascending=False, inplace=True)

            # Start by cleaning the data
            gps_data_df = self._clean_gps_data(gps_data_df, ACCURACY_EXCL)

            if gps_data_df is None:
                logger.error("No GPS data found after cleaning.")
                return None

            # ----------------------------------------------------------------------------------- #

            # Start with finding the key-locations (and HOME)
            key_loc_info_df = self._identify_key_locations(
                gps_data_df, 
                EPS_METERS, 
                MIN_SAMPLES,
                GPS_POINTS_SAMPLE_RATE
            )

            if key_loc_info_df is None:
                logger.error("No key-locations info found.")
                return None
            else:
                logger.info(f"\n\nKey-locations info found: {key_loc_info_df}\n\n")

            # Now that the main dataframe is ready we can form/compute the main route
            gps_data_df = self._compute_main_gps_route(key_loc_info_df, gps_data_df, EPS_METERS)

            if gps_data_df is None:
                logger.error("No GPS data found after computing the main GPS route.")
                return None

            # Fix wrong key-locs
            gps_data_df = self._fix_wrong_key_locs(gps_data_df)

            if gps_data_df is None:
                logger.error("No GPS data found after fixing wrong key-locs.")
                return None

            # Now for each key-location (cluster) find the necessary information
            key_loc_clusters_info_unique = self._compute_info_of_key_locations_clusters(gps_data_df)

            if key_loc_clusters_info_unique is None:
                logger.error("No key-locations clusters info found.")
                return None
            
            logger.info(f"Found {len(key_loc_clusters_info_unique)} unique key location clusters")
            logger.info(f"\n\nKey-locations clusters info found: {key_loc_clusters_info_unique}\n\n")
            if not key_loc_clusters_info_unique.empty:
                logger.info(f"Key location types found: {key_loc_clusters_info_unique['key_loc_type'].unique().tolist()}")
                home_locations_count = (key_loc_clusters_info_unique['key_loc_type'] == 'HOME').sum()
                non_home_locations_count = (key_loc_clusters_info_unique['key_loc_type'] != 'HOME').sum()
                total_time_spend_home = key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] == 'HOME']['total_time_spent_seconds'].sum()
                logger.info(f"Total time spend in HOME: {total_time_spend_home}")
                logger.info(f"HOME locations: {home_locations_count}, Non-HOME locations: {non_home_locations_count}")
            
            # If the user has more than one key-location, we can compute the transitions between them
            # but if the user has only one key-location, we cannot compute the transitions.
            # EX. The user stayed in HOME all day, so we cannot compute the transitions between HOME and other key-locations.
            if len(key_loc_clusters_info_unique) > 1:
                # Now find the transitions clusters between the key-locations
                key_loc_transitions_info = self._compute_transitions_info_of_key_locations_clusters(gps_data_df)

                if key_loc_transitions_info is None:
                    logger.error("No key-locations transitions info found.")
                    return None

                # Run a simple check to see if the computations are correct (check does not do something)
                self._check_computations_results(key_loc_clusters_info_unique, key_loc_transitions_info)
            else:
                logger.info("Only one key-location found. Cannot compute transitions between key-locations.")
                key_loc_transitions_info = None

            # Compute convex hull
            convex_hull_info = self._compute_convex_hull(gps_data_df)

            if convex_hull_info is None:
                logger.error("No convex hull info found.")
                return None

            # Compute gravimetric compactness
            gravimetric_compactness = self._compute_gravimetric_compactness(convex_hull_info['area'], convex_hull_info['perimeter'])

            if gravimetric_compactness is None:
                logger.error("No gravimetric compactness found.")
                return None

            # Compute SDE (Standard Deviational Ellipse)
            sde_info = self._compute_sde(gps_data_df)

            if sde_info is None:
                logger.error("No SDE info found.")
                return None

            # Note: are of SDE is different that the are of the convex hull 
            # Most of the time the area of the SDE is smaller than the area of the convex hull 
            # unless data is tightly clustered and uniformly distributed.
            # Convex hull represents the tightest convex polygon that encloses all GPS points
            # SDE represents the directional spread of points from the center using standard deviation along principal axes
            # and only captures the core distribution (e.g. 68% of points for 1 SD), not the full extent.

            # Compute max distance from home
            home_locations = key_loc_info_df[key_loc_info_df['type'] == 'HOME'][['latitude', 'longitude']]
            if home_locations.empty:
                logger.error("No HOME location found in key locations. Cannot compute max distance from home.")
                return None
            
            home_location_coords = home_locations.values[0]
            max_distance_from_home_info = self._compute_max_distance_from_home(gps_data_df, home_location_coords)

            if max_distance_from_home_info is None:
                logger.error("No max distance from home info found.")
                return None

            # Compute the Entropy
            entropy = self._compute_entropy(key_loc_clusters_info_unique)

            if entropy is None:
                logger.error("No entropy found.")
                return None

            if key_loc_transitions_info is not None and len(key_loc_transitions_info) > 0:
                # Compute the time the user was most active (1: Morning, 2: Neutral, 3: Evening)
                active_period_time = self._compute_time_period_active(key_loc_transitions_info)

                if active_period_time is None:
                    logger.error("No active period time found.")
                else:
                    logger.info(f"Active period time found: {active_period_time}")
            else:
                logger.info("No key-locations transitions info found. Cannot compute active period time.")
                active_period_time = None

            # Helper function to safely convert values to numeric, defaulting to 0
            def safe_numeric(value, default=0):
                if value is None or pd.isna(value):
                    return default
                try:
                    return float(value) if isinstance(value, (int, float)) else default
                except (ValueError, TypeError):
                    return default

            try:
                # Now build the analysis results
                gps_data_analysis_results = {
                    "key_locations_clusters_info": [
                        {
                            "key_location_id": row['belonging_key_loc'],
                            "latitude": safe_numeric(row['latitude']),
                            "longitude": safe_numeric(row['longitude']),
                            "total_time_spent_seconds": safe_numeric(row['total_time_spent_seconds']),
                            "num_of_gps_events": safe_numeric(row['num_of_gps_events']),
                            "key_loc_type": row['key_loc_type'],
                        }
                        for _, row in key_loc_clusters_info_unique.iterrows()
                    ],
                    "key_locations_transitions_info": [
                        {
                            "key_loc_start_id": row['key_loc_start_id'],
                            "key_loc_end_id": row['key_loc_end_id'],
                            "start_time_of_transition": row['start_time_of_transition'].strftime('%Y-%m-%d %H:%M:%S'),
                            "end_time_of_transition": row['end_time_of_transition'].strftime('%Y-%m-%d %H:%M:%S'),
                            "total_time_travel_seconds": safe_numeric(row['total_time_travel_seconds']),
                            "total_distance_traveled_km": safe_numeric(row['total_distance_traveled_km']),
                            "total_events_in_transition_cluster": safe_numeric(row['total_events_in_transition_cluster']),
                        }
                        for _, row in key_loc_transitions_info.iterrows()
                    ] if key_loc_transitions_info is not None else [],
                    "total_time_spend_in_home_seconds": safe_numeric(
                        key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] == 'HOME']['total_time_spent_seconds'].sum()
                    ),
                    "total_time_spend_traveling_seconds": safe_numeric(
                        key_loc_transitions_info['total_time_travel_seconds'].sum() if key_loc_transitions_info is not None else 0
                    ),
                    "total_time_spend_out_of_home_seconds": safe_numeric(
                        (key_loc_transitions_info['total_time_travel_seconds'].sum() if key_loc_transitions_info is not None else 0) + 
                        (key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] != 'HOME']['total_time_spent_seconds'].sum() 
                        if not key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] != 'HOME'].empty else 0)
                    ),
                    "total_distance_traveled_km": safe_numeric(
                        key_loc_transitions_info['total_distance_traveled_km'].sum() if key_loc_transitions_info is not None else 0
                    ),
                    "average_time_spend_in_locations_hours": safe_numeric(
                        (key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] != 'HOME']['total_time_spent_seconds'].mean() / 3600) 
                        if not key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] != 'HOME'].empty else 0.0
                    ),
                    "number_of_unique_locations": safe_numeric(
                        key_loc_info_df['key_location_id'].nunique()
                    ),
                    "number_of_locations_total": safe_numeric(
                        key_loc_info_df.shape[0]
                    ),
                    "first_move_timestamp_after_3am": key_loc_transitions_info['start_time_of_transition'].min().strftime('%Y-%m-%d %H:%M:%S') if key_loc_transitions_info is not None and not key_loc_transitions_info.empty else None,
                    "convex_hull": {
                        "area_m2": safe_numeric(convex_hull_info['area']),
                        "perimeter_m": safe_numeric(convex_hull_info['perimeter']),
                        "gravimetric_compactness": safe_numeric(gravimetric_compactness)
                    },
                    "standard_deviation_ellipse": {
                        "mean_center": list(sde_info['mean_center']) if sde_info['mean_center'] is not None else [0.0, 0.0],
                        "width_m": safe_numeric(sde_info['width_m']),
                        "height_m": safe_numeric(sde_info['height_m']),
                        "angle_deg": safe_numeric(sde_info['angle_deg']),
                        "area_m2": safe_numeric(sde_info['area_m2']),
                    },
                    "max_distance_from_home": {
                        "distance_km": safe_numeric(max_distance_from_home_info['max_distance']),
                        "timestamp": max_distance_from_home_info['max_distance_timestamp'].strftime('%Y-%m-%d %H:%M:%S') if max_distance_from_home_info['max_distance_timestamp'] else None,
                        "coords": max_distance_from_home_info['max_distance_point_coords'].to_dict(orient='records') if max_distance_from_home_info['max_distance_point_coords'] is not None and not max_distance_from_home_info['max_distance_point_coords'].empty else None
                    },
                    "entropy": safe_numeric(entropy),
                    "time_period_active": safe_numeric(active_period_time)
                }
            except Exception as e:
                logger.error(f"Error building GPS data analysis results: {e}")
                return None
            return gps_data_analysis_results
        except Exception as e:
            logger.error(f"Error calculating GPS data: {e}")
            return None
    
    def _compute_time_period_active(self, df: pd.DataFrame) -> int | None:
        """
        Compute the time the user was most active (1: Morning, 2: Neutral, 3: Evening)
        Assignment of OH activities (moves and OH stops) based on start time to the classes morning (6 AM–12 noon), after
        noon (12 noon–6 PM), or evening (6 PM–11 PM). A day is coded as 1 (morning day) if morning activities > evening 
        activities; as 3 (evening day) if evening activities > morning activities; 2 (neutral timing day) in all other cases
        Args:
            df: DataFrame with the GPS data
        Returns:
            Int with the time period the user was most active
        """
        try:
            morning_count = 0
            afternoon_count = 0
            evening_count = 0

            for _, row in df.iterrows():
                start_time = row['start_time_of_transition'].time()
                if time(6, 0) <= start_time < time(12, 0):
                    morning_count += 1
                elif time(12, 0) <= start_time < time(18, 0):
                    afternoon_count += 1
                elif time(18, 0) <= start_time < time(23, 59):
                    evening_count += 1

            if morning_count > evening_count:
                return 1  # Morning day
            elif evening_count > morning_count:
                return 3  # Evening day
            else:
                return 2  # Neutral timing day
        except Exception as e:
            logger.error(f"Error computing time period active: {e}")
            return None

    def _compute_entropy(self, df: pd.DataFrame) -> float | None:
        """
        Compute the Shannon entropy of time spent across different stop locations.
        Higher entropy = more even time distribution and/or more unique locations.

        Args:
            df: DataFrame with a 'total_time_spent_seconds' column per location cluster.
        Returns:
            Float entropy in natural units (nats), or None if invalid input.
        """
        try:
            if df.empty or 'total_time_spent_seconds' not in df:
                return None

            total_time = df['total_time_spent_seconds'].sum()
            if total_time <= 0:
                return None

            entropy = 0.0
            for row in df.itertuples():
                pi = row.total_time_spent_seconds / total_time
                if pi > 0:
                    entropy += pi * np.log(pi)  # Natural log = entropy in nats

            return -entropy  # Negate to get Shannon entropy    

        except Exception as e:
            print(f"Error computing entropy: {e}")
            return None
    
    def _compute_max_distance_from_home(self, df: pd.DataFrame, home_location_coords: tuple) -> dict | None:
        """
        Compute the max distance from home.
        Args:
            df: DataFrame with the GPS data
            home_location_coords: Tuple with the home location coordinates
        Returns:
            Tuple with the max distance, timestamp and point coordinates
        """
        try:
            home_lat, home_lon = home_location_coords
            max_distance = 0.0
            max_distance_timestamp = None
            max_distance_point_coords = None

            for _, row in df.iterrows():
                gps_lat = row['latitude']
                gps_lon = row['longitude']
                dist = distance((home_lat, home_lon), (gps_lat, gps_lon)).km
                
                if dist > max_distance:
                    max_distance_timestamp = row['timestamp_now']
                    max_distance_point_coords = pd.DataFrame({'latitude': [gps_lat], 'longitude': [gps_lon]})
                    max_distance = dist

            return {
                'max_distance': max_distance,
                'max_distance_timestamp': max_distance_timestamp,
                'max_distance_point_coords': max_distance_point_coords
            }
        except Exception as e:
            logger.error(f"Error computing max distance from home: {e}")
            return None

    def _compute_sde(self, df: pd.DataFrame, scale: int=1) -> dict | None:
        try:
            if df.empty or len(df) < 2:
                logger.warning("Insufficient GPS points for SDE calculation")
                return None

            # Use UTM projection based on mean longitude
            mean_lon = df['longitude'].mean()
            mean_lat = df['latitude'].mean()
            zone_number = int((mean_lon + 180) / 6) + 1
            is_northern = mean_lat >= 0

            proj = pyproj.Proj(proj='utm', zone=zone_number, ellps='WGS84', south=not is_northern)
            xs, ys = proj(df['longitude'].values, df['latitude'].values)
            coords = np.column_stack((xs, ys))

            # Check for spatial diversity
            x_range = np.max(xs) - np.min(xs)
            y_range = np.max(ys) - np.min(ys)
            
            # If the spatial spread is very small, return minimal SDE values
            if x_range < 1 and y_range < 1:  # Less than 1 meter spread
                logger.info(f"GPS points have minimal spatial spread for SDE (x_range: {x_range:.2f}m, y_range: {y_range:.2f}m)")
                center_lon, center_lat = proj(np.mean(xs), np.mean(ys), inverse=True)
                return {
                    'mean_center': (center_lat, center_lon),
                    'width_m': 0.0,
                    'height_m': 0.0,
                    'angle_deg': 0.0,
                    'area_m2': 0.0
                }

            # Mean center in projected space
            center = np.mean(coords, axis=0)
            centered_coords = coords - center

            # Check if all points are the same (zero variance)
            if np.allclose(centered_coords, 0, atol=1e-6):
                logger.info("All GPS points are at the same location for SDE calculation")
                center_lon, center_lat = proj(center[0], center[1], inverse=True)
                return {
                    'mean_center': (center_lat, center_lon),
                    'width_m': 0.0,
                    'height_m': 0.0,
                    'angle_deg': 0.0,
                    'area_m2': 0.0
                }

            # PCA for orientation
            pca = PCA(n_components=2)
            transformed = pca.fit_transform(centered_coords)
            std_devs = np.std(transformed, axis=0)

            # Width and height of the ellipse
            width, height = 2 * scale * std_devs

            # Orientation (angle of major axis in degrees)
            angle = np.degrees(np.arctan2(*pca.components_[0][::-1]))

            # Area in square meters
            area = np.pi * (width / 2) * (height / 2)

            # Convert center back to lat/lon
            center_lon, center_lat = proj(center[0], center[1], inverse=True)

            logger.info(f"SDE computed: width={width:.2f}m, height={height:.2f}m, area={area:.2f}m²")
            return {
                'mean_center': (center_lat, center_lon),
                'width_m': width,
                'height_m': height,
                'angle_deg': angle,
                'area_m2': area
            }
        except Exception as e:
            logger.error(f"Error computing SDE: {e}")   
            logger.info("Falling back to zero SDE values due to computation failure")
            # Try to return a fallback with mean coordinates
            try:
                mean_lat = df['latitude'].mean()
                mean_lon = df['longitude'].mean()
                return {
                    'mean_center': (mean_lat, mean_lon),
                    'width_m': 0.0,
                    'height_m': 0.0,
                    'angle_deg': 0.0,
                    'area_m2': 0.0
                }
            except:
                return None
    
    def _compute_gravimetric_compactness(self, area: float, perimeter: float) -> float | None:
        """
        Compute the gravimetric compactness of the user.
        Args:
            area: Area of the convex hull
            perimeter: Perimeter of the convex hull
        Returns:
            Float with the gravimetric compactness value, or 0 if area is zero
        """
        try:
            if area <= 0:
                logger.info("Area is zero or negative, cannot compute gravimetric compactness. Returning 0.")
                return 0.0
            
            K = perimeter / (2 * np.sqrt(np.pi * area))
            return K
        except Exception as e:
            logger.error(f"Error computing gravimetric compactness: {e}")
            return 0.0

    def _compute_convex_hull(self, df: pd.DataFrame) -> dict | None:
        """
        Compute the convex hull the user has created.
        Args:
                : DataFrame with the GPS data
        Returns:
            Dict with the convex hull area and perimeter, or default values if insufficient spatial spread
        """
        try:
            if df.empty or len(df) < 3:
                logger.warning("Insufficient GPS points for convex hull calculation")
                return {'area': 0.0, 'perimeter': 0.0}

            # Calculate the central longitude to determine UTM zone
            mean_lon = df['longitude'].mean()
            zone_number = int((mean_lon + 180) / 6) + 1
            is_northern = df['latitude'].mean() >= 0

            # Define UTM projection for local area
            proj = pyproj.Proj(proj='utm', zone=zone_number, ellps='WGS84', south=not is_northern)

            # Convert lat/lon to projected coordinates (in meters)
            xs, ys = proj(df['longitude'].values, df['latitude'].values)
            coords = np.column_stack((xs, ys))
            
            # Check for spatial diversity - if all points are too close, convex hull will fail
            x_range = np.max(xs) - np.min(xs)
            y_range = np.max(ys) - np.min(ys)
            
            # If the spatial spread is very small (< 10 meters in both dimensions), 
            # treat it as a single location
            if x_range < 10 and y_range < 10:
                logger.info(f"GPS points have minimal spatial spread (x_range: {x_range:.2f}m, y_range: {y_range:.2f}m). Treating as single location.")
                return {'area': 0.0, 'perimeter': 0.0}
            
            # Remove duplicate coordinates to avoid collinearity issues
            unique_coords = np.unique(coords, axis=0)
            if len(unique_coords) < 3:
                logger.info(f"Only {len(unique_coords)} unique coordinate(s) found. Cannot compute convex hull.")
                return {'area': 0.0, 'perimeter': 0.0}

            # Compute convex hull
            hull = ConvexHull(unique_coords)
            hull_points = unique_coords[hull.vertices]

            # Compute perimeter (Euclidean distances in projected space)
            perimeter = 0.0
            for i in range(len(hull_points)):
                p1 = hull_points[i]
                p2 = hull_points[(i + 1) % len(hull_points)]
                perimeter += np.linalg.norm(p2 - p1)

            area = hull.volume  # area in square meters (volume is area in 2D)

            logger.info(f"Convex hull computed: area={area:.2f} m², perimeter={perimeter:.2f} m")
            return {
                'area': area,
                'perimeter': perimeter,
            }
            
        except Exception as e:
            logger.error(f"Error computing convex hull: {e}")
            logger.info("Falling back to zero area/perimeter due to convex hull computation failure")
            return {'area': 0.0, 'perimeter': 0.0}
        
    def _check_computations_results(self, key_loc_clusters_info_unique: pd.DataFrame, key_loc_transitions_info: pd.DataFrame):
        """
        Check if the computations are correct.
        We check if the total time spend in each location + the time traveling/transitioning is equal to the total time of the day (24 hours).
        Args:
            key_loc_clusters_info_unique: DataFrame with the basic info of each key-location cluster
            key_loc_transitions_info: DataFrame with the transitions info of the key-locations clusters
        Returns:
            None
        """
        time_spend_home_hours = key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] == 'HOME']['total_time_spent_seconds'].values[0]/3600
        time_spend_other_locations_hours = key_loc_clusters_info_unique[key_loc_clusters_info_unique['key_loc_type'] != 'HOME']['total_time_spent_seconds'].values[0]/3600
        time_spend_transitioning_hours = key_loc_transitions_info['total_time_travel_seconds'].sum()/3600

        total_time = time_spend_home_hours + time_spend_other_locations_hours + time_spend_transitioning_hours
        
        if total_time > 24:
            logger.warning(f"Total time spent in key locations and transitions is greater than 24 hours: {total_time:.3f}.")
        else:
            logger.info(f"Total time spent in key locations and transitions is less than 24 hours: {total_time:.3f}, data might be missing for {24 - total_time:.3f} hours.")

    def _compute_transitions_info_of_key_locations_clusters(self, df: pd.DataFrame):
        """
        Compute the transitions info of the key-locations clusters.
        A transition is a movement from one key-location to another (or the same).
        Args:
            df: DataFrame with the GPS data
        Returns:
            DataFrame with the transitions info of the key-locations clusters
        """
        try:
            df = df.sort_values(by='timestamp_now')

            transition_cluster = []
            transition_cluster_basic_info = [] # holds the basic info of each key transition cluster
            recording = False
            transition_clusters_list = []

            for idx, gps_event in df.iterrows():
                if np.isnan(gps_event['belonging_key_loc']) == True and recording is False:
                    transition_cluster.append(gps_event)
                    recording = True
                elif np.isnan(gps_event['belonging_key_loc']) == True and recording is True:
                    transition_cluster.append(gps_event)
                elif np.isnan(gps_event['belonging_key_loc']) == False and recording is True:
                    transition_cluster_df = pd.DataFrame(transition_cluster)

                    time_distance = self._compute_total_time_from_timestamps(transition_cluster_df)

                    transition_cluster_start_time = transition_cluster_df['timestamp_now'].iloc[0]
                    transition_cluster_end_time = transition_cluster_df['timestamp_now'].iloc[-1]
                    
                    try:
                        key_loc_start_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[0]].index - 1
                    except IndexError:
                        key_loc_start_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[0]].index

                    try:
                        key_loc_end_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[-1]].index + 1
                    except IndexError:
                        key_loc_end_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[-1]].index

                    total_distance_km = self._compute_length_of_route(transition_cluster_df)
                    
                    transition_cluster_basic_info.append({
                            'key_loc_start_id': df['belonging_key_loc'].iloc[key_loc_start_index[0]],
                            'key_loc_end_id': df['belonging_key_loc'].iloc[key_loc_end_index[0]],
                            'transition_cluster_start_time': transition_cluster_start_time,
                            'transition_cluster_end_time': transition_cluster_end_time,
                            'trans_cluster_start_latitude': transition_cluster_df['latitude'].iloc[0],
                            'trans_cluster_start_longitude': transition_cluster_df['longitude'].iloc[0],
                            'trans_cluster_end_latitude': transition_cluster_df['latitude'].iloc[-1],
                            'trans_cluster_end_longitude': transition_cluster_df['longitude'].iloc[-1],
                            'time_spent_seconds': time_distance,
                            'total_distance_km': total_distance_km,
                            'num_of_gps_events': len(transition_cluster_df)
                    })

                    transition_clusters_list.append(transition_cluster_df)
                    transition_cluster = []
                    recording = False

            # Compute the lasts sub-route info
            if len(transition_cluster) > 0:
                transition_cluster_df = pd.DataFrame(transition_cluster)
                    
                time_distance = self._compute_total_time_from_timestamps(transition_cluster_df)

                transition_cluster_start_time = transition_cluster_df['timestamp_now'].iloc[0]
                transition_cluster_end_time = transition_cluster_df['timestamp_now'].iloc[-1]

                try:
                    key_loc_start_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[0]].index - 1
                    type_of_start_key_loc = df['belonging_key_loc'].iloc[key_loc_start_index[0]]
                except IndexError:
                    key_loc_start_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[0]].index
                    type_of_start_key_loc = df['belonging_key_loc'].iloc[key_loc_start_index[0]]

                try:
                    key_loc_end_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[-1]].index + 1
                    type_of_end_key_loc = df['belonging_key_loc'].iloc[key_loc_end_index[0]]
                except IndexError:
                    key_loc_end_index = df[df['gps_event_id'] == transition_cluster_df['gps_event_id'].iloc[-1]].index
                    type_of_end_key_loc = df['belonging_key_loc'].iloc[key_loc_end_index[0] - 1]

                total_distance_km = self._compute_length_of_route(transition_cluster_df)
                transition_cluster_basic_info.append({
                    'key_loc_start_id': type_of_start_key_loc,
                    'key_loc_end_id': type_of_end_key_loc,
                    'transition_cluster_start_time': transition_cluster_start_time,
                    'transition_cluster_end_time': transition_cluster_end_time,
                    'trans_cluster_start_latitude': transition_cluster_df['latitude'].iloc[0],
                    'trans_cluster_start_longitude': transition_cluster_df['longitude'].iloc[0],
                    'trans_cluster_end_latitude': transition_cluster_df['latitude'].iloc[-1],
                    'trans_cluster_end_longitude': transition_cluster_df['longitude'].iloc[-1],
                    'time_spent_seconds': time_distance,
                    'total_distance_km': total_distance_km,
                    'num_of_gps_events': len(transition_cluster_df)
                })
                transition_clusters_list.append(transition_cluster_df)

            logger.info(f"Length of transition_clusters_list: {len(transition_clusters_list)}")

            if len(transition_cluster_basic_info) == 0:
                logger.error("No transition cluster basic info found.")
                return None

            # Construct the final list of transitions based on the computed basic info
            transitions_final_df = self._constract_final_list_of_transitions(transition_cluster_basic_info)

            if transitions_final_df is None:
                logger.error("No transitions final list found.")
                return None

            return transitions_final_df
        except Exception as e:
            logger.error(f"Error computing transitions info of key locations clusters: {e}")
            return None

    def _constract_final_list_of_transitions(self, transition_cluster_basic_info: list) -> pd.DataFrame | None:
        """
        Construct the final list of transitions 
        Args:
            transition_cluster_basic_info: List with the basic info of each key transition cluster
        Returns:
            DataFrame with the final list of transitions
        """
        try:
            start_key_loc_id = transition_cluster_basic_info[0]['key_loc_start_id']
            transitions_final_list = []

            for idx, trans_cluster_info in enumerate(transition_cluster_basic_info):

                if idx == len(transition_cluster_basic_info) - 1: # we are at the last transition cluster and we can not found any change in the key location
                    total_time_transition_cluster = trans_cluster_info['time_spent_seconds']
                    total_distance_traveled_transition_cluster = trans_cluster_info['total_distance_km']
                    total_events_in_transition_cluster = trans_cluster_info['num_of_gps_events']

                    transitions_final_list.append({
                            'key_loc_start_id': start_key_loc_id,
                            'key_loc_end_id': trans_cluster_info['key_loc_end_id'],
                            'start_time_of_transition': trans_cluster_info['transition_cluster_start_time'],
                            'end_time_of_transition': trans_cluster_info['transition_cluster_end_time'],
                            'total_time_travel_seconds': total_time_transition_cluster,
                            'total_distance_traveled_km': total_distance_traveled_transition_cluster,
                            'total_events_in_transition_cluster': total_events_in_transition_cluster,
                    })
                    start_key_loc_id = trans_cluster_info['key_loc_end_id']

                if start_key_loc_id != trans_cluster_info['key_loc_end_id']:
                    total_time_transition_cluster = trans_cluster_info['time_spent_seconds']
                    total_distance_traveled_transition_cluster = trans_cluster_info['total_distance_km']
                    total_events_in_transition_cluster = trans_cluster_info['num_of_gps_events']

                    transitions_final_list.append({
                            'key_loc_start_id': start_key_loc_id,
                            'key_loc_end_id': trans_cluster_info['key_loc_end_id'],
                            'start_time_of_transition': trans_cluster_info['transition_cluster_start_time'],
                            'end_time_of_transition': trans_cluster_info['transition_cluster_end_time'],
                            'total_time_travel_seconds': total_time_transition_cluster,
                            'total_distance_traveled_km': total_distance_traveled_transition_cluster,
                            'total_events_in_transition_cluster': total_events_in_transition_cluster,
                    })
                    start_key_loc_id = trans_cluster_info['key_loc_end_id']

                # If the final transition cluster has the same start and end, then it means it belongs to the previous transition cluster
                if len(transitions_final_list) > 1 and transitions_final_list[-1]['key_loc_start_id'] == transitions_final_list[-1]['key_loc_end_id']:
                    # Remove the last transition cluster info
                    transitions_final_list.pop()

            return pd.DataFrame(transitions_final_list)
        except Exception as e:
            logger.error(f"Error constructing final list of transitions: {e}")
            return None

 
    def _compute_length_of_route(self, df: pd.DataFrame) -> float:
        """
        Compute the length of the route based on the GPS points.
        Args:
            df: DataFrame with the GPS data
        Returns:
            Length of the route in kilometers
        """
        df = df.sort_values(by='timestamp_now')

        if df.shape[0] < 2:
            return 0

        total_distance = 0.0 
        for i in range(1, len(df)):
            point_1 = df.iloc[i - 1]['latitude'], df.iloc[i - 1]['longitude']
            point_2 = df.iloc[i]['latitude'], df.iloc[i]['longitude']
            distance = haversine(point_1, point_2, Unit.KILOMETERS)
            total_distance += distance

        return total_distance
    
    def _compute_info_of_key_locations_clusters(self, df: pd.DataFrame) -> pd.DataFrame | None:
        """
            Compute the basic info of each key-location cluster, that will include:
                - Total time spent in the key-location
                - Number of GPS events on that key-location
                - What type of key-location it is
            Some other info are:
                - The ID of the key-location cluster
                - Latitude and longitude of the key-location cluster
            Args:
                df: DataFrame with the GPS data
            Returns:
                DataFrame with the basic info of each key-location cluster
        """
        try:
            df = df.sort_values(by='timestamp_now')

            key_locs_in_cluster = [] # holds the GPS events that belong to the same key location cluster
            key_loc_clusters_basic_info = [] # holds the basic info of each key location cluster
            key_loc_point_tracked = [] # holds the last key location point tracked
            recording = False # holds the recording state

            for _, gps_event in df.iterrows():
                if np.isnan(gps_event['belonging_key_loc']) == False and recording is False:
                    key_locs_in_cluster.append(gps_event)
                    key_loc_point_tracked = [gps_event['latitude'], gps_event['longitude']]
                    recording = True
                elif (
                        np.isnan(gps_event['belonging_key_loc']) == False and
                        gps_event['latitude'] == key_loc_point_tracked[0] and
                        gps_event['longitude'] == key_loc_point_tracked[1] and
                        recording is True
                    ):  
                    key_locs_in_cluster.append(gps_event)
                elif (
                        np.isnan(gps_event['belonging_key_loc']) == False and
                        gps_event['latitude'] != key_loc_point_tracked[0] and
                        gps_event['longitude'] != key_loc_point_tracked[1] and
                        recording is True
                    ):  
                    time_distance = self._compute_total_time_from_timestamps(pd.DataFrame(key_locs_in_cluster))

                    key_loc_clusters_basic_info.append({
                            'belonging_key_loc': key_locs_in_cluster[0]['belonging_key_loc'],
                            'longitude': key_locs_in_cluster[0]['longitude'],
                            'latitude': key_locs_in_cluster[0]['latitude'],
                            'time_spent_seconds': time_distance,
                            'num_of_gps_events': len(key_locs_in_cluster),
                            'key_loc_type': key_locs_in_cluster[0]['type']
                    }) 

                    key_locs_in_cluster = [gps_event]
                    key_loc_point_tracked = [gps_event['latitude'], gps_event['longitude']]
                    recording = False
                
            # Compute the last key-location cluster info
            if len(key_locs_in_cluster) > 0:
                time_distance = self._compute_total_time_from_timestamps(pd.DataFrame(key_locs_in_cluster))

                key_loc_clusters_basic_info.append({
                    'belonging_key_loc': key_locs_in_cluster[0]['belonging_key_loc'],
                    'longitude': key_locs_in_cluster[0]['longitude'],
                    'latitude': key_locs_in_cluster[0]['latitude'],
                    'time_spent_seconds': time_distance,
                    'num_of_gps_events': len(key_locs_in_cluster),
                    'key_loc_type': key_locs_in_cluster[0]['type'] 
                })
            
            key_loc_clusters_basic_info_df = pd.DataFrame(key_loc_clusters_basic_info)

            # Now group the key location clusters by their belonging_key_loc and add their total time spent
            key_loc_unique_clusters_list = []
            for key_loc_id, group in key_loc_clusters_basic_info_df.groupby('belonging_key_loc'):
                total_time_spent = group['time_spent_seconds'].sum()
                num_of_gps_events = group['num_of_gps_events'].sum()
                key_loc_unique_clusters_list.append({
                    'belonging_key_loc': key_loc_id,
                    'latitude': group['latitude'].iloc[0],  # take the first latitude
                    'longitude': group['longitude'].iloc[0],  # take the first longitude
                    'total_time_spent_seconds': total_time_spent,
                    'num_of_gps_events': num_of_gps_events,
                    'key_loc_type': group['key_loc_type'].iloc[0] # to take only the type
                })
            
            # Create a dataframe with the unique key location
            key_loc_unique_clusters_df = pd.DataFrame(key_loc_unique_clusters_list)
                
            return key_loc_unique_clusters_df
        except Exception as e:
            logger.error(f"Error computing info of key locations clusters: {e}")
            return None

    def _compute_total_time_from_timestamps(self, df: pd.DataFrame, timestamp_column_name='timestamp_now') -> float:

        """
        Compute the total time from the timestamps of a dataframe.
        Args:
            df: DataFrame with the timestamps
            timestamp_column_name: Name of the column with the timestamps
        Returns:
            Total time in seconds
        """

        df[timestamp_column_name] = pd.to_datetime(df[timestamp_column_name])
        df = df.sort_values(by=timestamp_column_name)

        start_time = df[timestamp_column_name].iloc[0]
        end_time = df[timestamp_column_name].iloc[-1]
        total_duration = (end_time - start_time).total_seconds()

        return round(total_duration, 3)  # rounded to 3 decimal places

    def _fix_wrong_key_locs(self, df: pd.DataFrame) -> pd.DataFrame | None:
        """
        This function find GPS points that belong to a key location, but the cluster that they form
        has duration less than 30 minutes. Those points are set to not belong to any key location.
        The function changes the belonging_key_loc column to NaN and the type column to NaN.
        That way, we can avoid situations where the system has incorrectly identified GPS points 
        as belonging to a key location because the user just passed (or stayed for a small amount of time) 
        near that key location. EXAMPLE: The user stayed for 50 min to key point A then moved to B key point 
        and stayed for 40 min, then moved again to C point and stayed for 120 min. Now the user from C wants to 
        go directly to A, but in the transition from C to A the user passed near B key point and the system generates some 
        GPS events in that time, the system used DBSCAN to identify key locations and identified those GPS points 
        as belonging to the cluster B, because DBSCAN does not include the time domain, those points are wrong and must
        be excluded from that key-point.

        Args:
            df: DataFrame with the GPS data
        Returns:
            Reconstructed dataframe with GPS data corrected
        """
        try:
            if df is None or df.empty:
                logger.warning("Empty DataFrame provided to _fix_wrong_key_locs")
                return df

            df = df.sort_values(by='timestamp_now')
            
            sub_route = []
            key_loc_point_tracked = []
            recording = False
            sub_route_to_fix_list = []
            for _, gps_event in df.iterrows():
                    
                    if np.isnan(gps_event['belonging_key_loc']) == False and recording is False:
                        sub_route.append(gps_event)
                        key_loc_point_tracked = [gps_event['latitude'], gps_event['longitude']]
                        recording = True
                    elif (
                            np.isnan(gps_event['belonging_key_loc']) == False and
                            gps_event['latitude'] == key_loc_point_tracked[0] and
                            gps_event['longitude'] == key_loc_point_tracked[1] and
                            recording is True
                    ):  
                        sub_route.append(gps_event)
                    elif (
                            np.isnan(gps_event['belonging_key_loc']) == False and
                            gps_event['latitude'] != key_loc_point_tracked[0] and
                            gps_event['longitude'] != key_loc_point_tracked[1] and
                            recording is True
                    ):
                        time_distance = self._compute_total_time_from_timestamps(pd.DataFrame(sub_route))
                        if time_distance <= 1800:  # 30 minutes
                            sub_route_to_fix_list.append(pd.DataFrame(sub_route))
                        sub_route = []
                        sub_route.append(gps_event)
                        key_loc_point_tracked = []
                        recording = False
            
            for sub_route_df in sub_route_to_fix_list:
                # Get indices from the original dataframe to update
                indices_to_fix = sub_route_df.index.tolist()
                df.loc[indices_to_fix, 'belonging_key_loc'] = np.nan
                df.loc[indices_to_fix, 'type'] = np.nan

            return df
        except Exception as e:
            logger.error(f"Error fixing wrong key locations: {e}")
            return None

    def _compute_main_gps_route(self, key_locs_coords: pd.DataFrame, df: pd.DataFrame, eps: int) -> pd.DataFrame | None:
        """
        Compute complete route by replacing GPS points near key locations with the key location data.
        By doing that, we can know in which timestamp the user was in a specific key location, this can make the
        analysis easier and accurate. Also note that by doing that we can remove the noise that happens when the user 
        is in a key-location, which means in a location, inside a building that GPS might not have good signal, and as a 
        result may produce inaccurate GPS events. This approach smooths the data and makes the proccess of forming the complete 
        route easier. We replace the latitude and longitude with the key location point's latitude and longitude that they belong to.
        Args:
            key_locs_coords: DataFrame with the key location information
            df: DataFrame with the GPS data
            eps: Epsilon value that has been used to identify the key locations (distance in meters that a point is considered to be in a key location)
        Returns:
            Reconstructed dataframe with the GPS data smoothed out
        """
        try:
            for _, key_loc_point in key_locs_coords.iterrows():
                near_gps_points = self._get_gps_points_near_key_loc(df, key_loc_point, eps)

                if near_gps_points.empty:
                    print(f"No GPS events near the key location: {key_loc_point}")
                    continue

                for idx in near_gps_points.index:
                    df.loc[idx, 'latitude'] = key_loc_point['latitude']
                    df.loc[idx, 'longitude'] = key_loc_point['longitude']
                    df.loc[idx, 'belonging_key_loc'] = key_loc_point['key_location_id']

                    # Each GPS point event that is close to the HOME location
                    # Is set as HOME, else it is set as NOT_IDENTIFIED
                    if key_loc_point['type'] == 'HOME':
                        df.loc[idx, 'type'] = 'HOME'
                    else:
                        df.loc[idx, 'type'] = 'NOT_IDENTIFIED'
            return df
        except Exception as e:
            logger.error(f"Error computing main GPS route: {e}")
            return None
    
    def _get_gps_points_near_key_loc(self, df: pd.DataFrame, key_loc_coords: pd.Series, eps: int) -> pd.DataFrame | None:
        """
        Get all GPS points that are within a certain distance from a key location.
        Args:
            key_loc_coords: Series with the key location coordinates
            eps: Epsilon value that has been used to identify the key locations (distance in meters that a point is considered to be in a key location)
        Returns:
            DataFrame with the GPS points that are near the key location
        """
        try:
            if key_loc_coords.empty:
                return df

            near_gps_rows = []

            for _, gps_event in df.iterrows():
                gps_event_lat = gps_event['latitude']
                gps_event_lon = gps_event['longitude']

                gps_point = (gps_event_lat, gps_event_lon)
                key_loc_point = (key_loc_coords['latitude'], key_loc_coords['longitude'])

                distance = haversine(gps_point, key_loc_point, unit=Unit.METERS)

                if distance <= eps and gps_event.notna().any():
                    near_gps_rows.append(gps_event)

            near_gps_points_df = pd.DataFrame(near_gps_rows, columns=df.columns)
            return near_gps_points_df
        except Exception as e:
            logger.error(f"Error getting GPS points near key location: {e}")
            return None

    def _identify_key_locations(self, df: pd.DataFrame, eps: int, samples: int, gps_points_sample_rate: int) -> pd.DataFrame | None:
        try:
            coords = df[['latitude', 'longitude']].map(radians).values  # Convert degrees to radians

            eps = eps / 6371000  # Earth's radius in meters (6371000 meters)

            db = DBSCAN(eps=eps, min_samples=samples, metric='haversine')
            labels = db.fit_predict(coords)

            # Construct key locations dataframe
            df['cluster'] = labels
            key_locs_dic = {
                cluster: {
                    'cluster_id': group['cluster'].unique()[0],
                    'mean_latitude': f"{group['latitude'].mean():.6f}",
                    'mean_longitude': f"{group['longitude'].mean():.6f}",
                    'points': group.drop(columns='cluster'),
                    'type': 'NOT_IDENTIFIED',
                }
                for cluster, group in df[df['cluster'] != -1].groupby('cluster')
            }
            key_locs_df = pd.DataFrame.from_dict(key_locs_dic, orient='index')

            # identify HOME location
            key_locs_df = self._find_home_key_location(key_locs_df, gps_points_sample_rate)

            # We only need some info for the rest of the analysis
            key_loc_info_df = key_locs_df[['cluster_id', 'mean_latitude', 'mean_longitude', 'type']].rename(columns={
                'cluster_id': 'key_location_id',
                'mean_latitude': 'latitude',
                'mean_longitude': 'longitude'
            })
            key_loc_info_df['latitude'] = key_loc_info_df['latitude'].astype(float)
            key_loc_info_df['longitude'] = key_loc_info_df['longitude'].astype(float)

            return key_loc_info_df
        except Exception as e:
            logger.error(f"Error identifying key locations: {e}")
            return None

    def _find_home_key_location(self, key_locs_df: pd.DataFrame, gps_points_sample_rate: int, home_period_valid_start_time=time(22, 0), home_period_valid_end_time=time(6, 0)) -> pd.DataFrame | None:
        max_percentage = 0
        home_idx = None
        for idx, key_loc in key_locs_df.iterrows():

            key_loc_points = key_loc['points'].copy()

            key_loc_points['timestamp_now'] = pd.to_datetime(key_loc_points['timestamp_now'])

            mask = (key_loc_points['timestamp_now'].dt.time >= home_period_valid_start_time) | \
                (key_loc_points['timestamp_now'].dt.time <= home_period_valid_end_time)

            night_points = key_loc_points[mask].sort_values(by='timestamp_now')
            duration_seconds = self._seconds_between_times(home_period_valid_start_time, home_period_valid_end_time)

            num_of_gps_events_home_period = duration_seconds / gps_points_sample_rate

            percentage = len(night_points) / num_of_gps_events_home_period * 100

            if max_percentage < percentage:
                max_percentage = percentage
                home_idx = idx

        if home_idx is not None:
            key_locs_df.at[home_idx, 'type'] = 'HOME'
        else:
            key_locs_df.at[home_idx, 'type'] = 'NOT_IDENTIFIED'

        return key_locs_df
    
    def _seconds_between_times(self, start_time: time, end_time: time) -> int:
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M:%S').time()

        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%H:%M:%S').time()

        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)

        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)  # Handle overnight intervals

        return (end_datetime - start_datetime).total_seconds()

    def _clean_gps_data(self, gps_df: pd.DataFrame, accuracy_excl: int) -> pd.DataFrame | None:
        """
        This function cleans the GPS data.
        Args:
            gps_data_df: DataFrame with the GPS data
        Returns:
            DataFrame with the cleaned GPS data
        """
        try:
            # Remove rows with missing values
            gps_df = gps_df.dropna(subset=['latitude', 'longitude', 'accuracy', 'gps_event_id', 'user_uid', 'timestamp_now'])

            # Remove rows that have accuract less than the accuracy_excl
            gps_df = gps_df[gps_df['accuracy'] <= accuracy_excl]

            # Remove duplicates
            gps_df = gps_df.drop_duplicates(subset=['id', 'timestamp_now'])

            # Check if we have at least 16 hours of data
            if not self._has_16_hours_in_total(gps_df):
                logger.info("Not enough GPS data to analyze (less than 16 hours).")
                return None
            
            # Check if we have GPS data at least every <threshold> seconds
            threshold = 1680 # 28 minutes
            if not self._has_consistent_GPS_data(gps_df, threshold):
                logger.info(f"GPS data are not consistent, not enough data to analyze (trhreashold is {threshold} seconds).")
                return None
            
            # Find clusters of same GPS events
            clusters_of_same_gps_events = self._find_clusters_of_same_GPS_events(gps_df)

            if clusters_of_same_gps_events is None:
                logger.error("Error finding clusters of same GPS events.")
                return None
            
            # transform those clusters that have identical GPS info data
            gps_df = self._transform_duplicate_gps_events(gps_df, clusters_of_same_gps_events)

            if gps_df is None:
                logger.error("No GPS data found after transforming duplicate GPS events.")
                return None

            # Remove outliers using the z-score
            gps_df = self._remove_outliers_using_z_score(gps_df, threshold=15000)

            if gps_df is None:
                logger.error("No GPS data found after removing outliers using the z-score.")
                return None

            # Remove outliers using the nearest-any-neighbor algorithm
            gps_df = self._remove_outliers_near_gps_points(gps_df, 500) 

            if gps_df is None:
                logger.error("No GPS data found after removing outliers near GPS points.")
                return None

            return gps_df
        except Exception as e:
            logger.error(f"Error cleaning GPS data: {e}")
            return None
    
    def _remove_outliers_near_gps_points(self, df: pd.DataFrame, min_distance: int) -> pd.DataFrame | None:
        """
        Check each GPS point and see if it has <= min_distance from at least one GPS point.
        That GPS point does not need to be (timely) the next or the previous one, it can be any GPS point.
        - If it has > min_distance from any GPS point, then remove it from the dataframe
        - else keep it

        Args:
            df: DataFrame with the GPS data
            min_distance: Minimum distance in meters between a GPS point and its neighbors
        Returns:
            DataFrame with the outliers removed
        """
        try:
            if df.shape[0] < 2:
                return df

            coords = df[['latitude', 'longitude']].to_numpy()

            coords_rad = np.radians(coords)

            dist_matrix = haversine_distances(coords_rad) * 6371000  # in meters 

            # For each point, check if there's at least one other point within the threshold
            np.fill_diagonal(dist_matrix, np.inf)  # Ignore self-distance
            has_neighbor = (dist_matrix < min_distance).any(axis=1)

            # Keep only those with at least one close neighbor
            cleaned_df = df[has_neighbor].reset_index(drop=True)

            return cleaned_df
        except Exception as e:
            logger.error(f"Error removing outliers near GPS points: {e}")
            return None
    
    def _remove_outliers_using_z_score(self, df: pd.DataFrame, threshold: int) -> pd.DataFrame | None:
        """
        This function removes the outliers from the dataframe using the z-score.
        Args:
            df: DataFrame with the GPS data
        Returns:
            DataFrame with the outliers removed
        """
        try:
            # Calculate distances from median
            coords = df[['latitude', 'longitude']].values
            median = np.median(coords, axis=0)
            distances = np.linalg.norm(coords - median, axis=1)

            # Median Absolute Deviation (MAD)
            mad = np.median(np.abs(distances - np.median(distances)))

            # Calculate modified Z-score
            modified_z_scores = 0.6745 * (distances - np.median(distances)) / mad

            # Identify outliers
            is_outlier = modified_z_scores > threshold

            # Split into clean data and outliers
            clean_data = df[~is_outlier].copy()
            outliers = df[is_outlier].copy()

            # Apply clean data to the original dataframe
            df = clean_data

            return df
        except Exception as e:
            logger.error(f"Error removing outliers using z-score: {e}")
            return None


    def _find_clusters_of_same_GPS_events(self, df: pd.DataFrame) -> List[List[pd.Series]]:
        try:
            df = df.sort_values(by='timestamp_now')

            clusters = []
            current_cluster = []

            prev_gps_evt = df.iloc[0]
            current_cluster.append(prev_gps_evt)

            for _, gps_event in df.iloc[1:].iterrows():
                if prev_gps_evt['latitude'] == gps_event['latitude'] and prev_gps_evt['longitude'] == gps_event['longitude']:
                    current_cluster.append(gps_event)
                else:
                    if len(current_cluster) >= 2:
                        clusters.append(current_cluster)
                    current_cluster = [gps_event]
                prev_gps_evt = gps_event

            if len(current_cluster) >= 2:
                clusters.append(current_cluster)

            return clusters
        except Exception as e:
            logger.error(f"Error finding clusters of same GPS events: {e}")
            return None
    
    def _create_cluster_unique_id(self, df: pd.DataFrame) -> str | None:

        """
        Generates a 30-character unique ID using characters from a randomly selected GPS events in the dataset
        This is used to identify the GPS events that are part of the same cluster

        Args:
            df: DataFrame with the GPS data
        
        Returns:
            String with the unique ID
        """

        try:
            # Remove NaN values in 'gps_event_id' column
            # because it will cause issues when generating a unique ID
            df = df.dropna(subset=['gps_event_id'])

            if len(df) == 0:
                print("No GPS events found to create a unique ID.")
                return None

            random_event = df.sample(1).iloc[0]
            random_id = random_event['gps_event_id']
            
            unique_id = ''.join(np.random.choice(list(random_id), size=30))

            return unique_id
        except Exception as e:
            logger.error(f"Error creating unique UID: {e}")
            return None

    def _construct_median_dataframe(self, df: pd.DataFrame, main_point: list) -> pd.DataFrame:
        """
        Function to construct a dataframe that represents a GPS event with median values of the whole dataframe;
        this dataframe will have the same columns as the main dataframe (that contains the GPS event points).
        Args:
            main_point: List with the GPS points (longitude, latitude) of the main point
            df: DataFrame with the GPS event points
        Returns:
            DataFrame with the median values of the whole dataframe
        """

        try:
            # Preparation
            df['timestamp_now'] = pd.to_datetime(df['timestamp_now'])
            df = df.sort_values(by='timestamp_now')

            # Median values
            median_timestamp = df['timestamp_now'].median()
            median_accuracy = df['accuracy'].median()
            median_bearing = df['bearing'].median()
            median_speed = df['speed'].median()
            median_speed_accuracy_meters_per_second = df['speed_accuracy_meters_per_second'].median()

            # New values
            longitude = main_point[1]
            latitude = main_point[0]

            rand_UID = self._create_cluster_unique_id(df)
            
            if rand_UID is None:
                logger.error("Cannot create a unique ID, returning an empty DataFrame.")
                return None

            # Construct the median key location dataframe
            median_gps_event_df = pd.DataFrame([{
                'id': 0,
                'gps_event_id': rand_UID,
                'latitude': latitude,
                'longitude': longitude,
                'timestamp_now': median_timestamp,
                'accuracy': median_accuracy,
                'bearing': median_bearing,
                'speed': median_speed,
                'speed_accuracy_meters_per_second': median_speed_accuracy_meters_per_second
            }])

            return median_gps_event_df
        except Exception as e:
            logger.error(f"Error constructing median dataframe: {e}")
            return None

    def _transform_duplicate_gps_events(self, df: pd.DataFrame, clusters: List[List[pd.Series]]) -> pd.DataFrame | None:
        """
        This function transforms the duplicate GPS events into a single event with median values of the whole dataframe.
        Args:
            clusters: List of lists of clusters of same GPS events
        Returns:
            DataFrame with the transformed GPS event points
        """
        try:
            df = df.sort_values(by='timestamp_now')

            ids_to_remove = set()
            new_rows = []

            for cluster in clusters:
                cluster_df = pd.DataFrame(cluster)

                # Get the gps_event_ids from the cluster
                cluster_ids = cluster_df['gps_event_id'].tolist()
                ids_to_remove.update(cluster_ids)

                first_point = cluster[0]
                representative_point = [first_point['latitude'], first_point['longitude']]

                new_event = self._construct_median_dataframe(cluster_df, representative_point)

                if new_event is not None:
                    new_rows.append(new_event) 
                else:
                    logger.error(f"Error occurred while constructing the median dataframe for the representative point {representative_point}.")
                    continue

            df =  df[~df['gps_event_id'].isin(ids_to_remove)]

            # Add the new representative rows to the dataframe
            if new_rows:
                if len(new_rows) == 1:
                    new_events_df = pd.DataFrame(new_rows[0])
                else:
                    new_events_df = pd.concat([pd.DataFrame(r) for r in new_rows])

                df = pd.concat([df, new_events_df], ignore_index=True)

            return df.sort_values(by='timestamp_now')
        except Exception as e:
            logger.error(f"Error transforming duplicate GPS events: {e}")
            return None

    def _has_16_hours_in_total(self, df: pd.DataFrame) -> bool:
        df['timestamp_now'] = pd.to_datetime(df['timestamp_now'])
        start = df['timestamp_now'].min()
        end = df['timestamp_now'].max()
        return (end - start).total_seconds() >= 16 * 3600
    
    def _has_consistent_GPS_data(self, df: pd.DataFrame, threshold: int) -> bool:
        df['timestamp_now'] = pd.to_datetime(df['timestamp_now'])
        df = df.sort_values(by='timestamp_now')
        time_diffs = df['timestamp_now'].diff().dt.total_seconds().fillna(0)

        if (time_diffs <= threshold).all():
            return True
        else:
            logger.info(f"GPS events that not meet the criteria (time distance from previous):\n {time_diffs[time_diffs > threshold]}")
            return False
        
    def _calc_call_data(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> dict | None:
        """
        This function calculates the call analysis.
        Args:
            None
        Returns:
            Dictionary with the call analysis
        """
        try:
            # Fetch the call data from the local database for the current day analyzed
            call_data = self.db_service.get_call_data(user_uid, start_datetime, end_datetime)

            if call_data is None:
                logger.info("No call data found.")
                return None
            
            # Convert list of objects to DataFrame with proper column names
            call_data_df = pd.DataFrame([
                {
                    'id': event.id,
                    'call_event_id': event.call_event_id,
                    'user_uid': event.user_uid,
                    'call_date': event.call_date,
                    'call_type': event.call_type,
                    'call_description': event.call_description,
                    'call_duration_sec': event.call_duration_sec
                }
                for event in call_data
            ])
            
            if call_data_df.empty:
                logger.info("No call data found.")
                return None

            call_data_df.sort_values(by='call_date', inplace=True)
            
            missed_call_ratio = self._calculate_missed_call_ratio(call_data_df)
            compute_night_call_ratio = self._calculate_night_call_ratio(call_data_df)
            compute_day_call_ratio = self._calculate_day_call_ratio(call_data_df)
            compute_avg_call_duration = self._calculate_avg_call_duration(call_data_df)
            compute_total_calls_in_a_day = self._calculate_total_calls_in_a_day(call_data_df)

            extract_user_call_insights = {
                "missed_call_ratio": missed_call_ratio,
                "night_call_ratio": compute_night_call_ratio,
                "day_call_ratio": compute_day_call_ratio,
                "avg_call_duration": compute_avg_call_duration,
                "total_calls_in_a_day": compute_total_calls_in_a_day
            }

            return extract_user_call_insights
        except Exception as e:
            logger.error(f"Error calculating call analysis: {e}")
            return None
    
    def _calculate_missed_call_ratio(self, df: pd.DataFrame) -> float:
        """
        This function calculates the missed call ratio (exclude VoIP calls).
        Args:
            df: DataFrame with the call data
        Returns:
            Float with the missed call ratio
        """
        try:
            df = df[df['call_description'] != 'VoIP_CALL_THIRD_PARTY_APP']
            total_calls = len(df)
            missed_calls = df['call_description'].str.upper().str.contains('MISSED').sum()
            return missed_calls / total_calls if total_calls > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating missed call ratio: {e}")
            return None

    def _calculate_night_call_ratio(self, df: pd.DataFrame) -> float:
        """
        This function calculates the night call ratio.
        Calls before 5 AM or after 10 PM are considered night calls.
        Args:
            df: DataFrame with the call data
        Returns:
            Float with the night call ratio
        """
        try:
            df['call_hour'] = pd.to_datetime(df['call_date']).dt.hour
            night_calls = df['call_hour'].apply(lambda x: 1 if x < 5 or x >= 22 else 0).sum()
            return (night_calls / len(df) if len(df) > 0 else 0) * 100
        except Exception as e:
            logger.error(f"Error calculating night call ratio: {e}")
            return None
    
    def _calculate_day_call_ratio(self, df: pd.DataFrame) -> float:
        """
        This function calculates the day call ratio.
        Calls between 6 AM and 10 PM are considered day calls.
        Args:
            df: DataFrame with the call data
        Returns:
            Float with the day call ratio
        """
        try:
            df['call_hour'] = pd.to_datetime(df['call_date']).dt.hour
            day_calls = df['call_hour'].apply(lambda x: 1 if 6 <= x < 22 else 0).sum()
            return (day_calls / len(df) if len(df) > 0 else 0) * 100
        except Exception as e:
            logger.error(f"Error calculating day call ratio: {e}")
            return None

    def _calculate_avg_call_duration(self, df: pd.DataFrame) -> float:
        """
        This function calculates the average call duration (exclude VoIP calls).
        Args:
            df: DataFrame with the call data
        Returns:
            Float with the average call duration
        """
        try:
            df = df[df['call_description'] != 'VoIP_CALL_THIRD_PARTY_APP']
            return df['call_duration_sec'].mean() # it is in seconds already
        except Exception as e:
            logger.error(f"Error calculating average call duration: {e}")
            return None
    
    def _calculate_total_calls_in_a_day(self, df: pd.DataFrame) -> int:
        """
        This function calculates the total calls in a day.
        Args:
            df: DataFrame with the call data
        Returns:
            Int with the total calls in a day
        """
        try:
            return len(df) # with VoIP calls included
        except Exception as e:
            logger.error(f"Error calculating total calls in a day: {e}")
            return None

    def _calc_activity_data(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> dict | None:
        """
        This function calculates the activity analysis.
        Args:
            None
        Returns:
            Dictionary with the activity analysis
        """
        try:
            # Fetch the activity data from the local database for the current day analyzed
            activity_data = self.db_service.get_activity_data(user_uid, start_datetime, end_datetime)

            if activity_data is None:
                logger.info("No activity data found.")
                return None
            
            # Convert list of objects to DataFrame with proper column names
            activity_data_df = pd.DataFrame([
                {
                    'id': event.id,
                    'user_activity_event_id': event.user_activity_event_id,
                    'user_uid': event.user_uid,
                    'timestamp': event.timestamp,
                    'activity_type': event.activity_type,
                    'confidence': event.confidence
                }
                for event in activity_data
            ])
            
            if activity_data_df.empty:
                logger.info("No activity data found.")
                return None

            activities_percentages = self._calculate_percentages(
                ["still", "tilting", "unknown", "on_foot", "in_vehicle", "walking", "running", "on_bicycle"], 
                activity_data_df['activity_type'].tolist()
            )

            activity_switching_frequency = self._calculate_activity_switching_frequency(activity_data_df)

            daily_active_minutes = self._calculate_daily_active_minutes(activity_data_df, ["on_foot", "in_vehicle", "walking", "running", "on_bicycle"])

            activity_entropy = self._calculate_activity_entropy(activity_data_df)

            inactivity_percentage = self._calculate_inactivity_percentage(activity_data_df)

            activity_percentages_per_day_sections = self._calculate_activity_percentages_per_day_sections(activity_data_df)

            activity_analysis = {
                "activities_percentages": activities_percentages,
                "activity_switching_frequency": activity_switching_frequency,
                "daily_active_minutes": daily_active_minutes,
                "activity_entropy": activity_entropy,
                "inactivity_percentage": inactivity_percentage,
                "activity_percentages_per_day_sections": activity_percentages_per_day_sections
            }

            return activity_analysis
        except Exception as e:
            logger.error(f"Error calculating activity analysis: {e}")
            return None

    def _calculate_activity_percentages_per_day_sections(self, df: pd.DataFrame) -> pd.DataFrame | None:
        """
        This function calculates the activity percentages per day sections.
        Args:
            df: DataFrame with the activity data
        Returns:
            Dataframe with the activity percentages per day sections
        """ 
        try:
            df = df.sort_values(by='timestamp')
            day_sections = self._define_day_sections()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour

            # Create a new column for the day section
            def get_day_section(row):
                hour = row['hour']
                for section, (start, end) in day_sections.items():
                    if start <= hour < end:
                        return section
                return 'Unknown'

            df['day_section'] = df.apply(get_day_section, axis=1)

            # Group by day section and activity type, then count occurrences
            activity_distribution = df.groupby(['day_section', 'activity_type']).size().unstack(fill_value=0)

            # Calculate percentages
            activity_distribution_percentage = activity_distribution.div(activity_distribution.sum(axis=1), axis=0) * 100

            return activity_distribution_percentage.sort_index()
        except Exception as e:
            logger.error(f"Error calculating activity percentages per day sections: {e}")
            return None

    def _define_day_sections(self) -> dict:
        """
        This function defines the day sections.
        Args:
            None
        Returns:
            Dictionary with the day sections and their corresponding hours
        """
        return {
            'night': (0, 6),
            'morning': (6, 12),
            'afternoon': (12, 18),
            'evening': (18, 22),
            'Late Evening': (22, 24)
        }
    
    def _calculate_inactivity_percentage(self, df: pd.DataFrame, start_hour: int = 10, end_hour: int = 22) -> float | None:
        """
        This function calculates the inactivity percentage, by providing 
        a representative final score for the inactivity during the active hours.
        Args:
            df: DataFrame with the activity data
        Returns:
            Float with the inactivity percentage (ex. 66.35%)
        """
        try:
            df = df.sort_values(by='timestamp')
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['date'] = df['timestamp'].dt.date

            filtered_df = df[df['activity_type'] != 'unknown']

            day_window = filtered_df[(filtered_df['hour'] >= start_hour) & (filtered_df['hour'] < end_hour)]
            activity_distribution = day_window.groupby(['user_uid', 'activity_type']).size().unstack(fill_value=0)

            activity_distribution_percentage = activity_distribution.div(activity_distribution.sum(axis=1), axis=0) * 100

            return activity_distribution_percentage['still'].mean() if 'still' in activity_distribution_percentage.columns else 0.0
        except Exception as e:
            logger.error(f"Error calculating inactivity percentage: {e}")
            return None

    def _calculate_activity_entropy(self, df: pd.DataFrame) -> float | None:
        """
        This function calculates the activity entropy.
        Args:
            df: DataFrame with the activity data
        Returns:
            Float with the activity entropy
        """
        try:
            df= df.sort_values(by='timestamp')
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            total_entropy = 0.0

            for date, group in df.groupby('date'):
                filtered = group[group['activity_type'] != 'unknown']
                if filtered.empty:
                    day_entropy = 0.0
                else:
                    activity_counts = filtered['activity_type'].value_counts()
                    probs = activity_counts / activity_counts.sum()
                    day_entropy = round(entropy(probs, base=2), 3)
                total_entropy += day_entropy

            return total_entropy
        except Exception as e:
            logger.error(f"Error calculating activity entropy: {e}")
            return None

    def _calculate_daily_active_minutes(self, df: pd.DataFrame, activity_types_labels: list) -> int | None:
        """
        This function calculates the daily active minutes.
        Args:
            df: DataFrame with the activity data
            activity_types_labels: List of activity types to consider
        Returns:    
            Integer with the daily active minutes
        """
        try:
            df = df.sort_values(by='timestamp')
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["date"] = df["timestamp"].dt.date

            total_active_minutes = 0
            for _, group in df.groupby("date"):
                active_group = group[group["activity_type"].isin(activity_types_labels)]
                if active_group.empty:
                    continue
                active_minutes_count = active_group["timestamp"].dt.floor("min").nunique()
                total_active_minutes += active_minutes_count

            return total_active_minutes
        except Exception as e:
            logger.error(f"Error calculating daily active minutes: {e}")
            return None

    def _calculate_activity_switching_frequency(self, df: pd.DataFrame) -> int | None:
        """
        This function calculates the switching frequency.
        Args:
            df: DataFrame with the activity data
        Returns:
            Integer with the total number of switches
        """
        try:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            total_switches = 0

            for _, group in df.groupby('date'):
                group = group.sort_values(by='timestamp')
                activity_sequence = group['activity_type'].tolist()
                switches = sum(
                    1 for i in range(1, len(activity_sequence))
                    if activity_sequence[i] != "unknown" and activity_sequence[i] != activity_sequence[i-1]
                )
                total_switches += switches

            return total_switches
        except Exception as e:
            logger.error(f"Error calculating activity switching frequency: {e}")
            return None
    
    def _calculate_percentages(self, categories: list, decisions: list) -> dict | None:

        """
        Given a list of categories and a list of decision made for each category,
        the function will return a dictionary with the percentage of each category.

        Args:
            categories: list - The list of categories
            decisions: list - The list of decisions made for each category

        Returns:
            dict - The dictionary with the percentage of each category
        """

        total_count = len(decisions)

        if total_count == 0:
            print("No decisions found.")
            return None

        decision_counts = {}
        for decision in decisions:
            if decision in categories:
                if decision not in decision_counts:
                    decision_counts[decision] = 0
                decision_counts[decision] += 1

        percentages = {category: (decision_counts.get(category, 0) / total_count * 100) for category in categories}
        # Debug: Log the calculated percentages  
        logger.info(f"Calculated percentages: {percentages}")
        return percentages

    def _calc_app_usage(self, user_uid: str, start_datetime: datetime, end_datetime: datetime, top_n_apps: int = 3) -> pd.DataFrame | None:
        """
        This function calculates the app usage.
        Args:
            user_uid: User ID
            start_datetime: Start datetime
            end_datetime: End datetime
            top_n_apps: Number of top apps to return (default is 3)
        Returns:
            DataFrame with the top n apps package names and the total time spent on each app
        """
        try:
            app_usage_list = self.db_service.get_app_usage(user_uid, start_datetime, end_datetime)
            if app_usage_list is None or len(app_usage_list) == 0:
                logger.info("No app usage found.")
                return None
            
            # Convert list of database rows to DataFrame with proper column names
            app_usage_df = pd.DataFrame([
                {
                    'app_name': row.app_name,
                    'time_used': row.time_used
                }
                for row in app_usage_list
            ])
            
            # Calculate the app usage   
            top_apps = app_usage_df.groupby('app_name')['time_used'].sum().reset_index()

            # Sort by duration and get the top n apps
            top_apps = top_apps.sort_values(by='time_used', ascending=False).head(top_n_apps)

            return top_apps
        except Exception as e:
            logger.error(f"Error calculating app usage: {e}")
            return None

    def _calc_device_drop_events(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> int | None:
        """
        This function calculates the device drop events.
        Args:
            user_uid: User ID
            start_datetime: Start datetime
            end_datetime: End datetime
        Returns:
            Dictionary with the device drop events
        """

        try:
            # Fetch the device drop events from the local database
            device_drop_events_list = self.db_service.get_device_drop_events(user_uid, start_datetime, end_datetime)

            if device_drop_events_list is None or len(device_drop_events_list) == 0:
                logger.info("No device drop events found.")
                return None
            
            # Count the number of device drop events
            device_drop_events_count = len(device_drop_events_list)
            
            return device_drop_events_count
        except Exception as e:
            logger.error(f"Error calculating device drop events: {e}")
            return None

    def _calc_low_light_day_time(self, user_uid: str, start_datetime: datetime, end_datetime: datetime) -> int:
        """
        This function calculates the low light day time.
        Args:
            user_uid: User ID
            start_datetime: Start datetime
            end_datetime: End datetime
        Returns:
            Dictionary with the low light day time
        """

        try:
            # Fetch the low light data from the local database
            low_light_data = self.db_service.get_low_light_data(user_uid, start_datetime, end_datetime)
            if low_light_data is None or len(low_light_data) == 0:
                logger.info("No low light data found.")
                return 0
            
            # Convert list of objects to DataFrame with proper column names
            low_light_data_df = pd.DataFrame([
                {
                    'id': event.id,
                    'low_light_event_id': event.low_light_event_id,
                    'user_uid': event.user_uid,
                    'start_time': event.start_time,
                    'end_time': event.end_time,
                    'duration_ms': event.duration_ms,
                    'low_light_threshold_used': event.low_light_threshold_used
                }
                for event in low_light_data
            ])
            
            # Calculate the low light day time, using the field 'duration_ms' for every event
            low_light_day_time_sec = low_light_data_df['duration_ms'].sum() / 1000.0  # Convert from milliseconds to seconds
            
            return int(low_light_day_time_sec) # in seconds
        except Exception as e:
            logger.error(f"Error calculating low light day time: {e}")
            return 0

    def _calc_screen_time_stat(self, user_uid, start_date_time, end_date_time) -> list | None:
        """
        Calculate the total screen time for a user in a given date range.
        The way this calculation is performed is the following:
        - We use screen time events but also sleep events.
        - From the sleep events we only need the screenOnDuration.
        - Mostly we use the screen time events, but if there are no screen time events,
          for a given time period we use the sleep events to calculate the total screen time.
        - This approach helps us to have a more accurate calculation of the total screen time;
          since the screen time events are not always available, also we cannot rely only on
          the sleep events because sometimes they are not well recorded from the UsageStatsManager.
        Args:
            user_uid: User ID
            start_date_time: Start datetime
            end_date_time: End datetime
        Returns:
            Total screen time for the user in the given time range
        """

        try:
            if start_date_time is None or end_date_time is None:
                raise ValueError("start_date_time and end_date_time must not be None")

            # Fetch screen time events for the user for the given time range
            screen_time_events_df = self.db_service.get_screen_time_events_of_a_user(user_uid, start_date_time, end_date_time)
            if screen_time_events_df is None or screen_time_events_df.empty:
                logger.info(f"No screen time events found for user {user_uid} in the given time range.")
                return None
            
            # Fetch sleep events for the user for the given time range
            sleep_events_df = self.db_service.get_sleep_data_of_a_user(user_uid, start_date_time, end_date_time)
            if sleep_events_df is None or sleep_events_df.empty:
                logger.info(f"No sleep events found for user {user_uid} in the given time range.")
                return None

            # Fetch unlock events for the user for the given time range
            unlock_events_list = self.db_service.get_device_unlock_events_of_a_user(user_uid, start_date_time, end_date_time)
            if unlock_events_list is None:
                logger.info(f"No unlock events found for user {user_uid} in the given time range.")
                return None
            
            # Convert list of objects to DataFrame with proper column names
            unlock_events_df = pd.DataFrame([
                {
                    'id': event.id,
                    'device_unlock_event_id': event.device_unlock_event_id,
                    'user_uid': event.user_uid,
                    'timestamp': event.timestamp
                }
                for event in unlock_events_list
            ])

            # Combine the screen time events with the unlock events to get more accurate screen time
            unlock_screen_events_df = self._combine_unlock_screen_events(unlock_events_df, screen_time_events_df, max_time_difference_sec=3)

            broadcast_intervals = [
                (row['start_time'], row['end_time'])
                for _, row in unlock_screen_events_df.iterrows()
                if pd.notnull(row['start_time']) and pd.notnull(row['end_time']) and (row['end_time'] > row['start_time'])
            ]
            
            usage_intervals = []
            for _, row in sleep_events_df.iterrows():
                duration_ms = int(row['screenOnDuration'])
                if pd.notnull(duration_ms) and duration_ms > 0:
                    start = row['timestamp_now'] - timedelta(milliseconds=duration_ms)
                    end = row['timestamp_now']
                    if end > start:
                        usage_intervals.append((start, end))
            
            hybrid_intervals = self._merge_intervals(broadcast_intervals, usage_intervals)

            total_screen_on_time_sec = sum((end - start).total_seconds() for start, end in hybrid_intervals)

            logger.info(f"Total screen-on time (seconds): {total_screen_on_time_sec}, (minutes): {total_screen_on_time_sec / 60}, (hours): {total_screen_on_time_sec / 3600}")

            return [total_screen_on_time_sec, hybrid_intervals]
        except Exception as e:
            logger.error(f"Error calculating total screen time for user {user_uid}: {e}")
            return None

    def _calc_screen_time_in_circadian_hours(self, screen_sessions, total_screen_on_time_sec) -> list[dict] | None:
        """
        This function calculates the screen time in circadian hours.
        Args:
            screen_sessions: List of screen sessions
            total_screen_on_time_sec: Total screen on time in seconds
        Returns:
            List of dictionaries with the screen time in circadian hours
        """

        try:
            df = pd.DataFrame(screen_sessions, columns=['time_start', 'time_end'])

            # Ensure datetime format
            df['time_start'] = pd.to_datetime(df['time_start'])
            df['time_end'] = pd.to_datetime(df['time_end'])

            # Calculate duration per session
            df['duration'] = (df['time_end'] - df['time_start']).dt.total_seconds()

            # Assign each session to a day section based on the start time
            day_sections = self._define_day_sections()

            def _get_day_section(hour):
                for section, (start, end) in day_sections.items():
                    if start <= hour < end:
                        return section
                return 'Unknown'

            df['day_section'] = df['time_start'].dt.hour.apply(_get_day_section)

            # Group and compute total duration per section
            screen_time_per_section = df.groupby('day_section')['duration'].sum().reset_index()

            # Compute percentages
            screen_time_per_section['percentage'] = (screen_time_per_section['duration'] / total_screen_on_time_sec * 100).round(2)

            return screen_time_per_section.sort_values(by='day_section').to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error calculating screen time in circadian hours: {e}")
            return None

    def _define_day_sections(self):
        return {
            'night': (0, 6),
            'morning': (6, 12),
            'afternoon': (12, 18),
            'evening': (18, 22),
            'Late Evening': (22, 24)
        }

    def _combine_unlock_screen_events(self, unlock_events_df, screen_time_events_df, max_time_difference_sec=3):
        """
        Find and keep screen time events that occurred within [max_time_difference_sec] seconds of an unlocked event
        Args:
            unlock_events_df: DataFrame of unlock events
            screen_time_events_df: DataFrame of screen time events
            max_time_difference_sec: Maximum time difference in seconds between an unlock event and a screen time event (default is 3 seconds)
        Returns:
            DataFrame of screen time events that occurred within [max_time_difference_sec] seconds of an unlocked event
        """

        try:
            unlock_df = unlock_events_df.copy()
            screen_df = screen_time_events_df.copy()

            # Ensure datetime format
            unlock_df['timestamp'] = pd.to_datetime(unlock_df['timestamp'])
            screen_df['start_time'] = pd.to_datetime(screen_df['start_time'])

            # Rename for clarity
            unlock_df = unlock_df.rename(columns={'timestamp': 'unlock_time'})
            # screen_df = screen_df.rename(columns={'start_time': 'time_start'})

            # Cross join 
            merged = unlock_df.merge(screen_df, how='cross')

            # Time difference
            merged['time_diff'] = (merged['start_time'] - merged['unlock_time']).dt.total_seconds().abs()

            # Filter
            matched = merged[merged['time_diff'] <= max_time_difference_sec]

            return matched.sort_values(by='unlock_time')
        except Exception as e:
            logger.error(f"Error combining unlock and screen events: {e}")
            return pd.DataFrame()


    def _merge_intervals(self, primary, fallback):
        """
        Merge intervals from two lists, prioritizing the primary list.
        Args:
            primary: List of primary intervals (tuples of start and end datetime)
            fallback: List of fallback intervals (tuples of start and end datetime)
        Returns:
            The merged list of intervals
        """

        all_intervals = primary.copy()

        # Add non-overlapping fallback intervals
        for f_start, f_end in fallback:
            overlaps = any(p_start < f_end and f_start < p_end for p_start, p_end in all_intervals)
            if not overlaps:
                all_intervals.append((f_start, f_end))

        # Sort and merge overlapping intervals
        all_intervals.sort()
        merged = []
        for interval in all_intervals:
            if not merged:
                merged.append(interval)
            else:
                last_start, last_end = merged[-1]
                current_start, current_end = interval
                if current_start <= last_end:
                    # Merge
                    merged[-1] = (last_start, max(last_end, current_end))
                else:
                    merged.append(interval)

        return merged

    def _merge_sleep_windows(self, sleep_windows_lc, max_gap=50):

        """
        This function merges sleep windows that are close to each other.
        Args:
            sleep_windows_lc: List of sleep windows
            max_gap: Maximum gap between sleep windows to merge them
        Returns:
            List of merged sleep windows
        """

        # Sort sleep segments by start time
        sleep_windows_lc = sorted(sleep_windows_lc, key=lambda x: x['start'])
        merged = []

        # Initialize current segment with the first segment
        current = sleep_windows_lc[0].copy()
        current['actual_duration'] = current['duration']

        for nxt in sleep_windows_lc[1:]:
            gap = (nxt['start'] - current['end']).total_seconds() / 60.0
            if gap < max_gap:
                # Merge the segment by extending the end time and updating duration
                current['end'] = nxt['end']
                current['duration'] = (current['end'] - current['start']).total_seconds() / 60.0
                current['actual_duration'] += nxt['duration']
            else:
                merged.append(current)
                current = nxt.copy()
                # Initialize actual_duration for the new segment
                current['actual_duration'] = current['duration']
        merged.append(current)
        return merged

    def calc_and_store_typing_stats(self, user_uid: str, daily_analysis_id: int, day_to_analyze: str) -> bool:

        """
        This function will calculate the high-level typing metrics for a particular day for a particular user.
        This includes:
        1) Calculating the mean and std for each high-level metric (ex. Pressure Intensity, Cognitive Processing Efficiency, etc.)
        2) Calculating the percentage distribution of cognitive decisions (ex. Critical: 10%, Very Bad: 10%, Normal: 50%, Very Good: %10, Excellent: %20)

        Args:
            user_uid: str - The user's unique identifier
            daily_analysis_id: int - The ID of the daily analysis event that this stats are about
            day_to_analyze: str - The day of the analysis (day that is analyzed)

        Returns:
            False: If the stats could not be calculated
            True: If the stats were calculated successfully
        """

        HIGH_LEVEL_METRICS_TABLE_NAMES = [
            'Pressure_Intensity_Data',
            'Cognitive_Processing_Efficiency_Data',
            'Cognitive_Processing_Index_Data',
            'Correction_Efficiency_Data',
            'Effort_To_Output_Ratio_Data',
            'Net_Production_Rate_Data',
            'Pause_To_Production_Ratio_Data',
            'Typing_Rhythm_Stability_Data',
        ]

        DECISION_CATEGORIES = ["Critical", "Very Bad", "Normal", "Very Good", "Excellent"]

        # SUPABASE_COLUMN_KEYS = [
        #     "std_pi", "mean_pi", "std_cpe", "mean_cpe", "std_cpi", "mean_cpi",
        #     "std_ce", "mean_ce", "std_eto", "mean_eto", "std_npr", "mean_npr",
        #     "std_ppr", "mean_ppr", "std_trs", "mean_trs"
        # ] # Columns of the table in Supabase (Daily_Analysis_Typing_Data)

        results_list = []
        session_decision_set = set() # This will hold the (unique values) sessions id's together with the cognitive decision made for them

        logger.info(f"\033[92m\n\n-----------Calculating typing stats for user {user_uid} for day {day_to_analyze}-----------\033[0m\n\n")

        try:
            # For each high-level metric, calculate the mean and std for the current day
            for metric_table_name in HIGH_LEVEL_METRICS_TABLE_NAMES:

                typing_sessions_decisions_info = self.supabase_service.retrieve_cognitive_info_of_typing_sessions(metric_table_name, user_uid, day_to_analyze)

                if not typing_sessions_decisions_info:
                    logger.warning(f"No data retrieved for metric {metric_table_name}")
                    continue
                
                metric_stats = self._calculate_metric_statistics(typing_sessions_decisions_info, metric_table_name)
                if metric_stats:
                    results_list.append(metric_stats)

                # Collect cognitive decisions
                for session in typing_sessions_decisions_info:
                    if "cognitive_decision" in session and "session_uid" in session:
                        session_decision_set.add((session["session_uid"], session["cognitive_decision"]))
            
            if not session_decision_set:
                logger.error(f"No typing sessions found for user {user_uid} on {day_to_analyze}")
                return False

            # Calculate decision distribution percentages
            percentages = self._calculate_percentages(
                DECISION_CATEGORIES,
                [decision[1] for decision in session_decision_set]
            )

            if not percentages:
                logger.error(f"No cognitive decisions found for user {user_uid} on {day_to_analyze}")
                return False

            # Calculate the total typing cognitive score
            total_typing_cognitive_score = self._calculate_total_typing_cognitive_score(percentages)

            if total_typing_cognitive_score is None:
                logger.error(f"Total typing cognitive score is None for user {user_uid} on {day_to_analyze}")
                return False

            # Store the results in Supabase
            # NOTE: For now we dont want to store the std and mean for each metric results, so we are not using the values from results_list
            # values = [item for result in results_list for item in (result["std"], result["mean"])]
            # payload = dict(zip(SUPABASE_COLUMN_KEYS, values))
            payload = {}
            payload.update({
                "analysis_id": daily_analysis_id,
                "percentage_critical": percentages["Critical"],
                "percentage_very_bad": percentages["Very Bad"],
                "percentage_normal": percentages["Normal"],
                "percentage_very_good": percentages["Very Good"],
                "percentage_excellent": percentages["Excellent"],
                "total_typing_cognitive_score": total_typing_cognitive_score
            })

            # Debug logging to see what values we're sending
            logger.info(f"DEBUG - Payload being sent to Supabase for user {user_uid}:")
            logger.info(f"analysis_id: {daily_analysis_id}")
            logger.info(f"percentage_critical: {percentages['Critical']}")
            logger.info(f"percentage_very_bad: {percentages['Very Bad']}")
            logger.info(f"percentage_normal: {percentages['Normal']}")
            logger.info(f"percentage_very_good: {percentages['Very Good']}")
            logger.info(f"percentage_excellent: {percentages['Excellent']}")
            logger.info(f"total_typing_cognitive_score: {total_typing_cognitive_score}")
            logger.info(f"Total percentages sum: {sum(percentages.values())}")

            # Store the results in Supabase
            response = self.supabase_service.send_data("Daily_Analysis_Typing_Stats", None, None, payload)

            if not response:
                logger.error(f"Failed to store typing stats for user {user_uid} on {day_to_analyze}")
                return False

            return True
        except Exception as e:
            logger.error(f"Error calculating typing stats for user {user_uid} on {day_to_analyze}: {e}")
            return False

    def _calculate_total_typing_cognitive_score(self, percentages: dict) -> float | None:
        """
        This function calculates the total typing score based on the percentages of each category.
        Args:
            percentages: dict - The dictionary with the percentages of each category
        Returns:
            float - The total typing score (range: -2.0 to +2.0)
        """
        try:
            # Debug: Log the input percentages
            logger.info(f"Calculating cognitive score with percentages: {percentages}")
            
            # Ensure all required keys exist
            required_keys = ["Excellent", "Very Good", "Normal", "Very Bad", "Critical"]
            for key in required_keys:
                if key not in percentages:
                    logger.error(f"Missing percentage key: {key}")
                    return None
            
            # Formula: Score = (2 * percentage_excellent + 1 * percentage_very_good + 0 * percentage_normal - 1 * percentage_very_bad - 2 * percentage_critical) / 100, percentage as intengers numbers
            total_typing_cognitive_score = (2 * percentages["Excellent"] + 1 * percentages["Very Good"] + 0 * percentages["Normal"] - 1 * percentages["Very Bad"] - 2 * percentages["Critical"]) / 100.0
            
            logger.info(f"Raw cognitive score (before any adjustments): {total_typing_cognitive_score}")
            logger.info(f"Type of cognitive score: {type(total_typing_cognitive_score)}")
            
            # Check if the score might be problematic
            if total_typing_cognitive_score < -200 or total_typing_cognitive_score > 200:
                logger.warning(f"Cognitive score seems out of normal range: {total_typing_cognitive_score}")
            
            return total_typing_cognitive_score 
        except Exception as e:
            logger.error(f"Error calculating total typing cognitive score: {e}")
            return None

    def _calculate_metric_statistics(self, typing_sessions_decisions_info: list, metric_table_name: str) -> dict | None:
        """Calculate mean and std for a metric from typing sessions data."""
        try:
            values = [session["value"] for session in typing_sessions_decisions_info]
            if not values:
                return None
                
            mean_value = np.mean(values)
            std_value = np.std(values)
            
            return {
                "description": metric_table_name,
                "std": std_value,
                "mean": mean_value
            }
        except (KeyError, ValueError) as e:
            logger.error(f"Error calculating statistics for {metric_table_name}: {e}")
            return None

    def _calculate_percentages(self, categories: list, decisions: list) -> dict | None:

        """
        Given a list of categories and a list of decision made for each category,
        the function will return a dictionary with the percentage of each category.

        Args:
            categories: list - The list of categories
            decisions: list - The list of decisions made for each category

        Returns:
            dict - The dictionary with the percentage of each category
        """

        total_count = len(decisions)

        if total_count == 0:
            print("No decisions found.")
            return None

        decision_counts = {}
        for decision in decisions:
            if decision in categories:
                if decision not in decision_counts:
                    decision_counts[decision] = 0
                decision_counts[decision] += 1

        percentages = {category: (decision_counts.get(category, 0) / total_count * 100) for category in categories}
        # Debug: Log the calculated percentages  
        logger.info(f"Calculated percentages: {percentages}")
        return percentages