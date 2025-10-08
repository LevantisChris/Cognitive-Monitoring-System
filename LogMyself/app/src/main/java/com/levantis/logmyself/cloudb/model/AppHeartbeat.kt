package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class AppHeartbeat(
    val timestamp: Timestamp,
    val status: Boolean // alive: true, dead: false
)
