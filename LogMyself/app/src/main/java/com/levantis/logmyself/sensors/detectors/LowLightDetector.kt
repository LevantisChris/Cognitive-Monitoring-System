package com.levantis.logmyself.sensors.detectors

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import com.levantis.logmyself.sensors.SensorsDataManager
import com.levantis.logmyself.sensors.listeners.LightListener
import com.levantis.logmyself.utils.SunsetSunriseTimes
import java.time.LocalDateTime
import java.time.LocalTime

/** Detect when the user is in a environment with low light exposure.
*  The detection will not happen in the nighttime and in general in hours a
*  human us not meant to take light exposure
*  @param context
 * @param listener
 * */

class LowLightDetector(
    private val context: Context,
    private val listener: LightListener
) : SensorEventListener {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private var lightSensor: Sensor? = null

    // Threshold for light detection
    private val lowLightThreshold = 15.0f // Lux - Below this level suggests low light

    // State variables
    private var validStartTime = 0L // start of the time the sun rises (ex. for Greece this is 7:00 during summer)
    private var validEndTime = 0L // end of the time the sun sets (ex. for Greece this is 19:00 during summer)
    private var lowLightExposureStartTime: LocalDateTime? = null // the start time the user was exposed to low light
    private var lowLightExposureEndTime: LocalDateTime? = null // the end time the user was exposed to low light
    private var lowLightExposureDuration: Long = 0 // the duration the user was exposed to low light
    private var isMonitoring = false
    private var isLowLight = false

    init {
        lightSensor = sensorManager.getDefaultSensor(Sensor.TYPE_LIGHT) // get the light sensor
        /* Set the valid start time based on the county the user is
        *  Example here is Greece
        *  TODO: Add a way to set the valid start and end time based on the user's location
        * */
        validStartTime = SunsetSunriseTimes.GREECE_SUMMER_SUNR
        validEndTime = SunsetSunriseTimes.GREECE_SUMMER_SUNS
        if (lightSensor == null) {
            Log.e("LowLightDetector", "Light sensor not available")
            listener.onLightSensorUnavailable()
        } else {
            Log.i("LowLightDetector", "Light sensor available: ${lightSensor?.name}")
        }
    }

    /**
     * Starts monitoring for light detections
     * Notifies the listener if the sensor is unavailable
     * */
    fun startMonitoring() {
        if(isMonitoring) {
            Log.w("LowLightDetector", "Already monitoring for light conditions")
            return
        }
        if(lightSensor == null) {
            listener.onLightSensorUnavailable()
            return
        }
        val registered = sensorManager.registerListener(
            this,
            lightSensor,
            SensorManager.SENSOR_DELAY_NORMAL
        )
        if(registered) {
            isMonitoring = true
            isLowLight = false
            listener.onLightMonitoringStarted()
        } else {
            Log.e("LowLightDetector", "Failed to register light sensor listener")
            listener.onLightSensorUnavailable() // Treat registration failure as unavailability
        }
    }
    /**
     * Stops monitoring for light detections (reason for that can be anything)
     * Notifies the listener if not currently monitoring
     * */
    fun stopMonitoring() {
        if(!isMonitoring) {
            Log.w("LowLightDetector", "Not currently monitoring for light conditions")
            return
        }
        Log.i("LowLightDetector", "Stopped monitoring for light conditions")
        sensorManager.unregisterListener(this)
        isMonitoring = false
        isLowLight = false
        listener.onLightMonitoringStopped()
    }

    override fun onSensorChanged(p0: SensorEvent?) {
        if (!isMonitoring || p0?.sensor?.type != Sensor.TYPE_LIGHT || SensorsDataManager.isNear.get()) {
            return
        }
        val lightLevel = p0.values[0] // Get the light level from the event
        if (lightLevel < lowLightThreshold) {
            if (!isLowLight) {
                Log.d("LowLightDetector", "Low light detected")
                isLowLight = true
                //
                /* Check if the start time period is valid for detection */
                val currentTime = java.time.LocalDateTime.now().toEpochSecond(java.time.ZoneOffset.UTC) * 1000
                if(currentTime < validStartTime || currentTime > validEndTime) {
                    Log.w("LowLightDetector", "Current time is outside the valid range for light detection")
                    listener.onLightDetectionNotValid()
                    return
                }
                /* Initialize the time the user is detected to be in an environment with low light exposure */
                lowLightExposureStartTime = LocalDateTime.now() // the timer starts
                listener.onLowLevelLightDetected()
            }
        } else {
            if (isLowLight) {
                Log.d("LowLightDetector", "Light level back to normal")
                isLowLight = false
                //
                lowLightExposureEndTime = LocalDateTime.now()
                /* If end time of the timer that measures low light exposure period is greater than the
                *  valid end time threshold, then set end time equal with the threshold */
                if((lowLightExposureEndTime?.toEpochSecond(java.time.ZoneOffset.UTC)?.times(1000)
                        ?: Long.MAX_VALUE) > validEndTime
                ) {
                    Log.w("LowLightDetector", "Current time is outside the valid range for light detection")
                    lowLightExposureEndTime = LocalDateTime.ofEpochSecond(validEndTime / 1000, 0, java.time.ZoneOffset.UTC) // equal with the valid end time
                    listener.onLightSensorUnavailable()
                    return
                }
                /* if the duration is less than ((30min)) is not valid */
                lowLightExposureDuration = lowLightExposureEndTime?.toEpochSecond(java.time.ZoneOffset.UTC)!! - lowLightExposureStartTime!!.toEpochSecond(java.time.ZoneOffset.UTC) // to seconds
                if(lowLightExposureDuration < 1800) { // 30 min
                    Log.w("LowLightDetector", "Low light exposure duration is less than 30 minutes")
                    return
                } else {
                    Log.w("LowLightDetector", "Low light exposure duration is valid" +
                            "Start time: $lowLightExposureStartTime\n" +
                            "End time: $lowLightExposureEndTime\n" +
                            "Duration: $lowLightExposureDuration"
                    )
                    SensorsDataManager.reportLowLightData(
                        lowLightExposureStartTime!!,
                        lowLightExposureEndTime!!,
                        lowLightExposureDuration,
                        validStartTime,
                        validEndTime,
                        lowLightThreshold
                    )
                }
            }
        }
    }

    override fun onAccuracyChanged(p0: Sensor?, p1: Int) {
        Log.d("LowLightDetector", "Sensor accuracy changed: $p1")
    }
}