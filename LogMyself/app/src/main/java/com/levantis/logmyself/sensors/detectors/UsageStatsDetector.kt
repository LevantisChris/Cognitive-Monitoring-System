package com.levantis.logmyself.sensors.detectors

import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context

/*
* Here we will take information such as:
* - If the screen is on or off
* - How many times the device is unlocked
* - User interactions and so on...
* In general whatever the usage stats API can provide
* **/

class UsageStatsDetector(
    private val context: Context,
)  {

    /**
     * @param: startTime --> The start time of the period we want to search
     * @param: endTime --> The end time of the period we want to search
     * @return: total screen time in milliseconds
     *  */
    fun getScreenOnDuration(startTime: Long, endTime: Long): Long {
        val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val usageEvents = usageStatsManager.queryEvents(startTime, endTime)
        val event = UsageEvents.Event()

        var totalScreenOnTime = 0L
        var lastScreenOnTimestamp: Long? = null
        var firstEventSeen = false

        while (usageEvents.hasNextEvent()) {
            usageEvents.getNextEvent(event)

            if (!firstEventSeen) {
                firstEventSeen = true
                // If first event is SCREEN_NON_INTERACTIVE, assume screen was ON from startTime
                if (event.eventType == UsageEvents.Event.SCREEN_NON_INTERACTIVE) {
                    lastScreenOnTimestamp = startTime
                    totalScreenOnTime += event.timeStamp - startTime
                    continue
                }
            }

            when (event.eventType) {
                UsageEvents.Event.SCREEN_INTERACTIVE -> {
                    lastScreenOnTimestamp = event.timeStamp
                }

                UsageEvents.Event.SCREEN_NON_INTERACTIVE -> {
                    if (lastScreenOnTimestamp != null) {
                        totalScreenOnTime += event.timeStamp - lastScreenOnTimestamp
                        lastScreenOnTimestamp = null
                    }
                }
            }
        }

        // If the screen was still ON at endTime
        if (lastScreenOnTimestamp != null) {
            totalScreenOnTime += endTime - lastScreenOnTimestamp
        }

        return totalScreenOnTime
    }

    fun getUsedApps(startTime: Long, endTime: Long): Map<String, Long> {
        val usm = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val usageEvents = usm.queryEvents(startTime, endTime)
        val event = UsageEvents.Event()

        val appUsageMap = mutableMapOf<String, Long>()
        val lastForegroundMap = mutableMapOf<String, Long>()

        while (usageEvents.hasNextEvent()) {
            usageEvents.getNextEvent(event)

            when (event.eventType) {
                UsageEvents.Event.MOVE_TO_FOREGROUND -> {
                    // Clamp to startTime if event is earlier
                    val clampedStart = maxOf(event.timeStamp, startTime)
                    lastForegroundMap[event.packageName] = clampedStart
                }

                UsageEvents.Event.MOVE_TO_BACKGROUND -> {
                    val foregroundStart = lastForegroundMap[event.packageName]
                    if (foregroundStart != null) {
                        // Clamp end to endTime if background event is beyond
                        val clampedEnd = minOf(event.timeStamp, endTime)
                        if (clampedEnd > foregroundStart) {
                            val duration = clampedEnd - foregroundStart
                            appUsageMap[event.packageName] =
                                appUsageMap.getOrDefault(event.packageName, 0L) + duration
                        }
                        lastForegroundMap.remove(event.packageName)
                    }
                }
            }
        }

        // App might still be in foreground when time window ends
        for ((packageName, foregroundStart) in lastForegroundMap) {
            val duration = endTime - foregroundStart
            if (duration > 0) {
                appUsageMap[packageName] =
                    appUsageMap.getOrDefault(packageName, 0L) + duration
            }
        }

        // Convert package names to human-readable app names
        val pm = context.packageManager
        val readableMap = mutableMapOf<String, Long>()

        for ((pkg, duration) in appUsageMap) {
            try {
                val label = pm.getApplicationLabel(pm.getApplicationInfo(pkg, 0)).toString()
                readableMap[label] = duration
            } catch (e: Exception) {
                readableMap[pkg] = duration // fallback
            }
        }

        return readableMap
    }
}