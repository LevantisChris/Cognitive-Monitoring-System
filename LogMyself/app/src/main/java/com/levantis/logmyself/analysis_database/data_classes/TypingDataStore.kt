package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

@Serializable
data class TypingCategoryPercentages (
    val analysis_id: Long,
    val percentage_critical: Double,
    val percentage_very_bad: Double,
    val percentage_normal: Double,
    val percentage_very_good: Double,
    val percentage_excellent: Double
)

@Serializable
data class LogBoardUser(
    val user_uid: String
)