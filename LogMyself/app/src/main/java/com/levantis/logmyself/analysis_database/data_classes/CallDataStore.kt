package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

@Serializable
data class CallDataAnalysisInfo (
    // Call_Data_Analysis Table Fields
    val day_call_ratio: Double?,
    val night_call_ratio: Double?,
    val avg_call_duration: Double?,
    val total_calls_in_a_day: Int?,
    val missed_call_ratio: Double?,
    val cognitive_score: Double?,
    val cognitive_decision: String?,
)