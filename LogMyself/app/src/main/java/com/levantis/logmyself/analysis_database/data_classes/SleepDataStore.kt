package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

@Serializable
data class SleepDataAnalysisInfo(
    val estimated_start_date_time: String,
    val estimated_end_date_time: String,
    val total_duration: Double,
    val actual_duration: Double,
    val sleep_screen_time: Double?,
    val sleep_quality_score: Double? = null,
    val type: String,
    val cognitive_score: Double? = null,
    val cognitive_decision: String? = null
)

@Serializable
data class DailySleepSummary(
    // Main sleep info (from the "main" type record)
    val estimated_start_date_time: String,
    val estimated_end_date_time: String,
    val total_duration: Double, // Combined duration of main sleep + all naps
    val actual_duration: Double,
    val sleep_screen_time: Double?,
    val sleep_quality_score: Double? = null, // From main sleep only (naps don't have this)
    val cognitive_score: Double? = null,
    val cognitive_decision: String? = null,
    
    // Additional aggregated info
    val main_sleep_duration: Double,
    val total_nap_duration: Double,
    val number_of_naps: Int,
    val nap_details: List<SleepDataAnalysisInfo> = emptyList()
)