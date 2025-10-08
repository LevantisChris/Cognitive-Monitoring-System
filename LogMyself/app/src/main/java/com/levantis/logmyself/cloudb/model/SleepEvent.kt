package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class SleepEvent(
    val confidence: Int,
    val light: Int,
    val motion: Int,
    val timestampNow: Timestamp,
    val timestampPrevious: Timestamp,
    val screenOnDuration: Long,
    val usedApps: Map<String, Long>,
)
