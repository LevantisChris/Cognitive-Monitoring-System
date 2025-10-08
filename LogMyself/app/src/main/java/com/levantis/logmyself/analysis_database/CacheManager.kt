package com.levantis.logmyself.analysis_database

import com.levantis.logmyself.analysis_database.data_classes.*
import kotlinx.datetime.LocalDate
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

/**
 * Cache manager for storing analysis data locally to avoid repeated database calls
 */
class CacheManager {
    
    // Cache storage with thread-safe access
    private val overallPerformanceCache = ConcurrentHashMap<String, CachedData<Pair<Double, String>>>()
    private val typingPercentagesCache = ConcurrentHashMap<String, CachedData<TypingCategoryPercentages>>()
    private val sleepDataCache = ConcurrentHashMap<String, CachedData<DailySleepSummary>>()
    private val gpsDataCache = ConcurrentHashMap<String, CachedData<GPSDataAnalysisInfo>>()
    private val activityDataCache = ConcurrentHashMap<String, CachedData<ActivityDataAnalysisInfo>>()
    private val callDataCache = ConcurrentHashMap<String, CachedData<CallDataAnalysisInfo>>()
    private val deviceInteractionCache = ConcurrentHashMap<String, CachedData<DeviceInteractionAnalysisInfo>>()
    private val cognitiveScoresSummaryCache = ConcurrentHashMap<String, CachedData<CognitiveScoresSummary>>()
    
    // Cache configuration
    companion object {
        private const val DEFAULT_CACHE_DURATION_MINUTES = 30L
        private const val LONG_CACHE_DURATION_MINUTES = 60L // For data that changes less frequently
    }
    
    /**
     * Data class to wrap cached data with timestamp
     */
    private data class CachedData<T>(
        val data: T,
        val timestamp: Long = System.currentTimeMillis(),
        val cacheDurationMinutes: Long = DEFAULT_CACHE_DURATION_MINUTES
    ) {
        fun isExpired(): Boolean {
            val expirationTime = timestamp + TimeUnit.MINUTES.toMillis(cacheDurationMinutes)
            return System.currentTimeMillis() > expirationTime
        }
    }
    
    /**
     * Generate cache key for user and date combination
     */
    private fun getCacheKey(userUid: String, date: LocalDate): String {
        return "${userUid}_${date}"
    }
    
    // Overall Performance Cache Methods
    fun getOverallPerformance(userUid: String, date: LocalDate): Pair<Double, String>? {
        val key = getCacheKey(userUid, date)
        val cachedData = overallPerformanceCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: Overall Performance for $key")
            cachedData.data
        } else {
            println("Cache MISS: Overall Performance for $key")
            null
        }
    }
    
    fun cacheOverallPerformance(userUid: String, date: LocalDate, data: Pair<Double, String>) {
        val key = getCacheKey(userUid, date)
        overallPerformanceCache[key] = CachedData(data, cacheDurationMinutes = LONG_CACHE_DURATION_MINUTES)
        println("Cached Overall Performance for $key")
    }
    
    // Typing Percentages Cache Methods
    fun getTypingPercentages(userUid: String, date: LocalDate): TypingCategoryPercentages? {
        val key = getCacheKey(userUid, date)
        val cachedData = typingPercentagesCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: Typing Percentages for $key")
            cachedData.data
        } else {
            println("Cache MISS: Typing Percentages for $key")
            null
        }
    }
    
    fun cacheTypingPercentages(userUid: String, date: LocalDate, data: TypingCategoryPercentages) {
        val key = getCacheKey(userUid, date)
        typingPercentagesCache[key] = CachedData(data)
        println("Cached Typing Percentages for $key")
    }
    
    // Sleep Data Cache Methods
    fun getSleepData(userUid: String, date: LocalDate): DailySleepSummary? {
        val key = getCacheKey(userUid, date)
        val cachedData = sleepDataCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: Sleep Data for $key")
            cachedData.data
        } else {
            println("Cache MISS: Sleep Data for $key")
            null
        }
    }
    
    fun cacheSleepData(userUid: String, date: LocalDate, data: DailySleepSummary) {
        val key = getCacheKey(userUid, date)
        sleepDataCache[key] = CachedData(data)
        println("Cached Sleep Data for $key")
    }
    
    // GPS Data Cache Methods
    fun getGpsData(userUid: String, date: LocalDate): GPSDataAnalysisInfo? {
        val key = getCacheKey(userUid, date)
        val cachedData = gpsDataCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: GPS Data for $key")
            cachedData.data
        } else {
            println("Cache MISS: GPS Data for $key")
            null
        }
    }
    
    fun cacheGpsData(userUid: String, date: LocalDate, data: GPSDataAnalysisInfo) {
        val key = getCacheKey(userUid, date)
        gpsDataCache[key] = CachedData(data)
        println("Cached GPS Data for $key")
    }
    
    // Activity Data Cache Methods
    fun getActivityData(userUid: String, date: LocalDate): ActivityDataAnalysisInfo? {
        val key = getCacheKey(userUid, date)
        val cachedData = activityDataCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: Activity Data for $key")
            cachedData.data
        } else {
            println("Cache MISS: Activity Data for $key")
            null
        }
    }
    
    fun cacheActivityData(userUid: String, date: LocalDate, data: ActivityDataAnalysisInfo) {
        val key = getCacheKey(userUid, date)
        activityDataCache[key] = CachedData(data)
        println("Cached Activity Data for $key")
    }
    
    // Call Data Cache Methods
    fun getCallData(userUid: String, date: LocalDate): CallDataAnalysisInfo? {
        val key = getCacheKey(userUid, date)
        val cachedData = callDataCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: Call Data for $key")
            cachedData.data
        } else {
            println("Cache MISS: Call Data for $key")
            null
        }
    }
    
    fun cacheCallData(userUid: String, date: LocalDate, data: CallDataAnalysisInfo) {
        val key = getCacheKey(userUid, date)
        callDataCache[key] = CachedData(data)
        println("Cached Call Data for $key")
    }
    
    // Device Interaction Cache Methods
    fun getDeviceInteractionData(userUid: String, date: LocalDate): DeviceInteractionAnalysisInfo? {
        val key = getCacheKey(userUid, date)
        val cachedData = deviceInteractionCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: Device Interaction Data for $key")
            cachedData.data
        } else {
            println("Cache MISS: Device Interaction Data for $key")
            null
        }
    }
    
    fun cacheDeviceInteractionData(userUid: String, date: LocalDate, data: DeviceInteractionAnalysisInfo) {
        val key = getCacheKey(userUid, date)
        deviceInteractionCache[key] = CachedData(data)
        println("Cached Device Interaction Data for $key")
    }
    
    // Cognitive Scores Summary Cache Methods
    fun getCognitiveScoresSummary(userUid: String, date: LocalDate): CognitiveScoresSummary? {
        val key = getCacheKey(userUid, date)
        val cachedData = cognitiveScoresSummaryCache[key]
        return if (cachedData != null && !cachedData.isExpired()) {
            println("Cache HIT: Cognitive Scores Summary for $key")
            cachedData.data
        } else {
            println("Cache MISS: Cognitive Scores Summary for $key")
            null
        }
    }
    
    fun cacheCognitiveScoresSummary(userUid: String, date: LocalDate, data: CognitiveScoresSummary) {
        val key = getCacheKey(userUid, date)
        cognitiveScoresSummaryCache[key] = CachedData(data, cacheDurationMinutes = LONG_CACHE_DURATION_MINUTES)
        println("Cached Cognitive Scores Summary for $key")
    }
    
    // Cache Management Methods
    
    /**
     * Clear all cached data for a specific user and date
     */
    fun clearCacheForDate(userUid: String, date: LocalDate) {
        val key = getCacheKey(userUid, date)
        overallPerformanceCache.remove(key)
        typingPercentagesCache.remove(key)
        sleepDataCache.remove(key)
        gpsDataCache.remove(key)
        activityDataCache.remove(key)
        callDataCache.remove(key)
        deviceInteractionCache.remove(key)
        cognitiveScoresSummaryCache.remove(key)
        println("Cleared all cache for $key")
    }
    
    /**
     * Clear all cached data for a specific user
     */
    fun clearCacheForUser(userUid: String) {
        val keysToRemove = mutableListOf<String>()
        
        // Collect keys that start with userUid
        listOf(
            overallPerformanceCache,
            typingPercentagesCache,
            sleepDataCache,
            gpsDataCache,
            activityDataCache,
            callDataCache,
            deviceInteractionCache,
            cognitiveScoresSummaryCache
        ).forEach { cache ->
            keysToRemove.addAll(cache.keys.filter { it.startsWith(userUid) })
        }
        
        // Remove from all caches
        keysToRemove.forEach { key ->
            overallPerformanceCache.remove(key)
            typingPercentagesCache.remove(key)
            sleepDataCache.remove(key)
            gpsDataCache.remove(key)
            activityDataCache.remove(key)
            callDataCache.remove(key)
            deviceInteractionCache.remove(key)
            cognitiveScoresSummaryCache.remove(key)
        }
        
        println("Cleared all cache for user: $userUid")
    }
    
    /**
     * Clear all expired entries from all caches
     */
    fun clearExpiredEntries() {
        listOf(
            overallPerformanceCache,
            typingPercentagesCache,
            sleepDataCache,
            gpsDataCache,
            activityDataCache,
            callDataCache,
            deviceInteractionCache,
            cognitiveScoresSummaryCache
        ).forEach { cache ->
            val expiredKeys = cache.entries.filter { it.value.isExpired() }.map { it.key }
            expiredKeys.forEach { key -> cache.remove(key) }
        }
        println("Cleared expired cache entries")
    }
    
    /**
     * Clear all cached data
     */
    fun clearAllCache() {
        overallPerformanceCache.clear()
        typingPercentagesCache.clear()
        sleepDataCache.clear()
        gpsDataCache.clear()
        activityDataCache.clear()
        callDataCache.clear()
        deviceInteractionCache.clear()
        cognitiveScoresSummaryCache.clear()
        println("Cleared all cache")
    }
    
    /**
     * Get cache statistics for debugging
     */
    fun getCacheStats(): String {
        return """
            Cache Statistics:
            - Overall Performance: ${overallPerformanceCache.size} entries
            - Typing Percentages: ${typingPercentagesCache.size} entries
            - Sleep Data: ${sleepDataCache.size} entries
            - GPS Data: ${gpsDataCache.size} entries
            - Activity Data: ${activityDataCache.size} entries
            - Call Data: ${callDataCache.size} entries
            - Device Interaction: ${deviceInteractionCache.size} entries
            - Cognitive Scores Summary: ${cognitiveScoresSummaryCache.size} entries
            Total entries: ${getTotalCacheSize()}
        """.trimIndent()
    }
    
    private fun getTotalCacheSize(): Int {
        return overallPerformanceCache.size +
                typingPercentagesCache.size +
                sleepDataCache.size +
                gpsDataCache.size +
                activityDataCache.size +
                callDataCache.size +
                deviceInteractionCache.size +
                cognitiveScoresSummaryCache.size
    }
    
    /**
     * Force refresh data for a specific date (clears cache and will fetch fresh data on next request)
     */
    fun forceRefresh(userUid: String, date: LocalDate) {
        clearCacheForDate(userUid, date)
        println("Forced refresh for user $userUid on date $date")
    }
}
