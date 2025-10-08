package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class CallEvent(
    val callType: Int?,
    val callDescription: String?,
    val callDuration: Int?,
    val callDate: Timestamp,
)
