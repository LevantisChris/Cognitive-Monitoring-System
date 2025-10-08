package com.levantis.logmyself.analysis_database

import com.levantis.logmyself.BuildConfig
import com.levantis.logmyself.analysis_database.data_classes.*
import com.levantis.logmyself.auth.AuthManager
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.query.Columns
import io.github.jan.supabase.postgrest.query.Order
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.postgrest.from
import kotlinx.datetime.LocalDate

/*
*  Class to manage all the operation with the Analysis Database (Supabase)
* */

class DatabaseService {

    private val supabase = createSupabaseClient(
        supabaseUrl = BuildConfig.SUPABASE_URL,
        supabaseKey = BuildConfig.SUPABASE_ANON_KEY
    ) {
        install(Postgrest)
    }
    
    // Cache manager for local data storage
    private val cacheManager = CacheManager()

    /* Get from the analysis DB all the final scores for each category
    and calculate with weights an overall score
    Args:
        date: String - date for which to get the scores (format: "YYYY-MM-DD")
        user: String - user UID
    Returns:
        List<Any> - List with Total score and final decision
        null - if date is empty or error occurs
    */
    suspend fun calculateOverallPerformance(date: LocalDate, userUid: String): Pair<Double, String>? {
        return try {
            if (userUid.isEmpty() || date.toString().isEmpty()) {
                println("User UID is empty")
                return null
            }

            // Check cache first
            cacheManager.getOverallPerformance(userUid, date)?.let { cachedData ->
                return cachedData
            }

            println("Getting overall performance from the analysis DB")
            val cognitiveScoresSummary = getCognitiveScoresSummary(userUid, date)

            if (cognitiveScoresSummary == null) {
                println("Cognitive Scores Summary is null")
                return null
            } else {
                println("Cognitive Scores Summary retrieved successfully: $cognitiveScoresSummary")
            }

            cognitiveScoresSummary.let { summary ->
                val score = summary.meanCognitiveScore ?: 0.0
                val decision = summary.totalCognitiveDecision ?: "No Data"
                val result = Pair(score, decision)
                
                // Cache the result
                cacheManager.cacheOverallPerformance(userUid, date, result)
                result
            }
        } catch (e: Exception) {
            println("Error getting overall performance: ${e.message}")
            null
        }
    }

    /* Function to get the score percentages of a user at a particular date
    *  Ex. Critical: X%, Very Bad: X%, Normal: X%, Very Good: X%, Excellent: X%
    * Args:
    *   date: LocalDate - date for which to get the scores (format: "YYYY-MM-DD")
    *  user_uid: String - user UID
    * Returns:
    *   void - to be implemented
    * */
    suspend fun calculateTypingOverallScorePercentages(date: LocalDate, userUid: String): TypingCategoryPercentages? {
        try {
            if (date.toString().isEmpty() || userUid.isEmpty()) {
                println("Date or user UID is empty")
                return null
            }

            // Take the user ID of the LogBoard app, because these two apps have different user ID's.
            // At this point the user ID is the one from the LogBoard app.
            // Based on the user email, take the LogBoard user ID from the Users table
            val userEmail  = AuthManager.getCurrentUser()?.email

            if (userEmail == null || userEmail.isEmpty()) {
                println("User email is null or empty")
                return null
            }

            val logBoardUserUid = supabase.from("Users")
                .select(columns = Columns.list("user_uid")) {
                    filter {
                        eq("app_origin", userEmail)
                    }
                }.decodeSingle<LogBoardUser>()

            if (logBoardUserUid.user_uid.isEmpty()) {
                println("LogBoard user UID is null or empty")
                return null
            }

            // Set the userUid as the LogBoard user UID (this is only for typing analysis)
            val userUid = logBoardUserUid.user_uid

            // Check cache first
            cacheManager.getTypingPercentages(userUid, date)?.let { cachedData ->
                return cachedData
            }

            // Get the percentages of each score category for the user on the specified date
            val typingPercentages = getAllTypingPercentagesScores(userUid, date)

            if (typingPercentages == null) {
                println("Typing Percentages is null")
                return null
            }

            typingPercentages.let { percentages ->
                println("Critical: ${percentages.percentage_critical}%")
                println("Very Bad: ${percentages.percentage_very_bad}%")
                println("Normal: ${percentages.percentage_normal}%")
                println("Very Good: ${percentages.percentage_very_good}%")
                println("Excellent: ${percentages.percentage_excellent}%")
                
                // Cache the result
                cacheManager.cacheTypingPercentages(userUid, date, percentages)
            }

            return typingPercentages
        } catch (e: Exception) {
            println("Error getting typing overall score percentages: ${e.message}")
            return null
        }
    }

    /**
     * Function to get the sleep info for a user at a particular date
     * Args:
     *  date: LocalDate - date for which to get the sleep info (format: "YYYY-MM-DD")
     *  user_uid: String - user UID
     *  Returns:
     *   DailySleepSummary? - data class with all the sleep info (main sleep + naps)
     *   null - if date is empty or error occurs
     * */
    suspend fun calculateSleepPerformance(date: LocalDate, userUid: String): DailySleepSummary? {
        try {
            if (date.toString().isEmpty() || userUid.isEmpty()) {
                println("Date or user UID is empty")
                return null
            }

            // Check cache first
            cacheManager.getSleepData(userUid, date)?.let { cachedData ->
                return cachedData
            }

            // Based on the date get the sleeps that have as end_time that date
            val sleepsInfo = getSleepsInfo(userUid, date)

            if (sleepsInfo == null) {
                println("Sleep Data Analysis is null")
                return null
            }

            sleepsInfo.let { info ->
                println("Sleep from ${info.estimated_start_date_time} to ${info.estimated_end_date_time}")
                println("Total Duration: ${info.total_duration} minutes (Main: ${info.main_sleep_duration}, Naps: ${info.total_nap_duration})")
                println("Actual Duration: ${info.actual_duration} minutes")
                println("All Naps Details: ${info.nap_details}")
                println("Sleep Screen Time: ${info.sleep_screen_time} minutes")
                println("Sleep Quality Score: ${info.sleep_quality_score ?: "N/A"}")
                println("Number of Naps: ${info.number_of_naps}")
                println("Cognitive Score: ${info.cognitive_score ?: "N/A"}")
                println("Cognitive Decision: ${info.cognitive_decision ?: "N/A"}")
                
                // Cache the result
                cacheManager.cacheSleepData(userUid, date, info)
            }

            return sleepsInfo
        } catch (e: Exception) {
            println("Error getting sleep performance: ${e.message}")
            return null
        }
    }

    suspend fun calculateGpsMobilityPerformance(date: LocalDate, userUid: String): GPSDataAnalysisInfo? {
        try {
            if (date.toString().isEmpty() || userUid.isEmpty()) {
                println("Date or user UID is empty")
                return null
            }

            // Check cache first
            cacheManager.getGpsData(userUid, date)?.let { cachedData ->
                return cachedData
            }

            // Get the GPS mobility info for the user on the specified date
            val gpsDataInfo = getGpsMobilityInfo(userUid, date)

            if (gpsDataInfo == null) {
                println("GPS Mobility Data Analysis is null")
                return null
            }

            gpsDataInfo.let { info ->
                println("GPS Mobility Data for ${date}:")
                println("Total time spent at home: ${info.total_time_spend_in_home_seconds} seconds")
                println("Time period active: ${info.time_period_active}")
                println("Total time spent travelling: ${info.total_time_spend_travelling_seconds} seconds")
                println("Number of unique locations: ${info.number_of_unique_locations}")
                println("First move timestamp after 3am: ${info.first_move_timestamp_after_threeAm}")
                println("Average time spent in locations: ${info.average_time_spend_in_locations_hours} hours")
                println("Max distance timestamp: ${info.max_distance_timestamp}")
                println("Cognitive score: ${info.cognitive_score ?: "N/A"}")
                println("Cognitive decision: ${info.cognitive_decision ?: "N/A"}")
                println("Coords of Key Locations:")
                info.coordsOfKeyLocs?.forEach { loc ->
                    println(" - ID: ${loc.key_location_id}, Type: ${loc.key_loc_type}, Lat: ${loc.latitude}, Lon: ${loc.longitude}")
                }

                // Cache the result
                cacheManager.cacheGpsData(userUid, date, info)
            }

            return gpsDataInfo
        } catch (e: Exception) {
            println("Error getting GPS mobility performance: ${e.message}")
            return null
        }
    }

    suspend fun calculateActivityPerformance(date: LocalDate, userUid: String): ActivityDataAnalysisInfo? {
        try {
            if (date.toString().isEmpty() || userUid.isEmpty()) {
                println("Date or user UID is empty")
                return null
            }

            // Check cache first
            cacheManager.getActivityData(userUid, date)?.let { cachedData ->
                return cachedData
            }

            val activityInfo = getActivityInfo(date, userUid)

            if (activityInfo == null) {
                println("Activity Data Analysis is null")
                return null
            }

            activityInfo.let { info ->
                println("Activity Data Analysis for ${date}:")
                println("Activity Entropy: ${info.activity_entropy}")
                println("Inactivity Percentage: ${info.inactivity_percentage}")
                println("Daily Active Minutes: ${info.daily_active_minutes}")
                println("Cognitive Score: ${info.cognitive_score ?: "N/A"}")
                println("Cognitive Decision: ${info.cognitive_decision ?: "N/A"}")
                println("Activity Distribution Per Day Section Analysis:")
                info.activity_distribution_per_day_section_analysis?.forEach { dist ->
                    println(" - Day Section: ${dist.day_section}")
                    println("   In Vehicle: ${dist.in_vehicle}")
                    println("   On Bicycle: ${dist.on_bicycle}")
                    println("   On Foot: ${dist.on_foot}")
                    println("   Still: ${dist.still}")
                    println("   Tilting: ${dist.tilting}")
                    println("   Unknown: ${dist.unknown}")
                }
                
                // Cache the result
                cacheManager.cacheActivityData(userUid, date, info)
            }
            return activityInfo
        } catch (e: Exception) {
            println("Error getting activity performance: ${e.message}")
            return null
        }
    }

    suspend fun calculateCallPerformance(date: LocalDate, userUid: String): CallDataAnalysisInfo? {
        try {
            if (date.toString().isEmpty() || userUid.isEmpty()) {
                println("Date or user UID is empty")
                return null
            }

            // Check cache first
            cacheManager.getCallData(userUid, date)?.let { cachedData ->
                return cachedData
            }

            val callInfo = getCallInfo(date, userUid)

            if (callInfo == null) {
                println("Call Data Analysis is null")
                return null
            }

            callInfo.let { info ->
                println("Call Data Analysis for ${date}:")
                println("Day Call Ratio: ${info.day_call_ratio}")
                println("Night Call Ratio: ${info.night_call_ratio}")
                println("Avg Call Duration: ${info.avg_call_duration}")
                println("Total Calls in a Day: ${info.total_calls_in_a_day}")
                println("Missed Call Ratio: ${info.missed_call_ratio}")
                println("Cognitive Score: ${info.cognitive_score ?: "N/A"}")
                println("Cognitive Decision: ${info.cognitive_decision ?: "N/A"}")
                
                // Cache the result
                cacheManager.cacheCallData(userUid, date, info)
            }

            return callInfo
        } catch (e: Exception) {
            println("Error getting call performance: ${e.message}")
            return null
        }
    }

    suspend fun calculateDeviceInteractionPerformance(date: LocalDate, userUid: String): DeviceInteractionAnalysisInfo? {
        try {
            if (date.toString().isEmpty() || userUid.isEmpty()) {
                println("Date or user UID is empty")
                return null
            }

            // Check cache first
            cacheManager.getDeviceInteractionData(userUid, date)?.let { cachedData ->
                return cachedData
            }

            val deviceInteractionInfo = getDeviceInteractionInfo(date, userUid)

            if (deviceInteractionInfo == null) {
                println("Device Interaction Data Analysis is null")
                return null
            }

            deviceInteractionInfo.let { info ->
                println("Device Interaction Data Analysis for ${date}:")
                println("Total Screen Time: ${info.total_screen_time_sec}")
                println("Total Low Light Time: ${info.total_low_light_time_sec}")
                println("Total Device Drop Events: ${info.total_device_drop_events}")
                println("Cognitive Score: ${info.cognitive_score ?: "N/A"}")
                println("Cognitive Decision: ${info.cognitive_decision ?: "N/A"}")
                
                // Cache the result
                cacheManager.cacheDeviceInteractionData(userUid, date, info)
            }

            return deviceInteractionInfo
        } catch (e: Exception) {
            println("Error getting device interaction performance: ${e.message}")
            return null
        }
    }

    /** 
     * Function to get the latest baseline values for a metric for a specific user
     * Args:
     *  metric: String - name of the metric, as it is in the Baseline_Metrics table
     *  userUid: String - user UID
     * Returns:
     *  BaselineMetrics? - baseline values for the metric
     *  null - if error occurs
     */
    suspend fun getLatestBaselineValues(metric: String, userUid: String): BaselineMetrics? {
        return try {
            val baselineValues = supabase.from("Baseline_Metrics")
                .select(columns = Columns.list("metric_name", "baseline_mean", "baseline_std", "baseline_median", "baseline_mad")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("metric_name", metric)
                    }
                    order("date_created", order = Order.DESCENDING)
                    limit(1)
                }.decodeSingle<BaselineMetrics>()
            baselineValues
        } catch (e: Exception) {
            println("Error getting baseline values: ${e.message}")
            null
        }
    }

    //////////////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Get the Device Interaction info needed for the UI visualization for a specific user and date
     */
    suspend fun getDeviceInteractionInfo(date: LocalDate, userUid: String): DeviceInteractionAnalysisInfo? {
        return try {
            val deviceInteractionInfo = supabase.from("Device_Interaction_Data_Analysis")
                .select(columns = Columns.list("id", "total_screen_time_sec", "total_low_light_time_sec", "total_device_drop_events", "cognitive_score", "cognitive_decision")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date.toString())
                    }
                }.decodeSingle<DeviceInteractionAnalysisBase>()

            if (deviceInteractionInfo.id.isEmpty()) {
                println("Device Interaction Data Analysis ID is null")
                return null
            }

            // Then use the id from above to get the next data from the table called Circadian_Screen_Time_Analysis
            val circadianScreenTimeAnalysis = supabase.from("Circadian_Screen_Time_Analysis")
                .select(columns = Columns.list("day_section", "duration", "percentage")) {
                    filter {
                        eq("daily_interaction_data_analysis_id", deviceInteractionInfo.id)
                    }
                }.decodeSingle<CircadianScreenTimeAnalysis>()

            // Lastly combine all of the info into the DeviceInteractionAnalysisInfo data class
            DeviceInteractionAnalysisInfo(
                id = deviceInteractionInfo.id,
                total_screen_time_sec = deviceInteractionInfo.total_screen_time_sec,
                total_low_light_time_sec = deviceInteractionInfo.total_low_light_time_sec,
                total_device_drop_events = deviceInteractionInfo.total_device_drop_events,
                cognitive_score = deviceInteractionInfo.cognitive_score,
                cognitive_decision = deviceInteractionInfo.cognitive_decision,
                circadian_screen_time_analysis = circadianScreenTimeAnalysis
            )
        } catch (e: Exception) {
            println("Error getting device interaction info: ${e.message}")
            null
        }
    }

    /**
     * Get the Call info needed for the UI visualization for a specific user and date
     */
    suspend fun getCallInfo(date: LocalDate, userUid: String): CallDataAnalysisInfo? {
        return try {
            val callInfo = supabase.from("Call_Data_Analysis")
            .select(columns = Columns.list("day_call_ratio", "night_call_ratio", "avg_call_duration", "total_calls_in_a_day", "missed_call_ratio", "cognitive_score", "cognitive_decision")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date.toString())
                    }
                }.decodeSingle<CallDataAnalysisInfo>()

            return callInfo
        } catch (e: Exception) {
            println("Error getting call info: ${e.message}")
            null
        }
    }

    /**
     * Get the Activity info needed for the UI visualization for a specific user and date
     */
    suspend fun getActivityInfo(date: LocalDate, userUid: String): ActivityDataAnalysisInfo? {
        return try {
            // First we select from the Activity_Data_Analysis table
            val activityInfo = supabase.from("Activity_Data_Analysis")
                .select(columns = Columns.list("id", "activity_entropy", "inactivity_percentage", "daily_active_minutes", "cognitive_score", "cognitive_decision")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date.toString())
                    }
                }.decodeSingle<ActivityDataAnalysisBase>()

            if (activityInfo.id.isEmpty()) {
                println("Activity Data Analysis ID is null")
                return null
            }

            // Then we select from the Activity_Distribution_Per_Day_Section_Analysis table (multiple rows)
            val activityDistributionInfo = supabase.from("Activity_Distribution_Per_Day_Section_Analysis")
                .select(columns = Columns.list("day_section", "in_vehicle", "on_bicycle", "on_foot", "still", "tilting", "unknown")) {
                    filter {
                        eq("activity_data_analysis_id", activityInfo.id)
                    }
                }.decodeList<ActivityDistributionPerDaySectionAnalysis>()

            // Lastly combine all of the info into the ActivityDataAnalysisInfo data class
            ActivityDataAnalysisInfo(
                id = activityInfo.id,
                activity_entropy = activityInfo.activity_entropy,
                inactivity_percentage = activityInfo.inactivity_percentage,
                daily_active_minutes = activityInfo.daily_active_minutes,
                cognitive_score = activityInfo.cognitive_score,
                cognitive_decision = activityInfo.cognitive_decision,
                activity_distribution_per_day_section_analysis = activityDistributionInfo
            )
        } catch (e: Exception) {
            println("Error getting activity info: ${e.message}")
            null
        }
    }

    /**
     * Get GPS mobility info for a specific user and date
     */
    suspend fun getGpsMobilityInfo(userUid: String, date: LocalDate): GPSDataAnalysisInfo? {
        return try {
            // First get the info from the GPS_Data_Analysis table
            val gpsInfo = supabase.from("GPS_Data_Analysis")
                .select(columns = Columns.list(
                    "id",
                    "total_time_spend_in_home_seconds",
                    "time_period_active",
                    "total_time_spend_travelling_seconds",
                    "number_of_unique_locations",
                    "first_move_timestamp_after_3am",
                    "average_time_spend_in_locations_hours",
                    "cognitive_decision",
                    "cognitive_score"
                )) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date.toString())
                    }
                }.decodeSingle<GPSDataAnalysisBase>()
            
            if (gpsInfo.id.isEmpty()) {
                println("GPS Data Analysis ID is null")
                return null
            }

            // Then use the id from above to get the next data from the table called GPS_Spatial_Features
            val gpsSpatialFeatures = supabase.from("GPS_Spatial_Features")
                .select(columns = Columns.list(
                    "max_distance_timestamp"
                )) {
                    filter {
                        eq("gps_data_analysis_id", gpsInfo.id)
                    }
                }.decodeSingle<GPSSpatialFeatures>()

            // Lastly get the info using again the ID for the key location data (GPS_Key_Locations table)
            val gpsKeyLocations = supabase.from("GPS_Key_Locations")
                .select(columns = Columns.list(
                    "key_location_id",
                    "latitude",
                    "longitude",
                    "key_loc_type"
                )) {
                    filter {
                        eq("gps_data_analysis_id", gpsInfo.id)
                    }
                }.decodeList<KeyLocationInfo>()

            // Now construct the final data class to return (GPSDataAnalysisInfo)
            GPSDataAnalysisInfo(
                total_time_spend_in_home_seconds = gpsInfo.total_time_spend_in_home_seconds,
                time_period_active = gpsInfo.time_period_active,
                total_time_spend_travelling_seconds = gpsInfo.total_time_spend_travelling_seconds,
                number_of_unique_locations = gpsInfo.number_of_unique_locations,
                first_move_timestamp_after_threeAm = gpsInfo.first_move_timestamp_after_3am,
                average_time_spend_in_locations_hours = gpsInfo.average_time_spend_in_locations_hours,
                cognitive_decision = gpsInfo.cognitive_decision,
                cognitive_score = gpsInfo.cognitive_score,
                max_distance_timestamp = gpsSpatialFeatures.max_distance_timestamp,
                coordsOfKeyLocs = gpsKeyLocations
            )
        } catch (e: Exception) {
            println("Error fetching GPS mobility info: ${e.message}")
            null
        }
    }

    /**
     * Get sleeps info of a date
     * We retrieve the sleeps (of type: main and nap's) that have as end_time that date
     */
    suspend fun getSleepsInfo(userUid: String, date: LocalDate): DailySleepSummary? {
        return try {
            println("Fetching sleep info for user: $userUid on date: $date")
            
            val sleepRecords = supabase.from("Sleep_Data_Analysis")
                .select(columns = Columns.list(
                    "estimated_start_date_time",
                    "estimated_end_date_time",
                    "total_duration",
                    "actual_duration",
                    "sleep_screen_time",
                    "sleep_quality_score", // null for type = nap
                    "type",
                    "cognitive_score", // don't include them for type = nap
                    "cognitive_decision" // don't include them for type = nap
                )) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date.toString())
                    }
                }.decodeList<SleepDataAnalysisInfo>()

            if (sleepRecords.isEmpty()) {
                println("No sleep records found for date: $date")
                return null
            }

            println("Found ${sleepRecords.size} sleep records for $date")
            
            // Debug: Print all sleep records with their dates
            sleepRecords.forEach { record ->
                println("  - ${record.type}: start=${record.estimated_start_date_time}, end=${record.estimated_end_date_time}")
            }
            
            // Separate main sleep from naps
            val mainSleep = sleepRecords.find { it.type.equals("main_sleep", ignoreCase = true) }
            val naps = sleepRecords.filter { it.type.equals("nap_sleep", ignoreCase = true) }
            println("Main sleep: ${if (mainSleep != null) "found" else "NOT found"}, Naps: ${naps.size}")
            
            if (mainSleep == null) {
                println("No main sleep found, using first record as main sleep")
                // If no main sleep found, use the first record
                val firstRecord = sleepRecords.first()
                return DailySleepSummary(
                    estimated_start_date_time = firstRecord.estimated_start_date_time,
                    estimated_end_date_time = firstRecord.estimated_end_date_time,
                    total_duration = sleepRecords.sumOf { it.total_duration },
                    actual_duration = sleepRecords.sumOf { it.actual_duration },
                    sleep_screen_time = firstRecord.sleep_screen_time,
                    sleep_quality_score = firstRecord.sleep_quality_score,
                    cognitive_score = firstRecord.cognitive_score,
                    cognitive_decision = firstRecord.cognitive_decision,
                    main_sleep_duration = firstRecord.total_duration,
                    total_nap_duration = naps.sumOf { it.total_duration },
                    number_of_naps = naps.size,
                    nap_details = naps
                )
            }

            println("Main sleep found: $mainSleep")

            // Create aggregated summary
            DailySleepSummary(
                estimated_start_date_time = mainSleep.estimated_start_date_time,
                estimated_end_date_time = mainSleep.estimated_end_date_time,
                total_duration = sleepRecords.sumOf { it.total_duration }, // Main sleep + all naps
                actual_duration = sleepRecords.sumOf { it.actual_duration },
                sleep_screen_time = mainSleep.sleep_screen_time,
                sleep_quality_score = mainSleep.sleep_quality_score, // Only main sleep has quality score
                cognitive_score = mainSleep.cognitive_score,
                cognitive_decision = mainSleep.cognitive_decision,
                main_sleep_duration = mainSleep.total_duration,
                total_nap_duration = naps.sumOf { it.total_duration },
                number_of_naps = naps.size,
                nap_details = naps
            )
            
        } catch (e: Exception) {
            println("Error fetching sleeps info: ${e.message}")
            null
        }
    }
    /**
     * Get all typing percentages scores
     */
    suspend fun getAllTypingPercentagesScores(userUid: String, date: LocalDate): TypingCategoryPercentages? {
        return try {
            // First get the Daily_Analyses record
            val dailyAnalysis = supabase.from("Daily_Analyses")
                .select(columns = Columns.list("id", "user_uid", "day_analyzed")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date)
                    }
                }.decodeSingle<DailyAnalysis>()

            println("Daily Analysis ID retrieved for typing percentages: ${dailyAnalysis.id}, user: ${dailyAnalysis.user_uid}, date: ${dailyAnalysis.day_analyzed}")

            // Then get the typing percentages per category for that analysis
            val typingCategoryPercentagesList = supabase.from("Daily_Analysis_Typing_Stats")
                .select(columns = Columns.list("analysis_id", "percentage_critical", "percentage_very_bad", "percentage_normal", "percentage_very_good", "percentage_excellent")) {
                    filter {
                        eq("analysis_id", dailyAnalysis.id)
                    }
                }.decodeList<TypingCategoryPercentages>()

            typingCategoryPercentagesList.firstOrNull()
        } catch (e: Exception) {
            println("Error fetching typing percentages scores: ${e.message}")
            null
        }
    }

    /**
     * Get all cognitive scores for a specific user and date
     */
    suspend fun getCognitiveScoresSummary(userUid: String, date: LocalDate): CognitiveScoresSummary? {
        val dateString = date.toString()

        // Check cache first
        cacheManager.getCognitiveScoresSummary(userUid, date)?.let { cachedData ->
            return cachedData
        }

        try {
            // Get all cognitive scores in parallel
            val sleepScore = getSleepCognitiveScore(userUid, dateString)
            val activityScore = getActivityCognitiveScore(userUid, dateString)
            val callScore = getCallCognitiveScore(userUid, dateString)
            val gpsScore = getGPSCognitiveScore(userUid, dateString)
            val deviceInteractionScore = getDeviceInteractionCognitiveScore(userUid, dateString)
//            val typingSessionScore = getTypingSessionCognitiveScore(userUid, dateString)
            val typingScore = getTypingCognitiveScore(userUid, dateString)

            // Collect all non-null scores
            val allScores = listOfNotNull(
                sleepScore,
                activityScore,
                callScore,
                gpsScore,
                deviceInteractionScore,
//                typingSessionScore,
                typingScore
            )

            // Calculate mean if we have scores
            val meanScore = if (allScores.isNotEmpty()) {
                allScores.average()
            } else null

            // Find the decision classification based on the mean score
            val totalCognitiveDecision = meanScore?.let { classifyDecision(it) }

            val result = CognitiveScoresSummary(
                userUid = userUid,
                analysisDate = dateString,
                sleepCognitiveScore = sleepScore,
                activityCognitiveScore = activityScore,
                callCognitiveScore = callScore,
                gpsCognitiveScore = gpsScore,
                deviceInteractionCognitiveScore = deviceInteractionScore,
//                typingSessionCognitiveScore = typingSessionScore,
                typingCognitiveScore = typingScore,
                meanCognitiveScore = meanScore,
                totalCognitiveDecision = totalCognitiveDecision,
                totalScoresAvailable = allScores.size
            )
            
            // Cache the result
            cacheManager.cacheCognitiveScoresSummary(userUid, date, result)
            println("Cognitive summary: $result")
            return result

        } catch (e: Exception) {
            println("Error fetching cognitive scores: ${e.message}")
            return null
        }
    }

    /* Classify decision based on the score derived
    * Note this is the same scoring system the system use
    * for every category. */
    private fun classifyDecision(score: Double): String {
        return when {
            score > 0.965 -> "Excellent"
            score > 0.586 -> "Very Good"
            score < -0.952 -> "Critical"
            score < -0.575 -> "Very Bad"
            else -> "Normal"
        }
    }

    /**
     * Get Sleep cognitive score
     */
    private suspend fun getSleepCognitiveScore(userUid: String, date: String): Double? {
        return try {
            val results = supabase.from("Sleep_Data_Analysis")
                .select(columns = Columns.list("day_analyzed", "user_uid", "cognitive_score")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date)
                    }
                }.decodeList<SleepCognitiveScore>()
            
            val validScore = results.firstOrNull { it.cognitive_score != null }?.cognitive_score
            println("Sleep cognitive score: $validScore")
            validScore
        } catch (e: Exception) {
            println("Error fetching Sleep cognitive score: ${e.message}")
            null
        }
    }

    /**
     * Get Activity cognitive score
     */
    private suspend fun getActivityCognitiveScore(userUid: String, date: String): Double? {
        return try {
            val results = supabase.from("Activity_Data_Analysis")
                .select(columns = Columns.list("day_analyzed", "user_uid", "cognitive_score")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date)
                    }
                }.decodeList<ActivityCognitiveScore>()
            
            val validScore = results.firstOrNull { it.cognitive_score != null }?.cognitive_score
            println("Activity cognitive score: $validScore")
            validScore
        } catch (e: Exception) {
            println("Error fetching Activity cognitive score: ${e.message}")
            null
        }
    }

    /**
     * Get Call cognitive score
     */
    private suspend fun getCallCognitiveScore(userUid: String, date: String): Double? {
        return try {
            val results = supabase.from("Call_Data_Analysis")
                .select(columns = Columns.list("day_analyzed", "user_uid", "cognitive_score")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date)
                    }
                }.decodeList<CallCognitiveScore>()

            val validScore = results.firstOrNull { it.cognitive_score != null }?.cognitive_score
            println("Call cognitive score: $validScore")
            validScore
        } catch (e: Exception) {
            println("Error fetching Call cognitive score: ${e.message}")
            null
        }
    }

    /**
     * Get GPS cognitive score
     */
    private suspend fun getGPSCognitiveScore(userUid: String, date: String): Double? {
        return try {
            val results = supabase.from("GPS_Data_Analysis")
                .select(columns = Columns.list("day_analyzed", "user_uid", "cognitive_score")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date)
                    }
                }.decodeList<GPSCognitiveScore>()
            
            // Filter out invalid scores and get the first valid one
            val validScore = results.firstOrNull { it.cognitive_score != null }?.cognitive_score
            println("GPS cognitive score: $validScore")
            validScore
        } catch (e: Exception) {
            println("Error fetching GPS cognitive score: ${e.message}")
            null
        }
    }

    /**
     * Get Device Interaction cognitive score
     */
    private suspend fun getDeviceInteractionCognitiveScore(userUid: String, date: String): Double? {
        return try {
            val results = supabase.from("Device_Interaction_Data_Analysis")
                .select(columns = Columns.list("day_analyzed", "user_uid", "cognitive_score")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date)
                    }
                }.decodeList<DeviceInteractionCognitiveScore>()
            
            val validScore = results.firstOrNull { it.cognitive_score != null }?.cognitive_score
            println("Device Interaction cognitive score: $validScore")
            validScore
        } catch (e: Exception) {
            println("Error fetching Device Interaction cognitive score: ${e.message}")
            null
        }
    }

    /**
     * Get Typing Session cognitive score
     */
//    private suspend fun getTypingSessionCognitiveScore(userUid: String, date: String): Double? {
//        return try {
//            val result = supabase.from("Typing_Sessions")
//                .select(columns = Columns.list("cognitive_score")) {
//                    filter {
//                        eq("user_uid", userUid)
//                        eq("session_date", date)
//                        neq("cognitive_score", "null")
//                    }
//                }.decodeSingle<TypingSessionCognitiveScore>()
//            result.cognitive_score
//        } catch (e: Exception) {
//            null
//        }
//    }

    /**
     * Get Typing cognitive score from Daily Analysis
     */
    private suspend fun getTypingCognitiveScore(userUid: String, date: String): Double? {
        return try {
            // First get the Daily_Analyses record
            val dailyAnalysis = supabase.from("Daily_Analyses")
                .select(columns = Columns.list("id", "user_uid", "day_analyzed")) {
                    filter {
                        eq("user_uid", userUid)
                        eq("day_analyzed", date)
                    }
                }.decodeSingle<DailyAnalysis>()

            // Then get the typing stats for that analysis
            val typingStatsList = supabase.from("Daily_Analysis_Typing_Stats")
                .select(columns = Columns.list("total_typing_cognitive_score", "analysis_id")) {
                    filter {
                        eq("analysis_id", dailyAnalysis.id)
                    }
                }.decodeList<TypingStats>()

            // Get the first valid cognitive score
            val validScore = typingStatsList.firstOrNull { it.total_typing_cognitive_score != null }?.total_typing_cognitive_score
            println("Typing cognitive score: $validScore")
            validScore
        } catch (e: Exception) {
            println("Error fetching typing cognitive score: ${e.message}")
            null
        }
    }
    
    // Cache management functions for UI use
    
    /**
     * Clear cache for a specific user and date
     * Useful when you know data has been updated and want fresh data
     */
    fun clearCacheForDate(userUid: String, date: LocalDate) {
        cacheManager.clearCacheForDate(userUid, date)
    }
    
    /**
     * Clear all cache for a specific user
     * Useful when switching users or user logs out
     */
    fun clearCacheForUser(userUid: String) {
        cacheManager.clearCacheForUser(userUid)
    }
    
    /**
     * Force refresh data for a specific date
     * This clears the cache and ensures next request fetches fresh data
     */
    fun forceRefreshData(userUid: String, date: LocalDate) {
        cacheManager.forceRefresh(userUid, date)
    }
    
    /**
     * Clear all cached data
     * Useful for memory management or when switching apps
     */
    fun clearAllCache() {
        cacheManager.clearAllCache()
    }
    
    /**
     * Get cache statistics for debugging
     */
    fun getCacheStats(): String {
        return cacheManager.getCacheStats()
    }
    
    /**
     * Clear expired cache entries
     * Should be called periodically to free up memory
     */
    fun clearExpiredCache() {
        cacheManager.clearExpiredEntries()
    }
}
