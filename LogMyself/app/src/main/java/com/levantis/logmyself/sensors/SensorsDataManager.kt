package com.levantis.logmyself.sensors

import android.content.Context
import android.util.Log
import androidx.room.concurrent.AtomicBoolean
import com.google.firebase.Timestamp
import com.levantis.logmyself.cloudb.FirestoreManager
import com.levantis.logmyself.cloudb.model.CallEvent
import com.levantis.logmyself.cloudb.model.DeviceUnlockEvent
import com.levantis.logmyself.cloudb.model.DropEvent
import com.levantis.logmyself.cloudb.model.LowLightDetectionEvent
import com.levantis.logmyself.cloudb.model.PositionGPSEvent
import com.levantis.logmyself.cloudb.model.ScreenTimeEvent
import com.levantis.logmyself.cloudb.model.SleepEvent
import com.levantis.logmyself.cloudb.model.UserActivityEvent
import com.levantis.logmyself.database.data.PowerChargingData
import com.levantis.logmyself.database.util.DatabaseProvider
import java.time.LocalDateTime
import java.time.ZoneId
import java.util.Date

/**
 * Centralized object to manage all sensors related data.
 * */

object SensorsDataManager {

    private var previousClassifyEventTime: LocalDateTime? = null

    /* -- States for managing screen time -- */
    private var screenOnTimeStart: LocalDateTime? = null// start of a on-screen session
    private var screenOnTimeEnd: LocalDateTime? = null // end of the on-screen session
    private var screenOnTimeDuration: Long = 0 // duration of the on-screen session
    private var screenOnTimeActive: Boolean = false // flag to indicate if the screen is on

    /* -- States for managing charge time -- */
    private var chargeTimeStart: LocalDateTime? = null // start of a charging session
    private var chargeTimeEnd: LocalDateTime? = null // end of the charging session
    private var chargeTimeActive: Boolean = false // flag to indicate if the device is charging on

    /* -- Stats -- */
    // Drop detector counter
    private val dropDetectorEventTimes: MutableList<LocalDateTime> = mutableListOf()

    /* -- State of object distance from proximity sensor */
    val isNear = AtomicBoolean(false) // distance from the proximity sensor

    /* Screen-on time related functions */
    fun startScreenTimeTracking() {
        if(!screenOnTimeActive) {
            screenOnTimeActive = true
            screenOnTimeStart = LocalDateTime.now()
            Log.d("SensorsDataManager", "Screen time tracking started at $screenOnTimeStart")
        } else {
            Log.d("SensorsDataManager", "Screen time tracking is already active")
        }
    }
    fun endScreenTimeTracking(context: Context) {
        if(screenOnTimeActive) {
            if(screenOnTimeStart == null) {
                Log.e("SensorsDataManager", "Screen on time start is null, cannot calculate duration")
                return
            }
            screenOnTimeActive = false
            screenOnTimeEnd = LocalDateTime.now()
            screenOnTimeDuration =
                java.time.Duration.between(screenOnTimeStart, screenOnTimeEnd).toMillis()
            Log.d("SensorsDataManager", "Screen time tracking ended at $screenOnTimeEnd")
            Log.d("SensorsDataManager", "Screen on duration: $screenOnTimeDuration ms")
            // Report the screen on time data
            if (screenOnTimeStart != null && screenOnTimeEnd != null) {
                reportScreenTimeData(
                    screenOnTimeStart!!,
                    screenOnTimeEnd!!,
                    screenOnTimeDuration
                )
            } else {
                Log.e("SensorsDataManager", "Screen on time start or end is null, cannot report data")
            }
            // reset time states
            screenOnTimeStart = null
            screenOnTimeEnd = null
        } else {
            Log.d("SensorsDataManager", "Screen time tracking is not active")
        }
    }

    /* -- Charge related functions -- */
    fun startChargeTimeTracking() {
        if(!chargeTimeActive) {
            chargeTimeActive = true
            chargeTimeStart = LocalDateTime.now()
            Log.d("SensorsDataManager", "Charge time tracking started at $chargeTimeStart")
        } else {
            Log.d("SensorsDataManager", "Charge time tracking is already active")
        }
    }

    fun stopChargeTimeTracking(context: Context) {
        if(chargeTimeActive) {
            chargeTimeActive = false
            chargeTimeEnd = LocalDateTime.now()
            Log.d("SensorsDataManager", "Charge time tracking stopped at $chargeTimeEnd")
            // report the charge time data
            if (chargeTimeStart != null && chargeTimeEnd != null) {
                val chargeTimeDuration =
                    java.time.Duration.between(chargeTimeStart, chargeTimeEnd).toMillis()
                Log.d("SensorsDataManager", "Charge time duration: $chargeTimeDuration ms")
                val chargeData = PowerChargingData(
                    startTime = chargeTimeStart!!,
                    endTime = chargeTimeEnd!!
                )
                // Add to the database
                DatabaseProvider.insertPowerChargingData(
                    context = context,
                    powerChargingData = chargeData
                )
            } else {
                Log.e("SensorsDataManager", "Charge time start or end is null, cannot report data")
            }
            // reset time states
            chargeTimeStart = null
            chargeTimeEnd = null
        } else {
            Log.d("SensorsDataManager", "Charge time tracking is not active")
        }
    }

    /* -- Getters and Setters -- */
    public fun addPhoneUnlockedEvents(context: Context) { // increment the counter for phone unlocked events
        reportUnlockEvent()
    }

    public fun getPreviousClassifyEventTime(): LocalDateTime? {
        return previousClassifyEventTime
    }
    public fun setPreviousClassifyEventTime(time: LocalDateTime) {
        previousClassifyEventTime = time
    }

    public fun getDropDetectorEventTimes(): List<LocalDateTime> {
        return dropDetectorEventTimes
    }
    public fun addDropDetectorEventTime(time: LocalDateTime) {
        dropDetectorEventTimes.add(time)
    }

    /* -- Reporters -- */

    fun convertToFirestoreTimestamp(localDateTime: LocalDateTime): Timestamp {
        val instant = localDateTime.atZone(ZoneId.systemDefault()).toInstant()
        val date = Date.from(instant)
        return Timestamp(date)
    }

    fun reportLowLightData(
        startTime: LocalDateTime,
        endTime: LocalDateTime,
        duration: Long,
        validStartTime: Long,
        validEndTime: Long,
        lowLightThreshold: Float
    ) {
        // Send to cloud database
        val lowLightData = LowLightDetectionEvent(
            startTime = convertToFirestoreTimestamp(startTime),
            endTime = convertToFirestoreTimestamp(endTime),
            duration = duration,
            validStartTime = validStartTime,
            validEndTime = validEndTime,
            lowLightThreshold = lowLightThreshold
        )
        FirestoreManager.saveEvent(
            "low_light_events",
            lowLightData,
            onSuccess = {
                Log.d("SensorsDataManager", "Low light data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save low light data to Firestore", exception)
            }
        )
    }

    fun reportDropData(
        timestamp: LocalDateTime,
        detectedMagnitude: Long,
        detectedFallDuration: Long) {
        // Send to cloud database
        val dropData = DropEvent(
            timestamp = convertToFirestoreTimestamp(timestamp),
            detectedMagnitude = detectedMagnitude,
            detectedFallDuration = detectedFallDuration
        )
        FirestoreManager.saveEvent(
            "drop_events",
            dropData,
            onSuccess = {
                Log.d("SensorsDataManager", "Drop data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save drop data to Firestore", exception)
            }
        )
    }

//    fun reportSleepClassifyData(
//        context: Context,
//        confidence: Int,
//        light: Int,
//        motion: Int,
//        timestampNow: LocalDateTime,
//        timestampPrevious: LocalDateTime,
//        screenOnDuration: Long,
//        usedApps: Map<String, Long>
//    ) {
//        // Send to cloud database
//        // Initialize the data class with the reported values
//        val sleepData = SleepDetectorData(
//            confidence = confidence,
//            light = light,
//            motion = motion,
//            timestampNow = timestampNow,
//            timestampPrevious = timestampPrevious,
//            screenOnDuration = screenOnDuration
//        )
//        // Add to the database
//        val sleepEventId = kotlinx.coroutines.runBlocking {
//            DatabaseProvider.insertSleepEventsData(
//                context = context,
//                sleepDetectorData = sleepData
//            )
//        }
//        Log.d("DetectorsManager", "Sleep event ID: $sleepEventId")
//        // Insert the used apps into the used_apps table
//        val usedAppEntries = usedApps.map { (appName, usageDuration) ->
//            UsedAppsData(
//                sleepEventId = sleepEventId,
//                appName = appName,
//                usageDuration = usageDuration
//            )
//        }
//        DatabaseProvider.insertUsedAppsData(
//            context = context,
//            usedAppsDataList = usedAppEntries
//        )
//    }

    fun reportSleepClassifyData(
        confidence: Int,
        light: Int,
        motion: Int,
        timestampNow: LocalDateTime,
        timestampPrevious: LocalDateTime,
        screenOnDuration: Long,
        usedApps: Map<String, Long>
    ) {
        // Send data to cloud database
        val sleepData = SleepEvent(
            confidence = confidence,
            light = light,
            motion = motion,
            timestampNow = convertToFirestoreTimestamp(timestampNow),
            timestampPrevious = convertToFirestoreTimestamp(timestampPrevious),
            screenOnDuration = screenOnDuration,
            usedApps = usedApps,
        )
        FirestoreManager.saveEvent(
            "sleep_events",
            sleepData,
            onSuccess = {
                Log.d("SensorsDataManager", "Sleep data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save sleep data to Firestore", exception)
            }
        )
    }

    private fun reportScreenTimeData(
        timeStart: LocalDateTime,
        timeEnd: LocalDateTime,
        duration: Long
    ) {
        // Send to cloud database
        val screenTimeCloudData = ScreenTimeEvent(
            timeStart = convertToFirestoreTimestamp(timeStart),
            timeEnd = convertToFirestoreTimestamp(timeEnd),
            duration = duration
        )
        FirestoreManager.saveEvent (
            "screen_time_events",
            screenTimeCloudData,
            onSuccess = {
                Log.d("SensorsDataManager", "Screen time data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save screen time data to Firestore", exception)
            }
        )
    }

    private fun reportUnlockEvent() {
        var unlockEventDate = LocalDateTime.now()
        // Send to cloud database
        val unlockEventCloudData = DeviceUnlockEvent(
            timestamp = convertToFirestoreTimestamp(unlockEventDate)
        )
        FirestoreManager.saveEvent(
            "device_unlocks_events",
            unlockEventCloudData,
            onSuccess = {
                Log.d("SensorsDataManager", "Unlock event data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save unlock event data to Firestore", exception)
            }
        )
    }

    fun reportActivityEvent(activityType: String, confidence: Int, timestamp: LocalDateTime) {
        // Send to cloud database
        val activityCloudData = UserActivityEvent(
            activityType = activityType,
            confidence = confidence,
            timestamp = convertToFirestoreTimestamp(timestamp)
        )
        FirestoreManager.saveEvent(
            "user_activities_events",
            activityCloudData,
            onSuccess = {
                Log.d("SensorsDataManager", "Activity data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save activity data to Firestore", exception)
            }
        )
    }

    fun reportCallEvent(
        callType: Int?,
        callDescription: String?,
        callDuration: Int?,
        callDate: LocalDateTime
    ) {
        // Send to cloud database
        val callData = CallEvent(
            callType = callType,
            callDescription = callDescription,
            callDuration = callDuration,
            callDate = convertToFirestoreTimestamp(callDate)
        )
        FirestoreManager.saveEvent(
            "call_events",
            callData,
            onSuccess = {
                Log.d("SensorsDataManager", "Call data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save call data to Firestore", exception)
            }
        )
    }

    fun reportPositionGPSEvent(
        latitude: Double,
        longitude: Double,
        accuracy: Float,
        altitude: Double,
        speed: Float,
        bearing: Float,
        speedAccuracyMetersPerSecond: Float,
        timestampNow: LocalDateTime
    ) {
        // Send to cloud database
        val positionGPSEvent = PositionGPSEvent(
            latitude = latitude,
            longitude = longitude,
            accuracy = accuracy,
            altitude = altitude,
            speed = speed,
            bearing = bearing,
            speedAccuracyMetersPerSecond = speedAccuracyMetersPerSecond,
            timestampNow = convertToFirestoreTimestamp(timestampNow)
        )
        FirestoreManager.saveEvent(
            "gps_events",
            positionGPSEvent,
            onSuccess = {
                Log.d("SensorsDataManager", "GPS data saved to Firestore")
            },
            onFailure = { exception ->
                Log.e("SensorsDataManager", "Failed to save GPS data to Firestore", exception)
            }
        )
    }
}