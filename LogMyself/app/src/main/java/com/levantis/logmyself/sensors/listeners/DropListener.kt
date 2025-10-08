package com.levantis.logmyself.sensors.listeners

import java.time.LocalDateTime

/**
 * Interface definition for a callback to be invoked when a drop event is detected
 * or the required sensor is unavailable.
 */
interface DropListener {
    /**
     * Called when a confirmed drop (freefall meeting duration criteria, potentially followed by impact) is detected.
     */
    fun onDropDetected(
        timestamp: LocalDateTime,
        detectedMagnitude: Long,
        detectedFallDuration: Long,
    ) {}

    /**
     * Called if the accelerometer sensor needed for detection is not available on the device.
     */
    fun onDropSensorUnavailable() {}

    /**
     * Optional: Called when monitoring starts successfully.
     */
    fun onDropMonitoringStarted() {} // Default empty implementation

    /**
     * Optional: Called when monitoring stops.
     */
    fun onDropMonitoringStopped() {} // Default empty implementation

    /**
     * Optional: Called during the freefall phase (before impact or end).
     * Might be useful for immediate UI feedback.
     */
    fun onDropFreefallDetected() {} // Default empty implementation
}