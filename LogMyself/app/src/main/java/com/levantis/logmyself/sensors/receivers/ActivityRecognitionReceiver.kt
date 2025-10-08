package com.levantis.logmyself.sensors.receivers

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.google.android.gms.location.ActivityRecognitionResult
import com.google.android.gms.location.ActivityTransition
import com.google.android.gms.location.ActivityTransitionEvent
import com.google.android.gms.location.DetectedActivity
import com.levantis.logmyself.sensors.SensorsDataManager
import java.time.LocalDateTime

class ActivityRecognitionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (ActivityRecognitionResult.hasResult(intent)) {
            val result = ActivityRecognitionResult.extractResult(intent)
            val probableActivity = result?.mostProbableActivity

            if (probableActivity != null) {
                Log.d("ActivityRecognitionReceiver", "Activity detected (general): ${probableActivity.type}")
                val type = getActivityName(probableActivity.type)
                val confidence = probableActivity.confidence
                Log.d("ActivityUpdate", "Activity: $type, Confidence: $confidence")
                // Save to database
                SensorsDataManager.reportActivityEvent(
                    type,
                    confidence,
                    LocalDateTime.now()
                )
            }
        } else if (intent.hasExtra("com.google.android.gms.location.ACTIVITY_TRANSITION_EVENT")) {
            val transitionEvents = intent.getParcelableArrayListExtra<ActivityTransitionEvent>(
                "com.google.android.gms.location.ACTIVITY_TRANSITION_EVENT"
            )
            transitionEvents?.forEach { event ->
                val activityType = getActivityName(event.activityType)
                val transitionType = when (event.transitionType) {
                    ActivityTransition.ACTIVITY_TRANSITION_ENTER -> "ENTER"
                    ActivityTransition.ACTIVITY_TRANSITION_EXIT -> "EXIT"
                    else -> "UNKNOWN"
                }
                Log.d("ActivityTransition", "Activity: $activityType, Transition: $transitionType")
            }
        }
    }

    private fun getActivityName(type: Int): String {
        return when (type) {
            DetectedActivity.IN_VEHICLE -> "in_vehicle"
            DetectedActivity.ON_BICYCLE -> "on_bicycle"
            DetectedActivity.ON_FOOT -> "on_foot"
            DetectedActivity.RUNNING -> "running"
            DetectedActivity.STILL -> "still"
            DetectedActivity.TILTING -> "tilting"
            DetectedActivity.WALKING -> "walking"
            else -> "unknown"
        }
    }
}
