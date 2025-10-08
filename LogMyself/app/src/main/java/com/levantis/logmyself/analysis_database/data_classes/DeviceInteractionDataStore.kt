package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

@Serializable
data class CircadianScreenTimeAnalysis (
    val day_section: String?,
    val duration: Double?,
    val percentage: Double?,
)

@Serializable
data class DeviceInteractionAnalysisBase (
    val id: String,
    val total_screen_time_sec: Double?,
    val total_low_light_time_sec: Double?,
    val total_device_drop_events: Int?,
    val cognitive_score: Double?,
    val cognitive_decision: String?,
)

@Serializable
data class DeviceInteractionAnalysisInfo (
    val id: String?,
    val total_screen_time_sec: Double?,
    val total_low_light_time_sec: Double?,
    val total_device_drop_events: Int?,
    val circadian_screen_time_analysis: CircadianScreenTimeAnalysis?,
    val cognitive_score: Double?,
    val cognitive_decision: String?,
)