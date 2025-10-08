package com.levantis.logmyself.sensors.detectors

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import com.levantis.logmyself.sensors.SensorsDataManager

class ProximityDetector (
    context: Context
) : SensorEventListener {

    private val sensorManager: SensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private var proximitySensor: Sensor? = null

    init {
        proximitySensor = sensorManager.getDefaultSensor(Sensor.TYPE_PROXIMITY)
        if(proximitySensor == null) {
            Log.i("ProximityDetector", "Proximity sensor not available")
        } else {
            Log.i("ProximityDetector", "Proximity sensor available: ${proximitySensor?.name}")
        }
    }

    fun startMonitoring() {
        if (proximitySensor != null) {
            sensorManager.registerListener(this, proximitySensor, SensorManager.SENSOR_DELAY_NORMAL)
            Log.i("ProximityDetector", "Proximity sensor monitoring started")
        } else {
            Log.e("ProximityDetector", "Proximity sensor not available")
        }
    }

    fun stopMonitoring() {
        if (proximitySensor != null) {
            sensorManager.unregisterListener(this, proximitySensor)
            Log.i("ProximityDetector", "Proximity sensor monitoring stopped")
        } else {
            Log.e("ProximityDetector", "Proximity sensor not available")
        }
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event?.sensor?.type == Sensor.TYPE_PROXIMITY) {
            val distance = event.values[0]
            if (distance < (proximitySensor?.maximumRange ?: 0f)) {
                Log.d("ProximityDetector", "Device is close to an object.")
                SensorsDataManager.isNear.set(true)
            } else {
                Log.d("ProximityDetector", "Device is far from an object.")
                SensorsDataManager.isNear.set(false)
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

}