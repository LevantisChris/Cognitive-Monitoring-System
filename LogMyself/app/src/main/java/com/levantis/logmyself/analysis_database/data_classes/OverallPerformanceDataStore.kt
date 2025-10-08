package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

// Data classes for cognitive scores
@Serializable
data class CognitiveScoresSummary(
    val userUid: String,
    val analysisDate: String,
    val typingCognitiveScore: Double? = null,
    val sleepCognitiveScore: Double? = null,
    val activityCognitiveScore: Double? = null,
    val callCognitiveScore: Double? = null,
    val gpsCognitiveScore: Double? = null,
    val deviceInteractionCognitiveScore: Double? = null,
    val typingSessionCognitiveScore: Double? = null,
    val meanCognitiveScore: Double? = null,
    val totalCognitiveDecision: String? = null,
    val totalScoresAvailable: Int = 0
)

@Serializable
data class SleepCognitiveScore(
    val cognitive_score: Double?,
    val day_analyzed: String,
    val user_uid: String
)

@Serializable
data class ActivityCognitiveScore(
    val cognitive_score: Double?,
    val day_analyzed: String,
    val user_uid: String
)

@Serializable
data class CallCognitiveScore(
    val cognitive_score: Double?,
    val day_analyzed: String,
    val user_uid: String
)

@Serializable
data class GPSCognitiveScore(
    val cognitive_score: Double?,
    val day_analyzed: String,
    val user_uid: String
)

@Serializable
data class DeviceInteractionCognitiveScore(
    val cognitive_score: Double?,
    val day_analyzed: String,
    val user_uid: String
)

//@Serializable
//data class TypingSessionCognitiveScore(
//    val cognitive_score: Double?,
//    val session_date: String,
//    val user_uid: String
//)

@Serializable
data class DailyAnalysis(
    val id: Int,
    val user_uid: String,
    val day_analyzed: String
)

@Serializable
data class TypingStats(
    val total_typing_cognitive_score: Double?,
    val analysis_id: Long
)
