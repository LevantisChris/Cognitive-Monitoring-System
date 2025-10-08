package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class LowLightDetectionEvent(
    val startTime: Timestamp,
    val endTime: Timestamp,
    val duration: Long,
    val validStartTime: Long,
    val validEndTime: Long,
    val lowLightThreshold: Float
)
