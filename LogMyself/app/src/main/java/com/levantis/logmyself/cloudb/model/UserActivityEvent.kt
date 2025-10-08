package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class UserActivityEvent(
    val activityType: String,
    val confidence: Int,
    val timestamp: Timestamp,
)
