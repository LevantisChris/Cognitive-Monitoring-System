package com.levantis.logmyself.sensors.listeners

import android.content.Context
import com.google.android.gms.location.SleepClassifyEvent
import com.google.android.gms.location.SleepSegmentEvent
import java.time.LocalDateTime

interface SleepListener {

    fun onSleepSegmentEvent() {}
    fun onSleepClassifyEvent(
        context: Context,
        confidence: Int,
        light: Int,
        motion: Int,
        timestampNow: LocalDateTime,
        timestampPrevious: LocalDateTime) {}
    fun onSleepTrackingStarted() {}
    fun onSleepTrackingStopped() {}
    fun onSleepTrackingError(reason: String) {}

}