from app.config import settings
import logging
from supabase import create_client
from datetime import date, datetime

logger = logging.getLogger(__name__)

class SupabaseService:

    def __init__(self):
        self._initialize_supabase()

    def _initialize_supabase(self):
        """Initialize Supabase client."""
        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Supabase initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase: {e}")
            raise
    
    def send_user(self, user_uid: str, user_email: str, app_origin: str) -> bool:
        """Send user data to Supabase."""
        try:
            if self.client is None:
                logger.warning("Supabase client not initialized. Skipping user send operation.")
                return False

            # Check if user already exists in Supabase
            existing = self.client.table('Users') \
                .select('user_uid') \
                .eq('user_uid', user_uid) \
                .execute()
            if existing.data:
                logger.warning(f"User {user_uid} already exists in Supabase")
                return True

            payload = {
                'user_uid': user_uid,
                'user_email': user_email,
                'app_origin': app_origin
            }
            self.client.table('Users').insert(payload).execute()
            logger.info(f"User {user_uid} sent to Supabase successfully")
            return True
        except Exception as e:
            logger.error(f"Error sending user {user_uid} to Supabase: {e}")
            return False

    def send_data(self, table_name: str, unique_field, unique_value, payload) -> bool:
        """Generic method to send data to any Supabase table."""
        try:
            if unique_value is not None and unique_value != '':  # that means the insert query does not need a check before inserting
                existing = self.client.table(table_name) \
                    .select(unique_field) \
                    .eq(unique_field, unique_value) \
                    .execute()
                if existing.data:
                    logger.warning(f"Record with: {unique_value} already exists in Supabase")
                    return True
            self.client.table(table_name).insert(payload).execute()
            return True
        except Exception as e:
            error_str = str(e)
            if '23505' in error_str: # 23505 is the code for duplicate key constraint violation
                logger.warning(f"Record already exists in {table_name}, skipping insertion (duplicate key constraint)")
                return True
            else:
                logger.error(f"Error sending data to Supabase: {e}")
                return False

    def get_user_baseline_metric_values(self, user_uid, metric_name):
        """Get the latest baseline values for a user and a specific metric."""
        try:
            select_str = "id, baseline_median, baseline_mad, Users(user_uid)"
            response = self.client.table('Baseline_Metrics') \
                .select(select_str) \
                .eq("user_uid", user_uid) \
                .eq("metric_name", metric_name) \
                .order('date_created', desc=True) \
                .limit(1) \
                .execute()
            data = response.data
            if data:
                baseline_data = data[0]
                return baseline_data
            else:
                logger.info(f"No baseline metric values found for user {user_uid} and metric {metric_name}.")
                return None
        except Exception as e:
            logger.error(f"Error fetching baseline metric values for user {user_uid}: {e}")
            return None

    def _get_baseline_metrics_rpc_function(self, user_uid: str, sess_end_date: datetime, current_date_time: datetime):
        try:

            if isinstance(sess_end_date, str):
                sess_end_date = datetime.fromisoformat(sess_end_date)
            if isinstance(current_date_time, str):
                current_date_time = datetime.fromisoformat(current_date_time)

            response_new = self.client.rpc('get_baseline_metrics', {
                    "input_user_uid_param": user_uid,
                    "start_date_param": sess_end_date.isoformat(),
                    "end_date_param": current_date_time.isoformat()
                }).execute()
            return response_new.data
        except Exception as e:
            logger.error(f"Error getting baseline metrics for user {user_uid}: {e}")
            return None

    def _save_baseline_data(self, user_uid: str, data, metrics: list, current_date: datetime, data_category: str):
        for metric_name, mean_key, std_key, median_key, mad_key in metrics:
            payload = {
                'user_uid': user_uid,
                'metric_name': metric_name,
                'baseline_mean': data[0][mean_key],
                'baseline_std': data[0][std_key],
                'baseline_median': data[0][median_key],
                'baseline_mad': data[0][mad_key],
                'date_created': current_date.isoformat(),
                'sess_start_date': data[0]['first_session'],
                'sess_end_date': data[0]['last_session'],
                'data_category': data_category
            }
            self.send_data(
                "Baseline_Metrics",
                None,
                None,
                payload
            )
        
    def get_z_scores_of_a_typing_session(self, session_uid: str):
        """""
        Get the z-scores for a typing session
        Args:
            session_uid: str - The unique identifier of the typing session
        Returns:
            dict - The z-scores for the typing session (ex. {"Effort_To_Output_Ratio_Data": 0.5, "Typing_Rhythm_Stability_Data": 0.5, "Cognitive_Processing_Index_Data": 0.5, "Pause_To_Production_Ratio_Data": 0.5, "Correction_Efficiency_Data": 0.5, "Net_Production_Rate_Data": 0.5, "Cognitive_Processing_Efficiency_Data": 0.5, "Pressure_Intensity_Data": 0.5})
        """
        try:
            logger.info(f"Retrieving z-scores for session {session_uid}...")
            metrics = [
                "Effort_To_Output_Ratio_Data",
                "Typing_Rhythm_Stability_Data",
                "Cognitive_Processing_Index_Data",
                "Pause_To_Production_Ratio_Data",
                "Correction_Efficiency_Data",
                "Net_Production_Rate_Data",
                "Cognitive_Processing_Efficiency_Data",
                "Pressure_Intensity_Data",
            ]
            z_scores = {}
            for metric in metrics:
                response = self.client.table(metric) \
                    .select('modified_z_score') \
                    .eq('session_uid', session_uid) \
                    .execute()
                if response.data:
                    z_scores[metric] = response.data[0]['modified_z_score']
            return z_scores
        except Exception as e:
            logger.error(f"Error retrieving z-scores: {e}")
            return None
    
    def get_z_scores_info_for_sleep_data(self, user_uid: str, day_analyzed: date, metrics_names: list):
        """
        Get the z-scores for a sleep data
        Args:
            user_uid: str - The user's unique identifier
            day_analyzed: date - The day of the analysis (day that is analyzed)
            metrics_names: list - The list of metric names to retrieve z-scores for
        Returns:
            dict - The z-scores for the sleep data (ex. {"id": 1, "sleep_data_analysis_id": 1, "sqs_z_score": 0.5})
        """
        try:
            # We need to fist query in the main data analysis table and get the ID
            # IMPORTANT: Only get main_sleep, not nap_sleep
            sleep_data_analysis_id = self.client.table('Sleep_Data_Analysis') \
                .select('id') \
                .eq('user_uid', user_uid) \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .eq('type', 'main_sleep') \
                .limit(1) \
                .execute()
            if sleep_data_analysis_id.data:
                sleep_data_analysis_id = sleep_data_analysis_id.data[0]['id']
            else:
                logger.error(f"No main sleep data analysis found for user {user_uid} on {day_analyzed}")
                return None

            select_query = f"id, sleep_data_analysis_id, {', '.join([f'{metric}_z_score' for metric in metrics_names])}"
            response = self.client.table('Sleep_Data_Z_Scores') \
                .select(select_query) \
                .eq('sleep_data_analysis_id', sleep_data_analysis_id) \
                .limit(1) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error retrieving z-scores for sleep data for user {user_uid} on {day_analyzed}: {e}")
            return None
    
    def get_z_scores_info_for_device_interaction_data(self, user_uid: str, day_analyzed: date, metrics_names: list):
        """
        Get the z-scores for a device interaction data
        Args:
            user_uid: str - The user's unique identifier
            day_analyzed: date - The day of the analysis (day that is analyzed)
            metrics_names: list - The list of metric names to retrieve z-scores for
        Returns:
            dict - The z-scores for the device interaction data (ex. {"id": 1, "device_interaction_data_analysis_id": 1, "screen_time_z_score": 0.5})
        """
        try:
            # We need to fist query in the main data analysis table and get the ID
            device_interaction_data_analysis_id = self.client.table('Device_Interaction_Data_Analysis') \
                .select('id') \
                .eq('user_uid', user_uid) \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .limit(1) \
                .execute()
            if device_interaction_data_analysis_id.data:
                device_interaction_data_analysis_id = device_interaction_data_analysis_id.data[0]['id']
            else:
                logger.error(f"No device interaction data analysis found for user {user_uid} on {day_analyzed}")
                return None

            select_query = f"id, device_interaction_data_analysis_id, {', '.join([f'{metric}_z_score' for metric in metrics_names])}"
            response = self.client.table('Device_Interaction_Data_Z_Scores') \
                .select(select_query) \
                .eq('device_interaction_data_analysis_id', device_interaction_data_analysis_id) \
                .limit(1) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error retrieving z-scores for device interaction data for user {user_uid} on {day_analyzed}: {e}")
            return None
    
    def get_z_scores_info_for_activity_data(self, user_uid: str, day_analyzed: date, metrics_names: list):
        """
        Get the z-scores for an activity data
        Args:
            user_uid: str - The user's unique identifier
            day_analyzed: date - The day of the analysis (day that is analyzed)
            metrics_names: list - The list of metric names to retrieve z-scores for
        Returns:
            dict - The z-scores for the activity data (ex. {"id": 1, "activity_data_analysis_id": 1, "daily_active_minutes_z_score": 0.5})
        """
        try:
            # We need to fist query in the main data analysis table and get the ID
            activity_data_analysis_id = self.client.table('Activity_Data_Analysis') \
                .select('id') \
                .eq('user_uid', user_uid) \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .limit(1) \
                .execute()
            if activity_data_analysis_id.data:
                activity_data_analysis_id = activity_data_analysis_id.data[0]['id']
            else:
                logger.error(f"No activity data analysis found for user {user_uid} on {day_analyzed}")
                return None

            select_query = f"id, activity_data_analysis_id, {', '.join([f'{metric}_z_score' for metric in metrics_names])}"
            response = self.client.table('Activity_Data_Z_Scores') \
                .select(select_query) \
                .eq('activity_data_analysis_id', activity_data_analysis_id) \
                .limit(1) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error retrieving z-scores for activity data for user {user_uid} on {day_analyzed}: {e}")
            return None
    
    def get_z_scores_info_for_call_data(self, user_uid: str, day_analyzed: date, metrics_names: list):
        """
        Get the z-scores for a call data
        Args:
            user_uid: str - The user's unique identifier
            day_analyzed: date - The day of the analysis (day that is analyzed)
            metrics_names: list - The list of metric names to retrieve z-scores for
        Returns:
            dict - The z-scores for the call data (ex. {"id": 1, "call_data_analysis_id": 1, "missed_call_ratio_z_score": 0.5})
        """
        try:
            # We need to fist query in the main data analysis table and get the ID
            call_data_analysis_id = self.client.table('Call_Data_Analysis') \
                .select('id') \
                .eq('user_uid', user_uid) \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .limit(1) \
                .execute()
            if call_data_analysis_id.data:
                call_data_analysis_id = call_data_analysis_id.data[0]['id']
            else:
                logger.error(f"No call data analysis found for user {user_uid} on {day_analyzed}")
                return None

            select_query = f"id, call_data_analysis_id, {', '.join([f'{metric}_z_score' for metric in metrics_names])}"
            response = self.client.table('Call_Data_Z_Scores') \
                .select(select_query) \
                .eq('call_data_analysis_id', call_data_analysis_id) \
                .limit(1) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error retrieving z-scores for call data for user {user_uid} on {day_analyzed}: {e}")
            return None
    
    def get_z_scores_info_for_gps_data(self, user_uid: str, day_analyzed: date, metrics_names: list):
        """
        Get the z-scores for a gps data
        Args:
            user_uid: str - The user's unique identifier
            day_analyzed: date - The day of the analysis (day that is analyzed)
            metrics_names: list - The list of metric names to retrieve z-scores for
        Returns:
            dict - The z-scores for the gps data (ex. {"id": 1, "gps_data_analysis_id": 1, "total_time_spend_in_home_seconds_z_score": 0.5})
        """
        try:
            # We need to fist query in the main data analysis table and get the ID
            gps_data_analysis_id = self.client.table('GPS_Data_Analysis') \
                .select('id') \
                .eq('user_uid', user_uid) \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .limit(1) \
                .execute()
            if gps_data_analysis_id.data:
                gps_data_analysis_id = gps_data_analysis_id.data[0]['id']
            else:
                logger.error(f"No gps data analysis found for user {user_uid} on {day_analyzed}")
                return None

            select_query = f"id, gps_data_analysis_id, {', '.join([f'{metric}_z_score' for metric in metrics_names])}"
            response = self.client.table('GPS_Data_Z_Scores') \
                .select(select_query) \
                .eq('gps_data_analysis_id', gps_data_analysis_id) \
                .limit(1) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error retrieving z-scores for gps data for user {user_uid} on {day_analyzed}: {e}")
            return None
        
    def update_scores_and_decisions_of_a_behavioral_data_analysis(self, main_data_analysis_id: int, metric_category_name: str, score: float, decision: str):
        """
        Update the scores and decisions of a behavioral data analysis
        Args:
            main_data_analysis_id: int - The id of the main data analysis
            metric_category_name: str - The name of the metric category
            score: float - The score to be updated
            decision: str - The decision to be updated
        """
        try:
            logger.info(f"Updating the scores and decisions of a behavioral data analysis for {metric_category_name} with ID {main_data_analysis_id}")
            if metric_category_name == "SLEEP_DATA":
                # Update the score and decision for the sleep data analysis in the main sleep data analysis table based on the analysis ID
                result = self.client.table('Sleep_Data_Analysis') \
                    .update({
                        'cognitive_score': score,
                        'cognitive_decision': decision
                    }) \
                    .eq('id', main_data_analysis_id) \
                    .execute()
            elif metric_category_name == "DAILY_DEVICE_INTERACTION":
                # Update the score and decision for the device interaction data analysis in the main device interaction data analysis table based on the analysis ID
                result = self.client.table('Device_Interaction_Data_Analysis') \
                    .update({
                        'cognitive_score': score,
                        'cognitive_decision': decision
                    }) \
                    .eq('id', main_data_analysis_id) \
                    .execute()
            elif metric_category_name == "ACTIVITY_BEHAVIOR":
                # Update the score and decision for the activity data analysis in the main activity data analysis table based on the analysis ID
                result = self.client.table('Activity_Data_Analysis') \
                    .update({
                        'cognitive_score': score,
                        'cognitive_decision': decision
                    }) \
                    .eq('id', main_data_analysis_id) \
                    .execute()
            elif metric_category_name == "CALL_METRICS":
                # Update the score and decision for the call data analysis in the main call data analysis table based on the analysis ID
                result = self.client.table('Call_Data_Analysis') \
                    .update({
                        'cognitive_score': score,
                        'cognitive_decision': decision
                    }) \
                    .eq('id', main_data_analysis_id) \
                    .execute()
            elif metric_category_name == "GPS_METRICS":
                # Update the score and decision for the gps data analysis in the main gps data analysis table based on the analysis ID
                result = self.client.table('GPS_Data_Analysis') \
                    .update({
                        'cognitive_score': score,
                        'cognitive_decision': decision
                    }) \
                    .eq('id', main_data_analysis_id) \
                    .execute()
            else:
                logger.error(f"Invalid metric category name: {metric_category_name}")
                return False
                
            # Verify the update succeeded
            if result and result.data:
                logger.info(f"Successfully updated {len(result.data)} row(s) for {metric_category_name}")
                return True
            else:
                logger.error(f"Update failed - no rows affected. ID {main_data_analysis_id} may not exist in table")
                return False
        except Exception as e:
            logger.error(f"Error updating the scores and decisions of a behavioral data analysis: {e}")
            return False

    def update_scores_and_decisions_of_a_typing_session(self, session_id: str, score: float, decision: str):
        try:
            self.client.table('Typing_Sessions') \
            .update({
                'cognitive_score': score,
                'cognitive_decision': decision
            }) \
            .eq('session_uid', session_id) \
            .execute()
            logger.info(f"\033[92mUpdated the cognitive score and final decision for session {session_id} successfully\033[0m")
            return True
        except Exception as e:
            logger.error(f"Error updating the cognitive score and final decision for session {session_id}: {e}")
            return False

    def send_computed_sleep_info(self, user_uid: str, sleep_data, day_analyzed: date) -> int | list[int] | None:
        """
        Send computed sleep info to Supabase.
        Args:
            user_uid: str - The user's unique identifier
            sleep_data: Dict[str, Any] or List[Dict[str, Any]] - The sleep data to be sent, should contain:
                - estimated_start_date_time: datetime
                - estimated_end_date_time: datetime
                - duration: int
                - actual_duration: int
                - sleep_screen_time: int
                - nts: float
                - nse: float
                - nst: float
                - nta: float
                - sqs: float
                - type: str
            day_analyzed: date - The day of the analysis (day that is analyzed)
        Returns:
            int | list[int] | None - The id(s) of the sleep data analysis if created successfully, None otherwise
        """
        try:
            # Handle both single sleep data (dict) and multiple sleep data (list)
            if isinstance(sleep_data, list):
                # Multiple sleep records - process each one
                sleep_ids = []
                for single_sleep_data in sleep_data:
                    sleep_id = self._send_single_sleep_info(user_uid, single_sleep_data, day_analyzed)
                    if sleep_id is not None:
                        sleep_ids.append(sleep_id)
                    else:
                        logger.error(f"Failed to store one sleep record of type {single_sleep_data.get('type')}")
                
                logger.info(f"\033[92mSent {len(sleep_ids)} sleep records for user {user_uid} successfully\033[0m")
                return sleep_ids if sleep_ids else None
            else:
                # Single sleep record - use original logic
                return self._send_single_sleep_info(user_uid, sleep_data, day_analyzed)
        except Exception as e:
            logger.error(f"Error sending computed sleep info for user {user_uid}: {e}")
            return None

    def _send_single_sleep_info(self, user_uid: str, sleep_data: dict, day_analyzed: date) -> int | None:
        """
        Send a single sleep record to Supabase.
        Args:
            user_uid: str - The user's unique identifier
            sleep_data: dict - The sleep data to be sent
            day_analyzed: date - The day of the analysis (day that is analyzed)
        Returns:
            int | None - The id of the sleep data analysis if it was created successfully, None otherwise
        """
        try:
            existing = self.client.table('Sleep_Data_Analysis') \
                .select('id') \
                .eq('user_uid', user_uid) \
                .lte('estimated_start_date_time', sleep_data['estimated_end_date_time']) \
                .gte('estimated_end_date_time', sleep_data['estimated_start_date_time']) \
                .execute()
            
            if existing.data:
                logger.info(f"\033[93mThe new sleep for the user: {user_uid} with start-time: {sleep_data['estimated_start_date_time']} and end-time {sleep_data['estimated_end_date_time']} is inside an existing one\033[0m")
                return None
            
            payload = {
                'user_uid': user_uid,
                'day_analyzed': day_analyzed.isoformat(),
                'estimated_start_date_time': sleep_data['estimated_start_date_time'].isoformat(),
                'estimated_end_date_time': sleep_data['estimated_end_date_time'].isoformat(),
                'total_duration': sleep_data['duration'],
                'actual_duration': sleep_data['actual_duration'],
                'sleep_screen_time': sleep_data['sleep_screen_time'],
                'norm_total_sleep': sleep_data['nts'],
                'norm_sleep_efficiency': sleep_data['nse'],
                'norm_screen_time': sleep_data['nst'],
                'norm_time_alignment': sleep_data['nta'],
                'sleep_quality_score': sleep_data['sqs'],
                'type': sleep_data['type']
            }
            result = self.client.table('Sleep_Data_Analysis').insert(payload).execute()
            logger.info(f"\033[92mSent {sleep_data['type']} sleep info for user {user_uid} successfully\033[0m")
            return result.data[0].get('id')
        except Exception as e:
            logger.error(f"Error sending single sleep info for user {user_uid}: {e}")
            return None
        
    def send_computed_gps_info(self, user_uid: str, gps_data: dict, day_analyzed: date) -> int | None:
        """
        Send computed GPS info to Supabase.
        Args:
            user_uid: str - The user's unique identifier
            gps_data: dict - The GPS data to be sent
            day_analyzed: date - The day of the analysis (day that is analyzed)
        Returns:
            bool - True if the data was sent successfully, False otherwise
        """
        try:
            # Check if an analysis is already for the given day and user
            existing = self.client.table('GPS_Data_Analysis') \
                .select('id') \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .eq('user_uid', user_uid) \
                .execute()
            
            if existing.data:
                existing_id = existing.data[0].get('id')
                logger.info(f"GPS analysis for user {user_uid} on {day_analyzed} already exists: ID: {existing_id}")
                return existing_id  # Return existing ID instead of None
            
            payload = {
                'day_analyzed': day_analyzed.isoformat(),
                'total_time_spend_in_home_seconds': gps_data.get('total_time_spend_in_home_seconds', 0),
                'total_time_spend_travelling_seconds': gps_data.get('total_time_spend_traveling_seconds', 0),
                'total_time_spend_out_of_home_seconds': gps_data.get('total_time_spend_out_of_home_seconds', 0),
                'total_distance_traveled_km': gps_data.get('total_distance_traveled_km', 0),
                'average_time_spend_in_locations_hours': gps_data.get('average_time_spend_in_locations_hours', 0),
                'number_of_unique_locations': gps_data.get('number_of_unique_locations', 0),
                'number_of_locations_total': gps_data.get('number_of_locations_total', 0),
                'first_move_timestamp_after_3am': gps_data.get('first_move_timestamp_after_3am', 0),
                'entropy': gps_data.get('entropy', 0),
                'time_period_active': gps_data.get('time_period_active', 0),
                'user_uid': user_uid
            }
            result = self.client.table('GPS_Data_Analysis').insert(payload).execute()
            if result.data:
                gps_data_analysis_id = result.data[0].get('id')
            else:
                logger.error(f"Failed to create a daily GPS data analysis event for user {user_uid} on {day_analyzed}")
                return None

            # Now insert into gps_key_locations table
            gps_key_locations_list = gps_data.get('key_locations_clusters_info')
            for location_data in gps_key_locations_list:
                payload = {
                    'key_location_id': location_data['key_location_id'],
                    'latitude': location_data['latitude'],
                    'longitude': location_data['longitude'],
                    'total_time_spent_seconds': location_data['total_time_spent_seconds'],
                    'num_of_gps_events': location_data['num_of_gps_events'],
                    'key_loc_type': location_data['key_loc_type'],
                    'gps_data_analysis_id': gps_data_analysis_id
                }
                self.client.table('GPS_Key_Locations').insert(payload).execute()

            # Now insert into gps_transitions
            gps_transitions_list = gps_data.get('key_locations_transitions_info')
            for transition_data in gps_transitions_list:
                payload = {
                    'key_loc_start_id': transition_data['key_loc_start_id'],
                    'key_loc_end_id': transition_data['key_loc_end_id'],
                    'start_time_of_transition': transition_data['start_time_of_transition'],
                    'end_time_of_transition': transition_data['end_time_of_transition'],
                    'total_time_travel_seconds': transition_data['total_time_travel_seconds'],
                    'total_distance_traveled_km': transition_data['total_distance_traveled_km'],
                    'total_gps_events_in_transition_cluster': transition_data['total_events_in_transition_cluster'],
                    'gps_data_analysis_id': gps_data_analysis_id
                }
                self.client.table('GPS_Transitions').insert(payload).execute()

            # Safely extract values with proper error handling
            convex_hull = gps_data.get('convex_hull', {})
            sde = gps_data.get('standard_deviation_ellipse', {})
            max_distance = gps_data.get('max_distance_from_home', {})
                
            # Handle mean_center safely
            mean_center = sde.get('mean_center', [0, 0])
            if not isinstance(mean_center, (list, tuple)) or len(mean_center) < 2:
                mean_center = [0, 0]
                
            # Handle coords safely
            coords = max_distance.get('coords', [])
            if not isinstance(coords, list) or len(coords) == 0:
                coords_lat, coords_lon = 0, 0
            else:
                coords_lat = coords[0].get('latitude', 0)
                coords_lon = coords[0].get('longitude', 0)
                
            payload = {
                'convex_hull_area_m2': convex_hull.get('area_m2', 0),
                'convex_hull_perimeter_m': convex_hull.get('perimeter_m', 0),
                'gravimetric_compactness': convex_hull.get('gravimetric_compactness', 0),
                'sde_mean_center_lon': mean_center[0],
                'sde_mean_center_lat': mean_center[1],
                'sde_width_m': sde.get('width_m', 0),
                'sde_height_m': sde.get('height_m', 0),
                'sde_angle_deg': sde.get('angle_deg', 0),
                'sde_area_m2': sde.get('area_m2', 0),
                'max_distance_from_home_km': max_distance.get('distance_km', 0),
                'max_distance_timestamp': max_distance.get('timestamp', 0),
                'max_distance_lat': coords_lat,
                'max_distance_lon': coords_lon,
                'gps_data_analysis_id': gps_data_analysis_id
            }
            self.client.table('GPS_Spatial_Features').insert(payload).execute()
            
            logger.info(f"\033[92mSent GPS info for user {user_uid} successfully\033[0m")
            return gps_data_analysis_id
        
        except Exception as e:
            logger.error(f"Error sending computed GPS info for user {user_uid}: {e}")
            return None

    def send_computed_call_info(self, user_uid: str, call_data: dict, day_analyzed: date) -> int | None:
        """
        Send computed call info to Supabase.
        Args:
            user_uid: str - The user's unique identifier
            call_data: dict - The call data to be sent
            day_analyzed: date - The day of the analysis (day that is analyzed)
        Returns:
            int | None - The id of the call data analysis if it was created successfully, None otherwise
        """
        try:
            # Check if an analysis is already for the given day and user
            existing = self.client.table('Call_Data_Analysis') \
                .select('id') \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .eq('user_uid', user_uid) \
                .execute()
            
            if existing.data:
                existing_id = existing.data[0].get('id')
                logger.info(f"Call analysis for user {user_uid} on {day_analyzed} already exists: ID: {existing_id}")
                return existing_id  # Return existing ID instead of None

            payload = {
                'day_analyzed': day_analyzed.isoformat(),
                'missed_call_ratio': call_data.get('missed_call_ratio', 0),
                'night_call_ratio': call_data.get('night_call_ratio', 0),
                'day_call_ratio': call_data.get('day_call_ratio', 0),
                'avg_call_duration': call_data.get('avg_call_duration', 0),
                'total_calls_in_a_day': call_data.get('total_calls_in_a_day', 0),
                'user_uid': user_uid
            }
            result = self.client.table('Call_Data_Analysis').insert(payload).execute()
            logger.info(f"\033[92mSent call info for user {user_uid} successfully\033[0m")
            return result.data[0].get('id')
        except Exception as e:
            logger.error(f"Error sending computed call info for user {user_uid}: {e}")
            return None
        
    
    def send_computed_activity_info(self, user_uid: str, activity_data: dict, day_analyzed: date) -> int | None:
        """
        Send computed activity info to Supabase.
        Args:
            user_uid: str - The user's unique identifier
            activity_data: dict - The activity data to be sent
            day_analyzed: date - The day of the analysis (day that is analyzed)
        Returns:
            bool - True if the data was sent successfully, False otherwise
        """
        try:
            # Check if an analysis is already for the given day and user
            existing = self.client.table('Activity_Data_Analysis') \
                .select('id') \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .eq('user_uid', user_uid) \
                .execute()
            
            if existing.data:
                existing_id = existing.data[0].get('id')
                logger.info(f"Activity analysis for user {user_uid} on {day_analyzed} already exists: ID: {existing_id}")
                return existing_id  # Return existing ID instead of None

            payload = {
                'day_analyzed': day_analyzed.isoformat(), # The day that is analyzed
                'switching_frequency': activity_data.get('activity_switching_frequency', 0),
                'daily_active_minutes': activity_data.get('daily_active_minutes', 0),
                'activity_entropy': activity_data.get('activity_entropy', 0),
                'inactivity_percentage': activity_data.get('inactivity_percentage', 0),
                'user_uid': user_uid
            }
            result = self.client.table('Activity_Data_Analysis').insert(payload).execute()
            if result.data:
                activity_data_analysis_id = result.data[0].get('id')
            else:
                logger.error(f"Failed to create a daily activity data analysis event for user {user_uid} on {day_analyzed}")
                return None
            
            # Now insert into Activity_Distribution_Per_Day_Section_Analysis table
            activity_distribution_per_day_section_df = activity_data.get('activity_percentages_per_day_sections')

            for day_section, row in activity_distribution_per_day_section_df.iterrows():
                payload = {
                    'day_section': day_section,
                    'in_vehicle': row.get('in_vehicle', 0),
                    'on_bicycle': row.get('on_bicycle', 0),
                    'on_foot': row.get('on_foot', 0),
                    'still': row.get('still', 0),
                    'tilting': row.get('tilting', 0),
                    'unknown': row.get('unknown', 0),
                    'activity_data_analysis_id': activity_data_analysis_id
                }
                self.client.table('Activity_Distribution_Per_Day_Section_Analysis').insert(payload).execute()

            logger.info(f"\033[92mSent activity info for user {user_uid} successfully\033[0m")
            return activity_data_analysis_id
        except Exception as e:
            logger.error(f"Error sending computed activity info for user {user_uid}: {e}")
            return None

    def send_computed_device_interaction_info(self, user_uid: str, interaction_data: dict, day_analyzed: date) -> int | None:
        """
        Send computed device interaction info to Supabase.
        Args:
            user_uid: str - The user's unique identifier
            interaction_data: dict - The interaction data to be sent
            day_analyzed: date - The day of the analysis (day that is analyzed)
        Returns:
            int | None - The id of the device interaction data analysis if it was created successfully, None otherwise
        """
        try:

            # Check if an analysis is already for the given day and user
            existing = self.client.table('Device_Interaction_Data_Analysis') \
                .select('id') \
                .eq('day_analyzed', day_analyzed.isoformat()) \
                .eq('user_uid', user_uid) \
                .execute()
            
            if existing.data:
                existing_id = existing.data[0].get('id')
                logger.info(f"Device interaction analysis for user {user_uid} on {day_analyzed} already exists: ID: {existing_id}")
                return existing_id  # Return existing ID instead of None

            payload = {
                'day_analyzed': day_analyzed.isoformat(), # The day that is analyzed
                'total_screen_time_sec': interaction_data.get('screen_time_analysis_result', 0) or 0,
                'total_low_light_time_sec': interaction_data.get('low_light_day_time_result', 0) or 0,
                'total_device_drop_events': interaction_data.get('device_drop_events_result', 0) or 0,
                "user_uid": user_uid
            }
            result = self.client.table('Device_Interaction_Data_Analysis').insert(payload).execute()
            if result.data:
                interaction_data_analysis_id = result.data[0].get('id')
            else:
                logger.error(f"Failed to create a daily interaction data analysis event for user {user_uid} on {day_analyzed}")
                return None

            # Now insert into Circadian_Screen_Time_Analysis table
            circadian_screen_time_list = interaction_data.get('screen_time_circadian_hours_result')
            if circadian_screen_time_list is not None:
                for circadian_screen_time in circadian_screen_time_list:
                    payload = {
                        'day_section': circadian_screen_time['day_section'],
                        'duration': circadian_screen_time['duration'] or 0,
                        'percentage': circadian_screen_time['percentage'] or 0,
                        'daily_interaction_data_analysis_id': interaction_data_analysis_id
                    }
                    self.client.table('Circadian_Screen_Time_Analysis').insert(payload).execute()

            # Now insert into App_Usage_Analysis table
            app_usage_df = interaction_data.get('app_usage_result')
            if app_usage_df is not None:
                for index, row in app_usage_df.iterrows():
                    payload = {
                        'app_name': row['app_name'],
                        'time_used_sec': row['time_used'] or 0, # seconds
                        'daily_interaction_data_analysis_id': interaction_data_analysis_id
                    }
                    self.client.table('App_Usage_Analysis').insert(payload).execute()

            logger.info(f"\033[92mSent device interaction info for user {user_uid} successfully\033[0m")
            return interaction_data_analysis_id
        except Exception as e:
            logger.error(f"Error sending device interaction info for user {user_uid}: {e}")
            return None

    def create_a_daily_analysis_event(self, user_uid: str, day_analyzed: str, analysis_date: str) -> int | None:
        """
        Create a daily analysis event for a user in given day.
        The event is created in the table Daily_Analysis_Events.
        
        Args:
            user_uid: str - The user's unique identifier
            day_analyzed: date - The day of the analysis (day that is analyzed)
            analysis_date: datetime - The date and time of the analysis (when the analysis is done)

        Returns:
            str - The ID of the created daily analysis event
        """
        try:
            
            # Check if the event for the given day already exists
            existing = self.client.table('Daily_Analyses') \
                .select('id') \
                .eq('day_analyzed', day_analyzed) \
                .eq('user_uid', user_uid) \
                .execute()
            
            if existing.data:
                record_id = existing.data[0].get('id')
                logger.info(f"Daily analysis event for user {user_uid} on {day_analyzed} already exists: ID: {record_id}")
                return record_id
            
            # Else, create a new event
            payload = {
                "day_analyzed": day_analyzed,
                "analysis_date": analysis_date,
                "user_uid": user_uid
            }
            response = self.client.table('Daily_Analyses').insert(payload).execute()
            if response.data:
                logger.info(f"Daily analysis event for user {user_uid} on {day_analyzed} created successfully: ID: {response.data[0].get('id')}")
                return response.data[0].get('id')
            else:
                logger.error(f"Failed to create a daily analysis event for user {user_uid} on {day_analyzed}")
                return None
        except Exception as e:
            logger.error(f"Error creating a daily analysis event for user {user_uid} on {day_analyzed}: {e}")
            return None

    def retrieve_cognitive_info_of_typing_sessions(self, table_name: str, user_uid: str, date_to_analyze: str) -> list | None:
        """
        Retrieve the cognitive info (score and decision) made for typing sessions of a user for a given day.
        Also, this function will return the session UID's.

        Args:
            table_name: str - The name of the table to retrieve the data from, it helps with the construction of the JOIN select query
            user_uid: str - The user's unique identifier
            date_to_analyze: str - The day of the analysis (day that is analyzed)

        Returns:
            list - A list of dictionaries, each containing the session UID and the cognitive info (score and decision)
            None: If the cognitive info could not be retrieved
        """

        try:
            
            select_query = f"cognitive_decision, {table_name}(session_uid, value)"
            response = self.client.table('Typing_Sessions') \
                .select(select_query) \
                .eq('user_uid', user_uid) \
                .eq('session_date', date_to_analyze) \
                .execute()
            
            if not response.data:
                logger.info(f"No typing sessions found for user {user_uid} on {date_to_analyze}")
                return None

            # Flatten the response
            flat_data = []
            for session in response.data:
                data = session.get(table_name)
                cognitive_decision = session.get('cognitive_decision')

                if data:
                    # Handle both single item and list cases
                    if isinstance(data, list):
                        for item in data:
                            # Add cognitive_decision to each metric data item
                            item_with_decision = item.copy()  # Copy to avoid modifying original
                            item_with_decision['cognitive_decision'] = cognitive_decision
                            flat_data.append(item_with_decision)
                    else:
                        # Add cognitive_decision to the single metric data item
                        data_with_decision = data.copy()
                        data_with_decision['cognitive_decision'] = cognitive_decision
                        flat_data.append(data_with_decision)

            return flat_data
        except Exception as e:
            logger.error(f"Error retrieving cognitive decisions of typing sessions for user {user_uid} on {date_to_analyze}: {e}")
            return None

    def create_z_scores_for_sleep_data(self, user_uid: str, sleep_data_analysis_id: int, z_score_sleep_time: float, z_score_sqs: float, z_score_sleep_start_time: float, z_score_sleep_end_time: float):
        """Create the z-scores for each sleep data that requires it"""
        # Create table Sleep_Data_Z_Scores
        try:
            self.client.table('Sleep_Data_Z_Scores') \
                .insert({
                    'sleep_data_analysis_id': sleep_data_analysis_id,
                    'sleep_time_z_score': z_score_sleep_time,
                    'sqs_z_score': z_score_sqs,
                    'sleep_start_time_z_score': z_score_sleep_start_time,
                    'sleep_end_time_z_score': z_score_sleep_end_time
                }) \
                .execute()
            logger.info(f"\033[92mCreated the z-scores for sleep data for user {user_uid} successfully\033[0m")
            return True
        except Exception as e:
            logger.error(f"Error creating z-scores for sleep data for user {user_uid}: {e}")
            return False
    
    def create_z_scores_for_device_interaction_data(self, user_uid: str, device_interaction_data_analysis_id: int, z_score_screen_time: float, z_score_low_light_day_time: float, z_score_device_drop_events: float):
        """Create the z-scores for the device interaction data"""
        try:
            self.client.table('Device_Interaction_Data_Z_Scores') \
                .insert({
                    'device_interaction_data_analysis_id': device_interaction_data_analysis_id,
                    'screen_time_z_score': z_score_screen_time,
                    'low_light_day_time_z_score': z_score_low_light_day_time,
                    'device_drop_events_z_score': z_score_device_drop_events
                }) \
                .execute()
            logger.info(f"\033[92mCreated the z-scores for device interaction data for user {user_uid} successfully\033[0m")
            return True
        except Exception as e:
            logger.error(f"Error creating z-scores for device interaction data for user {user_uid}: {e}")
            return False
    
    def create_z_scores_for_activity_data(self, user_uid: str, activity_data_analysis_id: int, z_score_daily_active_minutes: float):
        """Create the z-scores for the activity data"""
        try:
            self.client.table('Activity_Data_Z_Scores') \
                .insert({
                    'activity_data_analysis_id': activity_data_analysis_id,
                    'daily_active_minutes_z_score': z_score_daily_active_minutes
                }) \
                .execute()
            logger.info(f"\033[92mCreated the z-scores for activity data for user {user_uid} successfully\033[0m")
            return True
        except Exception as e:
            logger.error(f"Error creating z-scores for activity data for user {user_uid}: {e}")
            return False

    def create_z_scores_for_call_data(self, user_uid: str, call_data_analysis_id: int, z_score_missed_call_ratio: float, z_score_avg_call_duration: float, z_score_total_calls_in_a_day: int):
        """Create the z-scores for the call data"""
        try:
            self.client.table('Call_Data_Z_Scores') \
                .insert({
                    'call_data_analysis_id': call_data_analysis_id,
                    'missed_call_ratio_z_score': z_score_missed_call_ratio,
                    'avg_call_duration_z_score': z_score_avg_call_duration,
                    'total_calls_in_a_day_z_score': z_score_total_calls_in_a_day
                }) \
                .execute()
            logger.info(f"\033[92mCreated the z-scores for call data for user {user_uid} successfully\033[0m")
            return True
        except Exception as e:
            logger.error(f"Error creating z-scores for call data for user {user_uid}: {e}")
            return False
    
    def create_z_scores_for_gps_data(self, user_uid: str, gps_data_analysis_id: int, z_score_total_time_spend_in_home_seconds: float, z_score_total_time_spend_traveling_seconds: float, z_score_total_time_spend_out_of_home_seconds: float, z_score_total_distance_traveled_km: float, z_score_average_time_spend_in_locations_hours: float, z_score_number_of_unique_locations: float, z_score_convex_hull_area_m2: float, z_score_standard_deviation_ellipse_area_m2: float, z_score_max_distance_from_home_timestamp: float, z_score_entropy: float):
        """Create the z-scores for the GPS data"""
        try:
            self.client.table('GPS_Data_Z_Scores') \
                .insert({
                    'gps_data_analysis_id': gps_data_analysis_id,
                    'total_time_spend_in_home_seconds_z_score': z_score_total_time_spend_in_home_seconds,
                    'total_time_spend_travelling_seconds_z_score': z_score_total_time_spend_traveling_seconds,
                    'total_time_spend_out_of_home_seconds_z_score': z_score_total_time_spend_out_of_home_seconds,
                    'total_distance_traveled_km_z_score': z_score_total_distance_traveled_km,
                    'average_time_spend_in_locations_hours_z_score': z_score_average_time_spend_in_locations_hours,
                    'number_of_unique_locations_z_score': z_score_number_of_unique_locations,
                    'convex_hull_area_m2_z_score': z_score_convex_hull_area_m2,
                    'sde_area_m2_z_score': z_score_standard_deviation_ellipse_area_m2,
                    'max_distance_from_home_time_z_score': z_score_max_distance_from_home_timestamp,
                    'entropy_z_score': z_score_entropy
                }) \
                .execute()
            logger.info(f"\033[92mCreated the z-scores for GPS data for user {user_uid} successfully\033[0m")
            return True
        except Exception as e:
            logger.error(f"Error creating z-scores for GPS data for user {user_uid}: {e}")
            return False
