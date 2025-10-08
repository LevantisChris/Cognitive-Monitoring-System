package com.levantis.logmyself.sensors.detectors

import android.Manifest
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.util.Log
import com.google.android.gms.location.ActivityRecognition
import com.google.android.gms.location.SleepSegmentRequest
import com.levantis.logmyself.sensors.listeners.SleepListener
import com.levantis.logmyself.sensors.receivers.SleepReceiver
import com.levantis.logmyself.utils.PermissionsManager

class SleepDetector(
    private val context: Context,
    private val listener: SleepListener
) {
    private val activityRecognitionClient = ActivityRecognition.getClient(context)

    fun startSleepTracking() {
        val pendingIntent = createPendingIntent()

        // Create a SleepSegmentRequest
        // --
        /* NOTE: getDefaultSleepSegmentRequest()
        *  Creates a default request that registers
        *  for both SleepSegmentEvent and SleepClassifyEvent data.
        */
        val request = SleepSegmentRequest.getDefaultSleepSegmentRequest()
        // Request sleep segment updates
        if (PermissionsManager.isPermissionGranted(context, Manifest.permission.ACTIVITY_RECOGNITION)) {
            /* Try-catch because it might be revoked */
            try {
                activityRecognitionClient.requestSleepSegmentUpdates(pendingIntent, request)
                    .addOnSuccessListener {
                        listener.onSleepTrackingStarted()
                        Log.d("SleepDetector", "(requestSleepSegmentUpdates) Started successfully")
                    }
                    .addOnFailureListener { e ->
                        listener.onSleepTrackingError("UNKNOWN_ERROR")
                        Log.e("SleepDetector", "(requestSleepSegmentUpdates) Failed to start", e)
                    }
                activityRecognitionClient.requestActivityUpdates(60000L, pendingIntent)
                    .addOnSuccessListener {
                        Log.d("SleepDetector", "(requestActivityUpdates) Started successfully")
                    }
                    .addOnFailureListener { e ->
                        Log.d("SleepDetector", "(requestActivityUpdates) Failed to start", e)
                    }
            } catch (e: SecurityException) {
                listener.onSleepTrackingError("UNKNOWN_ERROR")
                Log.e("SleepDetector", "SecurityException: Permission might have been revoked", e)
            }
        } else {
            listener.onSleepTrackingError("DENIED_PERMISSION")
            Log.e("SleepDetector", "Activity recognition permission not granted")
        }
    }

    fun stopSleepTracking() {
        val pendingIntent = createPendingIntent()

        if (PermissionsManager.isPermissionGranted(context, Manifest.permission.ACTIVITY_RECOGNITION)) {
            try {
                activityRecognitionClient.removeSleepSegmentUpdates(pendingIntent)
                    .addOnSuccessListener {
                        Log.d("SleepDetector", "Sleep segment updates removed successfully")
                        activityRecognitionClient.removeActivityUpdates(pendingIntent)
                            .addOnSuccessListener {
                                listener.onSleepTrackingStopped()
                                Log.d("SleepDetector", "Activity updates removed successfully")
                            }
                            .addOnFailureListener { e ->
                                listener.onSleepTrackingError("UNKNOWN_ERROR")
                                Log.e("SleepDetector", "Failed to remove activity updates", e)
                            }
                    }
                    .addOnFailureListener { e ->
                        listener.onSleepTrackingError("UNKNOWN_ERROR")
                        Log.e("SleepDetector", "Failed to remove sleep segment updates", e)
                    }
            } catch (e: SecurityException) {
                listener.onSleepTrackingError("UNKNOWN_ERROR")
                Log.e("SleepDetector", "SecurityException: Permission might have been revoked", e)
            }
        } else {
            listener.onSleepTrackingError("DENIED_PERMISSION")
            Log.e("SleepDetector", "Activity recognition permission not granted")
        }
    }

    private fun createPendingIntent(): PendingIntent {
        val intent = Intent(context, SleepReceiver::class.java)
        return PendingIntent.getBroadcast(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )
    }


}