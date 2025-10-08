package com.levantis.logmyself.cloudb.model

/* Used apps correspond to a sleep event */

data class UsedAppsEvent(
    val appName: String,
    val usageDuration: Long
)
