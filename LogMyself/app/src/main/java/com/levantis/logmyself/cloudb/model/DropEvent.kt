package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class DropEvent(
    val timestamp: Timestamp,
    val detectedMagnitude: Long,
    val detectedFallDuration: Long
)
