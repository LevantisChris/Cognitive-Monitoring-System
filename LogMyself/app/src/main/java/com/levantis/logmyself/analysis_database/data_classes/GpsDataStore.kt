package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

@Serializable
data class KeyLocationInfo(
    val key_location_id: Int,
    val latitude: Double,
    val longitude: Double,
    val key_loc_type: String
)

@Serializable
data class GPSDataAnalysisBase(
    val id: String,
    val total_time_spend_in_home_seconds: Double?,
    val time_period_active: Int?,
    val total_time_spend_travelling_seconds: Double?,
    val number_of_unique_locations: Int?,
    val first_move_timestamp_after_3am: String?,
    val average_time_spend_in_locations_hours: Double?,
    val cognitive_decision: String?,
    val cognitive_score: Double?
)

@Serializable
data class GPSSpatialFeatures(
    val max_distance_timestamp: String?
)

@Serializable
data class GPSDataAnalysisInfo(
    // GPS_Data_Analysis Table data
    val total_time_spend_in_home_seconds: Double? = null,
    val time_period_active: Int? = null,
    val total_time_spend_travelling_seconds: Double? = null,
    val number_of_unique_locations: Int? = null,
    val first_move_timestamp_after_threeAm: String? = null,
    val average_time_spend_in_locations_hours: Double? = null,
    val cognitive_decision: String? = null,
    val cognitive_score: Double? = null,
    // GPS_Spatial_Features Table data
    val max_distance_timestamp: String? = null, // Timestamp where the user reached the furthest distance from home
    // GPS_Key_Locations Table data
    val coordsOfKeyLocs: List<KeyLocationInfo>? = null
)