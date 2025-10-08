package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class PowerChargingEvent(
    val startTime: Timestamp,
    val endTime: Timestamp
)
