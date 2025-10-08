package com.levantis.logmyself.sensors.detectors

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import com.levantis.logmyself.sensors.SensorsDataManager
import com.levantis.logmyself.sensors.listeners.DropListener
import java.time.LocalDateTime
import kotlin.math.sqrt

/**
 * Manages accelerometer sensor monitoring to detect device drops (freefall).
 * Notifies a listener about drop events.
 *
 * @param context The application or activity context used to access system services
 * @param listener The callback listener to notify about drop events or sensor status
 */
class DropDetector(
    private val context: Context,
    private val listener: DropListener
) : SensorEventListener {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private var accelerometerSensor: Sensor? = null

    // Thresholds for drop detection
    private val freefallThreshold = 1.0f // m/s^2 - Below this magnitude suggests freefall
    private val impactThreshold = 15.0f  // m/s^2 - Above this magnitude after freefall suggests impact
    private val minFreefallDurationMs = 30 // milliseconds - Minimum time in freefall state

    // State variables
    private var isMonitoring = false
    private var isFalling = false
    private var freefallStartTime: Long = 0 // Nanoseconds from event timestamp

    init {
        accelerometerSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER) // get the accelerometer sensor
        if (accelerometerSensor == null) {
            Log.e("DropDetector", "Accelerometer sensor not available")
        } else {
            Log.i("DropDetector", "Accelerometer sensor available: ${accelerometerSensor?.name}")
        }
    }

    /**
     * Starts monitoring for potential drops
     * Notifies the listener if the sensor is unavailable
     * */
    fun startMonitoring() {
        if (isMonitoring) {
            Log.w("DropDetector", "Already monitoring for drops")
            return
        }
        if (accelerometerSensor == null) {
            listener.onDropSensorUnavailable()
            return
        }
        val registered = sensorManager.registerListener(
            this,
            accelerometerSensor,
            SensorManager.SENSOR_DELAY_GAME
        )

        if(registered) {
            isMonitoring = true
            isFalling = false // reset it
            listener.onDropMonitoringStarted()
        } else {
            Log.e("DropDetector", "Failed to register accelerometer listener")
            listener.onDropSensorUnavailable() // Treat registration failure as unavailability
        }
    }

    fun stopMonitoring() {
        if(!isMonitoring) {
            Log.w("DropDetector", "Not currently monitoring for drops")
            return
        }
        sensorManager.unregisterListener(this, accelerometerSensor)
        isMonitoring = false
        isFalling = false // reset it
        Log.i("DropDetector", "Stopped monitoring for drops")
        listener.onDropMonitoringStopped()
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (!isMonitoring || event?.sensor?.type != Sensor.TYPE_ACCELEROMETER) {
            return
        }

        val x = event.values[0]
        val y = event.values[1]
        val z = event.values[2]

        // Calculate the magnitude of the acceleration vector
        val magnitude = sqrt(x * x + y * y + z * z)

        // --- Detection Logic ---
        if (magnitude < freefallThreshold) {
            // Potential start of freefall
            if (!isFalling) {
                isFalling = true
                freefallStartTime = event.timestamp // Use event timestamp (nanos)
                Log.d("DropDetector", "Potential Freefall START. Magnitude: $magnitude")
                listener.onDropFreefallDetected() // Notify listener about potential fall start
            }
        } else { // Magnitude is above freefall threshold
            if (isFalling) {
                // Was previously falling, now it's not (or impact occurred)
                val fallDurationNs = event.timestamp - freefallStartTime
                val fallDurationMs = fallDurationNs / 1_000_000 // Convert ns to ms

                Log.d("DropDetector", "Potential Freefall ENDED. Duration: ${fallDurationMs}ms. Current Magnitude: $magnitude")

                // Check 1: Was the freefall duration long enough?
                if (fallDurationMs >= minFreefallDurationMs) {
                    // Check 2: Was there a significant impact spike?
                    if (magnitude > impactThreshold) {
                        Log.w("DropDetector", "CONFIRMED DROP (Duration + Impact)! Impact Magnitude: $magnitude")
                        SensorsDataManager.addDropDetectorEventTime(LocalDateTime.now())
                        listener.onDropDetected(
                            timestamp = LocalDateTime.now(),
                            detectedMagnitude = magnitude.toLong(),
                            detectedFallDuration = fallDurationMs
                        ) // Notify listener: Confirmed Drop!
                    } else {
                        // It fell long enough, but didn't end with a major spike.
                        // Could still be a drop onto something soft, or just a weird motion.
                        // Decide if you want to notify for this case too.
                        Log.d("DropDetector", "Confirmed Freefall (Duration met, no high impact). Magnitude: $magnitude")
                        // Maybe add another listener method like onSoftDropDetected() or just call onDropDetected()
                        // listener.onDropDetected() // Optional: Count this as a drop too
                    }
                } else {
                    // Fall was too short, likely noise or a quick jolt.
                    Log.d("DropDetector", "Ignoring short fall duration: ${fallDurationMs}ms")
                }

                // Reset falling state regardless of outcome
                isFalling = false
            }
            // Not falling and magnitude is normal (idle state) - No action needed
        }
    }

    override fun onAccuracyChanged(sensor: Sensor, accuracy: Int) {
        Log.i("DropDetector", "onAccuracyChanged for sensor: ${sensor.name} with acc: $accuracy")
    }
}