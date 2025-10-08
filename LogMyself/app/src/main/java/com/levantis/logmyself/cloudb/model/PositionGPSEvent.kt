package com.levantis.logmyself.cloudb.model

import com.google.firebase.Timestamp

data class PositionGPSEvent(
    val latitude: Double,
    val longitude: Double,
    val accuracy: Float,
    val altitude: Double,
    val speed: Float,
    val bearing: Float,
    val speedAccuracyMetersPerSecond: Float,
    val timestampNow: Timestamp,
)
