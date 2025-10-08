package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

@Serializable
data class ActivityDistributionPerDaySectionAnalysis (
    // Activity_Distribution_Per_Day_Section_Analysis Table Fields
    val day_section: String?,
    val in_vehicle: Double?,
    val on_bicycle: Double?,
    val on_foot: Double?,
    val still: Double?,
    val tilting: Double?,
    val unknown: Double?,
)

@Serializable
data class ActivityDataAnalysisBase (
    val id: String,
    val activity_entropy: Double?,
    val inactivity_percentage: Double?,
    val daily_active_minutes: Double?,
    val cognitive_score: Double?,
    val cognitive_decision: String?,
)

@Serializable
data class ActivityDataAnalysisInfo (
    // Activity_Data_Analysis Table Fields
    val id: String?,
    val activity_entropy: Double?,
    val inactivity_percentage: Double?,
    val daily_active_minutes: Double?,
    val cognitive_score: Double?,
    val cognitive_decision: String?,
    // Activity_Distribution_Per_Day_Section_Analysis Table Fields
    val activity_distribution_per_day_section_analysis: List<ActivityDistributionPerDaySectionAnalysis>?,
)