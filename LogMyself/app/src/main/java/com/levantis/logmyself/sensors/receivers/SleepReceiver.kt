package com.levantis.logmyself.sensors.receivers

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import android.view.WindowManager
import com.google.android.gms.location.ActivityRecognitionResult
import com.google.android.gms.location.SleepClassifyEvent
import com.google.android.gms.location.SleepSegmentEvent
import com.levantis.logmyself.sensors.SensorsDataManager
import com.levantis.logmyself.sensors.detectors.UsageStatsDetector
import java.time.LocalDateTime

/*
* Receiver to handle all sleep related events.
* **/

class SleepReceiver : BroadcastReceiver() {

    fun onSleepClassifyEventInternal(
        context: Context,
        confidence: Int,
        light: Int,
        motion: Int,
        timestampNow: LocalDateTime,
        timestampPrevious: LocalDateTime
    ) {
        val usageStatsDetector: UsageStatsDetector = UsageStatsDetector(context) // get usage stats additional data
        Log.d("SleepReceiver", "Sleep classify event received: confidence=$confidence, light=$light, motion=$motion, timestampNow=$timestampNow, timestampPrevious=$timestampPrevious")
        SensorsDataManager.reportSleepClassifyData(
            confidence,
            light,
            motion,
            timestampNow,
            timestampPrevious,
            usageStatsDetector.getScreenOnDuration(
                timestampPrevious.atZone(java.time.ZoneId.systemDefault()).toInstant().toEpochMilli(),
                timestampNow.atZone(java.time.ZoneId.systemDefault()).toInstant().toEpochMilli()
            ),
            usageStatsDetector.getUsedApps(
                timestampPrevious.atZone(java.time.ZoneId.systemDefault()).toInstant().toEpochMilli(),
                timestampNow.atZone(java.time.ZoneId.systemDefault()).toInstant().toEpochMilli()
            ),
        )
    }

    override fun onReceive(context: Context, intent: Intent) {
        // Handle SleepSegmentEvent
        /*
        * Represents the result of segmenting sleep after the user is awake
        * */
        if (SleepSegmentEvent.hasEvents(intent)) {
            val segmentEvents = SleepSegmentEvent.extractEvents(intent)
            for (event in segmentEvents) {
                Log.d("SleepReceiver",
                    "Sleep segment (SleepSegmentEvent): ${event.startTimeMillis} - ${event.endTimeMillis}")
            }
        }

        // Handle SleepClassifyEvent
        /**
         * Represents a sleep classification event including the classification timestamp, the sleep confidence,
         * and the supporting data such as device motion and ambient light level. Classification events are
         * reported at a regular intervals, such as every 10 minutes.
         * */
        if (SleepClassifyEvent.hasEvents(intent)) {
            val classifyEvents = SleepClassifyEvent.extractEvents(intent)
            for (event in classifyEvents) {
                var dateTimeNow = LocalDateTime.now()
                if (SensorsDataManager.getPreviousClassifyEventTime() == null) {
                    SensorsDataManager.setPreviousClassifyEventTime(dateTimeNow)
                    Log.d(
                        "SleepReceiver",
                        "Sleep classify (SleepClassifyEvent - INITIAL): \nconfidence=${event.confidence}, \n" +
                                "light=${event.light}\n, Motion=${event.motion}\n, " +
                                "System timestamp=${event.timestampMillis}\n" + ", Timestamp=${dateTimeNow}\n")
                } else {
                    onSleepClassifyEventInternal(
                        context = context,
                        confidence = event.confidence,
                        light = event.light,
                        motion = event.motion,
                        timestampNow = dateTimeNow,
                        timestampPrevious = SensorsDataManager.getPreviousClassifyEventTime()!!
                    )
                    SensorsDataManager.setPreviousClassifyEventTime(dateTimeNow)
                }
            }
        }
    }
}