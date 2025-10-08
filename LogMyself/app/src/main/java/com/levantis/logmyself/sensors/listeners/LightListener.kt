package com.levantis.logmyself.sensors.listeners

interface LightListener {

    /**
     * Called if the light sensor needed for detection is not available on the device.
     */
    fun onLightSensorUnavailable() {}

    /*
    * Called if the the detection is not valid
    */
    fun onLightDetectionNotValid() {}

    /**
     * Optional: Called when monitoring starts successfully.
     */
    fun onLightMonitoringStarted() {}

    /**
     * Optional: Called when monitoring stops.
     */
    fun onLightMonitoringStopped() {}

    /**
     * Called when the light level is bellow a defined threshold
     * (typically indicating a low-light condition)
     * */
    fun onLowLevelLightDetected() {}
}