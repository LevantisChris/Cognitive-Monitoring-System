package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class ScreenTimeEvent(
    var timeStart: Timestamp,
    var timeEnd: Timestamp,
    var duration: Long
)
