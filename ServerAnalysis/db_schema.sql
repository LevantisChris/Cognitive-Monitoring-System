-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.Activity_Data_Analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  day_analyzed date NOT NULL,
  switching_frequency integer NOT NULL,
  daily_active_minutes integer NOT NULL,
  activity_entropy double precision NOT NULL,
  inactivity_percentage double precision NOT NULL,
  user_uid text NOT NULL,
  cognitive_score double precision,
  cognitive_decision text,
  CONSTRAINT Activity_Data_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT activity_data_analysis_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.Activity_Data_Z_Scores (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  activity_data_analysis_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  daily_active_minutes_z_score double precision,
  CONSTRAINT Activity_Data_Z_Scores_pkey PRIMARY KEY (id),
  CONSTRAINT Activity_Data_Z_Scores_activity_data_analysis_id_fkey FOREIGN KEY (activity_data_analysis_id) REFERENCES public.Activity_Data_Analysis(id)
);
CREATE TABLE public.Activity_Distribution_Per_Day_Section_Analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  day_section text NOT NULL,
  in_vehicle double precision NOT NULL,
  on_bicycle double precision NOT NULL,
  on_foot double precision NOT NULL,
  still double precision NOT NULL,
  tilting double precision NOT NULL,
  unknown double precision NOT NULL,
  activity_data_analysis_id uuid NOT NULL,
  CONSTRAINT Activity_Distribution_Per_Day_Section_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT activity_distribution_per_day_se_activity_data_analysis_id_fkey FOREIGN KEY (activity_data_analysis_id) REFERENCES public.Activity_Data_Analysis(id)
);
CREATE TABLE public.App_Usage_Analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  app_name text NOT NULL,
  time_used_sec double precision NOT NULL,
  daily_interaction_data_analysis_id uuid NOT NULL,
  CONSTRAINT App_Usage_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT app_usage_analysis_daily_interaction_data_analysis_id_fkey FOREIGN KEY (daily_interaction_data_analysis_id) REFERENCES public.Device_Interaction_Data_Analysis(id)
);
CREATE TABLE public.Baseline_Metrics (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_uid text NOT NULL,
  date_created date NOT NULL,
  metric_name text NOT NULL,
  baseline_mean double precision,
  baseline_std double precision,
  sess_start_date date NOT NULL,
  sess_end_date date NOT NULL,
  baseline_median double precision,
  baseline_mad double precision,
  data_category text NOT NULL,
  CONSTRAINT Baseline_Metrics_pkey PRIMARY KEY (id),
  CONSTRAINT Baseline_Metrics_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.Call_Data_Analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  day_analyzed date NOT NULL,
  missed_call_ratio double precision NOT NULL,
  night_call_ratio double precision NOT NULL,
  day_call_ratio double precision NOT NULL,
  avg_call_duration double precision NOT NULL,
  total_calls_in_a_day integer NOT NULL,
  user_uid text NOT NULL,
  cognitive_score double precision,
  cognitive_decision text,
  CONSTRAINT Call_Data_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT call_data_analysis_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.Call_Data_Z_Scores (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  call_data_analysis_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  missed_call_ratio_z_score double precision,
  avg_call_duration_z_score double precision,
  total_calls_in_a_day_z_score double precision,
  CONSTRAINT Call_Data_Z_Scores_pkey PRIMARY KEY (id),
  CONSTRAINT Call_Data_Z_Scores_call_data_analysis_id_fkey FOREIGN KEY (call_data_analysis_id) REFERENCES public.Call_Data_Analysis(id)
);
CREATE TABLE public.Circadian_Screen_Time_Analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  day_section text NOT NULL,
  duration double precision NOT NULL,
  percentage real NOT NULL,
  daily_interaction_data_analysis_id uuid NOT NULL,
  CONSTRAINT Circadian_Screen_Time_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT circadian_screen_time_analysi_daily_interaction_data_analy_fkey FOREIGN KEY (daily_interaction_data_analysis_id) REFERENCES public.Device_Interaction_Data_Analysis(id)
);
CREATE TABLE public.Cognitive_Processing_Efficiency_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  analysis_date date,
  session_uid text NOT NULL,
  value double precision NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Cognitive_Processing_Efficiency_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Cognitive_Processing_Efficiency_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Cognitive_Processing_Efficiency_D_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.Cognitive_Processing_Index_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  analysis_date date NOT NULL,
  session_uid text NOT NULL,
  value double precision NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Cognitive_Processing_Index_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Cognitive_Processing_Index_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Cognitive_Processing_Index_Data_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.Correction_Efficiency_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  analysis_date date NOT NULL,
  session_uid text NOT NULL,
  value double precision NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Correction_Efficiency_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Correction_Efficiency_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Correction_Efficiency_Data_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.Daily_Analyses (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  day_analyzed date NOT NULL,
  analysis_date date NOT NULL,
  user_uid text NOT NULL,
  CONSTRAINT Daily_Analyses_pkey PRIMARY KEY (id),
  CONSTRAINT Daily_Analyses_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.Daily_Analysis_Typing_Stats (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  std_pi double precision,
  mean_pi double precision,
  std_cpe double precision,
  mean_cpe double precision,
  std_cpi double precision,
  mean_cpi double precision,
  std_ce double precision,
  mean_ce double precision,
  std_eto double precision,
  mean_eto double precision,
  std_npr double precision,
  mean_npr double precision,
  std_ppr double precision,
  mean_ppr double precision,
  std_trs double precision,
  mean_trs double precision,
  analysis_id bigint NOT NULL UNIQUE,
  percentage_critical double precision DEFAULT '0'::double precision,
  percentage_excellent double precision DEFAULT '0'::double precision,
  percentage_normal double precision DEFAULT '0'::double precision,
  percentage_very_bad double precision DEFAULT '0'::double precision,
  percentage_very_good double precision DEFAULT '0'::double precision,
  total_typing_cognitive_score double precision NOT NULL CHECK (total_typing_cognitive_score >= 0.0::double precision),
  CONSTRAINT Daily_Analysis_Typing_Stats_pkey PRIMARY KEY (id),
  CONSTRAINT Daily_Analysis_Data_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.Daily_Analyses(id)
);
CREATE TABLE public.Device_Interaction_Data_Analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  day_analyzed date NOT NULL,
  total_screen_time_sec double precision NOT NULL,
  total_low_light_time_sec double precision NOT NULL,
  total_device_drop_events integer NOT NULL,
  user_uid text NOT NULL,
  cognitive_score double precision,
  cognitive_decision text,
  CONSTRAINT Device_Interaction_Data_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT device_interaction_data_analysis_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.Device_Interaction_Data_Z_Scores (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  device_interaction_data_analysis_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  screen_time_z_score double precision,
  low_light_day_time_z_score double precision,
  device_drop_events_z_score double precision,
  CONSTRAINT Device_Interaction_Data_Z_Scores_pkey PRIMARY KEY (id),
  CONSTRAINT Device_Interaction_Data_Z_Sco_device_interaction_data_anal_fkey FOREIGN KEY (device_interaction_data_analysis_id) REFERENCES public.Device_Interaction_Data_Analysis(id)
);
CREATE TABLE public.Effort_To_Output_Ratio_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  analysis_date date NOT NULL,
  session_uid text NOT NULL,
  value double precision NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Effort_To_Output_Ratio_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Effort_To_Output_Ratio_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Effort_To_Output_Ratio_Data_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.GPS_Data_Analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  day_analyzed date NOT NULL,
  total_time_spend_in_home_seconds double precision,
  total_time_spend_travelling_seconds double precision,
  total_time_spend_out_of_home_seconds double precision,
  total_distance_traveled_km double precision,
  average_time_spend_in_locations_hours double precision,
  number_of_unique_locations double precision,
  number_of_locations_total double precision,
  first_move_timestamp_after_3am timestamp with time zone,
  entropy double precision,
  time_period_active double precision,
  user_uid text NOT NULL,
  cognitive_score double precision,
  cognitive_decision text,
  CONSTRAINT GPS_Data_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT gps_data_analysis_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.GPS_Data_Z_Scores (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  gps_data_analysis_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  total_time_spend_in_home_seconds_z_score double precision,
  total_time_spend_travelling_seconds_z_score double precision,
  total_time_spend_out_of_home_seconds_z_score double precision,
  total_distance_traveled_km_z_score double precision,
  average_time_spend_in_locations_hours_z_score double precision,
  number_of_unique_locations_z_score double precision,
  convex_hull_area_m2_z_score double precision,
  sde_area_m2_z_score double precision,
  max_distance_from_home_time_z_score double precision,
  entropy_z_score double precision,
  CONSTRAINT GPS_Data_Z_Scores_pkey PRIMARY KEY (id),
  CONSTRAINT GPS_Data_Z_Scores_gps_data_analysis_id_fkey FOREIGN KEY (gps_data_analysis_id) REFERENCES public.GPS_Data_Analysis(id)
);
CREATE TABLE public.GPS_Key_Locations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  key_location_id double precision NOT NULL,
  latitude double precision,
  longitude double precision,
  total_time_spent_seconds double precision,
  num_of_gps_events double precision,
  key_loc_type text,
  gps_data_analysis_id uuid NOT NULL,
  CONSTRAINT GPS_Key_Locations_pkey PRIMARY KEY (id),
  CONSTRAINT gps_key_locations_gps_data_analysis_id_fkey FOREIGN KEY (gps_data_analysis_id) REFERENCES public.GPS_Data_Analysis(id)
);
CREATE TABLE public.GPS_Spatial_Features (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  convex_hull_area_m2 double precision,
  convex_hull_perimeter_m double precision,
  gravimetric_compactness double precision,
  sde_mean_center_lon double precision,
  sde_mean_center_lat double precision,
  sde_width_m double precision,
  sde_height_m double precision,
  sde_angle_deg double precision,
  sde_area_m2 double precision,
  max_distance_from_home_km double precision,
  max_distance_timestamp timestamp with time zone,
  max_distance_lat double precision,
  max_distance_lon double precision,
  gps_data_analysis_id uuid NOT NULL,
  CONSTRAINT GPS_Spatial_Features_pkey PRIMARY KEY (id),
  CONSTRAINT gps_spatial_features_gps_data_analysis_id_fkey FOREIGN KEY (gps_data_analysis_id) REFERENCES public.GPS_Data_Analysis(id)
);
CREATE TABLE public.GPS_Transitions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  key_loc_start_id real NOT NULL,
  key_loc_end_id real NOT NULL,
  start_time_of_transition timestamp with time zone NOT NULL,
  end_time_of_transition timestamp with time zone NOT NULL,
  total_time_travel_seconds double precision,
  total_distance_traveled_km double precision,
  total_gps_events_in_transition_cluster double precision,
  gps_data_analysis_id uuid NOT NULL,
  CONSTRAINT GPS_Transitions_pkey PRIMARY KEY (id),
  CONSTRAINT gps_transitions_gps_data_analysis_id_fkey FOREIGN KEY (gps_data_analysis_id) REFERENCES public.GPS_Data_Analysis(id)
);
CREATE TABLE public.Included_Typing_Sessions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  day_analyzed date NOT NULL,
  typing_session_id text NOT NULL UNIQUE,
  analysis_id bigint NOT NULL,
  CONSTRAINT Included_Typing_Sessions_pkey PRIMARY KEY (id),
  CONSTRAINT Included_Sessions_typing_session_id_fkey FOREIGN KEY (typing_session_id) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Included_Sessions_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.Daily_Analyses(id)
);
CREATE TABLE public.Net_Production_Rate_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  analysis_date date NOT NULL,
  session_uid text NOT NULL,
  value double precision NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Net_Production_Rate_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Net_Production_Rate_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Net_Production_Rate_Data_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.Pause_To_Production_Ratio_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  analysis_date date NOT NULL,
  session_uid text NOT NULL,
  value double precision NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Pause_To_Production_Ratio_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Pause_To_Production_Ratio_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Pause_To_Production_Ratio_Data_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.Pressure_Intensity_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  session_uid text NOT NULL UNIQUE,
  value double precision NOT NULL,
  analysis_date date NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Pressure_Intensity_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Pressure_Intensity_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Pressure_Intensity_Data_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.Sleep_Data_Analysis (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  estimated_start_date_time timestamp without time zone NOT NULL,
  estimated_end_date_time timestamp without time zone NOT NULL,
  total_duration double precision NOT NULL,
  actual_duration double precision NOT NULL,
  sleep_screen_time double precision,
  norm_total_sleep double precision,
  norm_sleep_efficiency double precision,
  norm_screen_time double precision,
  norm_time_alignment double precision,
  sleep_quality_score double precision,
  user_uid text NOT NULL,
  type text NOT NULL,
  day_analyzed date NOT NULL,
  cognitive_score double precision,
  cognitive_decision text,
  CONSTRAINT Sleep_Data_Analysis_pkey PRIMARY KEY (id),
  CONSTRAINT Detected_Sleeps_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.Sleep_Data_Z_Scores (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  sleep_data_analysis_id bigint NOT NULL UNIQUE,
  sqs_z_score double precision,
  sleep_time_z_score double precision,
  sleep_start_time_z_score double precision,
  sleep_end_time_z_score double precision,
  CONSTRAINT Sleep_Data_Z_Scores_pkey PRIMARY KEY (id),
  CONSTRAINT Sleep_Data_Z_Scores_sleep_data_analysis_id_fkey FOREIGN KEY (sleep_data_analysis_id) REFERENCES public.Sleep_Data_Analysis(id)
);
CREATE TABLE public.Typing_Rhythm_Stability_Data (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  analysis_date date NOT NULL,
  session_uid text NOT NULL,
  value double precision NOT NULL,
  modified_z_score double precision,
  included_baseline_metric bigint,
  CONSTRAINT Typing_Rhythm_Stability_Data_pkey PRIMARY KEY (id),
  CONSTRAINT Typing_Rhythm_Stabiltiy_Data_session_uid_fkey FOREIGN KEY (session_uid) REFERENCES public.Typing_Sessions(session_uid),
  CONSTRAINT Typing_Rhythm_Stability_Data_included_baseline_metric_fkey FOREIGN KEY (included_baseline_metric) REFERENCES public.Baseline_Metrics(id)
);
CREATE TABLE public.Typing_Sessions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  session_uid text NOT NULL UNIQUE,
  user_uid text NOT NULL,
  session_date date NOT NULL,
  cognitive_score double precision,
  cognitive_decision text,
  CONSTRAINT Typing_Sessions_pkey PRIMARY KEY (id),
  CONSTRAINT Typing_Sessions_user_uid_fkey FOREIGN KEY (user_uid) REFERENCES public.Users(user_uid)
);
CREATE TABLE public.Users (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  user_uid text NOT NULL UNIQUE,
  user_email text,
  app_origin text,
  CONSTRAINT Users_pkey PRIMARY KEY (id)
);