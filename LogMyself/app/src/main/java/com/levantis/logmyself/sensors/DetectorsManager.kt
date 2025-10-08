package com.levantis.logmyself.sensors

import android.Manifest
import android.content.Context
import android.util.Log
import androidx.annotation.RequiresPermission
import com.levantis.logmyself.sensors.detectors.CallStateDetector
import com.levantis.logmyself.sensors.listeners.DropListener
import com.levantis.logmyself.sensors.listeners.LightListener
import com.levantis.logmyself.sensors.listeners.SleepListener
import com.levantis.logmyself.sensors.detectors.DropDetector
import com.levantis.logmyself.sensors.detectors.LowLightDetector
import com.levantis.logmyself.sensors.detectors.NotificationDetector
import com.levantis.logmyself.sensors.detectors.ProximityDetector
import com.levantis.logmyself.sensors.detectors.SleepDetector
import com.levantis.logmyself.sensors.utils.FusionLocationProvider
import java.time.LocalDateTime

/**
 * Centralized class to manage all sensors related tasks and functions
 * NOTE: Try to only have one instance of this class in the app
 * */

class DetectorsManager(
    private val context: Context
) {
    /* Activations states */
    private var activeDropDetector: Boolean = false
    private var activeLowLightDetector: Boolean = false
    private var activeSleepDetector: Boolean = false
    private var activeCallDetector: Boolean = false
    private var activeFusionLoc: Boolean = false
    private var activeProximityDetector: Boolean = false
    private var activeNotificationDetector: Boolean = false

    private val dropDetector: DropDetector = DropDetector(
        context, object : DropListener {
        override fun onDropDetected(timespamp: LocalDateTime, detectedMagnitude: Long, detectedFallDuration: Long) {
            Log.d("DropDetector", "Drop detected")
            SensorsDataManager.reportDropData(
                timespamp, detectedMagnitude, detectedFallDuration
            )
        }
        override fun onDropFreefallDetected() {
            //addSensorData("Freefall", System.currentTimeMillis(), 1.0f)
        }
        override fun onDropSensorUnavailable() {
            // Handle sensor unavailable
        }
        override fun onDropMonitoringStarted() {
            // Handle monitoring started
        }
        override fun onDropMonitoringStopped() {
            // Handle monitoring stopped
        }
    })

    private val lowLightDetector: LowLightDetector = LowLightDetector(
        context, object : LightListener {
            override fun onLightSensorUnavailable() {
                Log.e("LowLightDetector", "Light sensor not available")
            }
            override fun onLightDetectionNotValid() {
                Log.e("LowLightDetector", "Light detection not valid")
            }
            override fun onLowLevelLightDetected() {
                Log.d("LowLightDetector", "Low light detected")
            }
            override fun onLightMonitoringStarted() {
                Log.d("LowLightDetector", "Light monitoring started")
            }
            override fun onLightMonitoringStopped() {
                Log.d("LowLightDetector", "Light monitoring stopped")
            }
        },
    )

    private val sleepDetector: SleepDetector = SleepDetector(
        context, object : SleepListener {
            override fun onSleepTrackingStarted() {
                Log.d("DetectorsManager", "Sleep tracking started")
            }
            override fun onSleepTrackingStopped() {
                Log.d("DetectorsManager", "Sleep tracking stopped")
            }
            override fun onSleepTrackingError(reason: String) {
                if(reason == "DENIED_PERMISSION") {
                    Log.e("DetectorsManager", "Sleep tracking permission denied: $reason")
                    //TODO: Add it to the DB
                } else {
                    Log.e("DetectorsManager", "Sleep tracking error: $reason")
                }
            }
        }
    )

    private val callStateDetector: CallStateDetector = CallStateDetector(context);

    private val fusionLocationProvider: FusionLocationProvider = FusionLocationProvider(context)

    private val proximityDetector: ProximityDetector = ProximityDetector(context)

    private val notificationDetector: NotificationDetector = NotificationDetector()

    fun startMonitoringNotificationDetector() {
        if(activeNotificationDetector == false) {
            Log.i("DetectorsManager", "Notification detection is OFF - Starting notification detection")
            activeNotificationDetector = true
            notificationDetector.startMonitoring(context)
        } else {
            Log.i("DetectorsManager", "Notification detection is already ON - Not starting notification detection")
        }
    }

    fun stopMonitoringNotificationDetector() {
        if(activeNotificationDetector == true) {
            Log.i("DetectorsManager", "Notification detection is ON - Stopping notification detection")
            activeNotificationDetector = false
            notificationDetector.stopMonitoring(context)
        } else {
            Log.i("DetectorsManager", "Notification detection is already OFF - Not stopping notification detection")
        }
    }

    fun startMonitoringProximityDetector() {
        if(activeProximityDetector == false) {
            Log.i("DetectorsManager", "Proximity detection is OFF - Starting proximity detection")
            activeProximityDetector = true
            proximityDetector.startMonitoring()
        } else {
            Log.i("DetectorsManager", "Proximity detection is already ON - Not starting proximity detection")
        }
    }

    fun stopMonitoringProximityDetector() {
        if(activeProximityDetector == true) {
            Log.i("DetectorsManager", "Proximity detection is ON - Stopping proximity detection")
            activeProximityDetector = false
            proximityDetector.stopMonitoring()
        } else {
            Log.i("DetectorsManager", "Proximity detection is already OFF - Not stopping proximity detection")
        }
    }

    @RequiresPermission(allOf = [Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION])
    fun startMonitoringFusionLocationDetector() {
        if(activeFusionLoc == false) {
            Log.i("DetectorsManager", "Fusion location detection is OFF - Starting fusion location detection")
            activeFusionLoc = true
            fusionLocationProvider.startLocationUpdates()
        } else {
            Log.i("DetectorsManager", "Fusion location detection is already ON - Not starting fusion location detection")
        }
    }

    fun stopMonitoringFusionLocationDetector() {
        if(activeFusionLoc == true) {
            Log.i("DetectorsManager", "Fusion location detection is ON - Stopping fusion location detection")
            activeFusionLoc = false
            fusionLocationProvider.stopLocationUpdates()
        } else {
            Log.i("DetectorsManager", "Fusion location detection is already OFF - Not stopping fusion location detection")
        }
    }

    fun startMonitoringCallDetection() {
        if(activeCallDetector == false) {
            Log.i("DetectorsManager", "Call detection is OFF - Starting call detection")
            activeCallDetector = true
            callStateDetector.startMonitoring()
        } else {
            Log.i("DetectorsManager", "Call detection is already ON - Not starting call detection")
        }
    }

    fun stopMonitoringCallDetection() {
        if(activeCallDetector == true) {
            Log.i("DetectorsManager", "Call detection is ON - Stopping call detection")
            activeCallDetector = false
            callStateDetector.stopMonitoring()
        } else {
            Log.i("DetectorsManager", "Call detection is already OFF - Not stopping call detection")
        }
    }

    fun startMonitoringDropDetection() {
        if(activeDropDetector == false) {
            Log.i("DetectorsManager", "Drop detection is OFF - Starting drop detection")
            activeDropDetector = true
            dropDetector.startMonitoring()
        } else {
            Log.i("DetectorsManager", "Drop detection is already ON - Not starting drop detection")
        }
    }

    fun stopMonitoringDropDetection() {
        if(activeDropDetector == true) {
            Log.i("DetectorsManager", "Drop detection is ON - Stopping drop detection")
            activeDropDetector = false
            dropDetector.stopMonitoring()
        } else {
            Log.i("DetectorsManager", "Drop detection is already OFF - Not stopping drop detection")
        }
    }

    fun startMonitoringLowLightDetection() {
        if(activeLowLightDetector == false) {
            Log.i("DetectorsManager", "Low light detection is OFF - Starting low light detection")
            activeLowLightDetector = true
            lowLightDetector.startMonitoring()
        } else {
            Log.i("DetectorsManager", "Low light detection is already ON - Not starting low light detection")
        }
    }

    fun stopMonitoringLowLightDetection() {
        if(activeLowLightDetector == true) {
            Log.i("DetectorsManager", "Low light detection is ON - Stopping low light detection")
            activeLowLightDetector = false
            lowLightDetector.stopMonitoring()
        } else {
            Log.i("DetectorsManager", "Low light detection is already OFF - Not stopping low light detection")
        }
    }

    fun startMonitoringSleepDetection() {
        if(activeSleepDetector == false) {
            Log.i("DetectorsManager", "Sleep detection is OFF - Starting sleep detection")
            activeSleepDetector = true
            sleepDetector.startSleepTracking()
        } else {
            Log.i("DetectorsManager", "Sleep detection is already ON - Not starting sleep detection")
        }
    }

    fun stopMonitoringSleepDetection() {
        if(activeDropDetector == true) {
            Log.i("DetectorsManager", "Sleep detection is ON - Stopping sleep detection")
            activeSleepDetector = false
            sleepDetector.stopSleepTracking()
        } else {
            Log.i("DetectorsManager", "Sleep detection is already OFF - Not stopping sleep detection")
        }
    }

}