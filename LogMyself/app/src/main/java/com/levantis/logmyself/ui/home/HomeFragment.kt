package com.levantis.logmyself.ui.home

import android.animation.ValueAnimator
import android.app.DatePickerDialog
import android.content.Context
import android.os.Bundle
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.animation.AccelerateDecelerateInterpolator
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.core.content.res.ResourcesCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.levantis.logmyself.R
import com.levantis.logmyself.analysis_database.DatabaseService
import com.levantis.logmyself.analysis_database.data_classes.*
import com.levantis.logmyself.auth.AuthManager
import com.levantis.logmyself.databinding.FragmentHomeBinding
import com.levantis.logmyself.ui.charts.bar_charts.SegmentCategory
import com.levantis.logmyself.ui.map.MapDialogFragment
import android.graphics.Color
import kotlinx.coroutines.launch
import java.time.LocalDate

class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!

    // Database service
    private val databaseService = DatabaseService()

    // Data storage properties
    private var overallPerformanceData: Pair<Double, String>? = null
    private var typingPerformanceData: TypingCategoryPercentages? = null
    private var sleepPerformanceData: DailySleepSummary? = null
    private var activityPerformanceData: ActivityDataAnalysisInfo? = null
    private var gpsPerformanceData: GPSDataAnalysisInfo? = null
    private var callPerformanceData: CallDataAnalysisInfo? = null
    private var deviceInteractionData: DeviceInteractionAnalysisInfo? = null

    // Loading state
    private var isLoading = false

    // Current user and date
    private var selectedDate: java.time.LocalDate = java.time.LocalDate.now().minusDays(1) // Default to yesterday
    private val currentDate: LocalDate
        get() = selectedDate
    
    private val currentUserUid: String?
        get() = AuthManager.getCurrentUser()?.uid

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        val root: View = binding.root

        return root
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupInitialUI()
        setupClickListeners()
        loadAllData()
    }

    /**
     * Setup initial UI state and show loading animation
     */
    private fun setupInitialUI() {
        // Show loading state for all cards
        showLoadingState()
        
        // Update date in welcome message
        updateWelcomeMessage()
    }

    /**
     * Setup click listeners for interactive elements
     */
    private fun setupClickListeners() {
        binding.viewMapMessageTextView.setOnClickListener {
            onViewMapClicked()
        }
        
        // Set up click listener for date selection (all previous dates available)
        binding.welcomeTextView.setOnClickListener {
            showDatePicker()
        }
    }

    /**
     * Handle view map click event
     */
    private fun onViewMapClicked() {
        // Get key locations from GPS data
        val keyLocations = gpsPerformanceData?.coordsOfKeyLocs ?: emptyList()
        
        if (keyLocations.isEmpty()) {
            // Show message if no location data is available
            println("No location data available for map display")
            return
        }
        
        // Create and show the map dialog
        val mapDialog = MapDialogFragment.newInstance(keyLocations)
        mapDialog.show(parentFragmentManager, "MapDialog")
    }

    /**
     * Show date picker dialog with all previous dates available
     */
    private fun showDatePicker() {
        val today: LocalDate = LocalDate.now()
        val maxDate: LocalDate = today.minusDays(1) // Yesterday is the latest selectable date
        val minDate: LocalDate = LocalDate.of(2020, 1, 1) // Allow dates back to 2020
        
        // Convert to Calendar for DatePickerDialog
        val calendar = java.util.Calendar.getInstance()
        calendar.set(selectedDate.year, selectedDate.monthValue - 1, selectedDate.dayOfMonth)
        
        val datePickerDialog = DatePickerDialog(
            requireContext(),
            { _, year, month, dayOfMonth ->
                val selectedDateLocal = java.time.LocalDate.of(year, month + 1, dayOfMonth)
                
                // Validate the selected date is within allowed range
                if (selectedDateLocal > maxDate || selectedDateLocal < minDate) {
                    // Show error message or keep current date
                    println("Selected date is outside allowed range (must be before today and after 2020)")
                    return@DatePickerDialog
                }
                
                // Update selected date and refresh data
                selectedDate = selectedDateLocal
                println("Date picker: Selected date changed to: $selectedDate")
                updateWelcomeMessage()
                
                // Show loading state and reload data
                showLoadingState()
                loadAllData()
            },
            calendar.get(java.util.Calendar.YEAR),
            calendar.get(java.util.Calendar.MONTH),
            calendar.get(java.util.Calendar.DAY_OF_MONTH)
        )
        
        // Set date limits
        val maxCalendar = java.util.Calendar.getInstance()
        maxCalendar.set(maxDate.year, maxDate.monthValue - 1, maxDate.dayOfMonth)
        datePickerDialog.datePicker.maxDate = maxCalendar.timeInMillis
        
        val minCalendar = java.util.Calendar.getInstance()
        minCalendar.set(minDate.year, minDate.monthValue - 1, minDate.dayOfMonth)
        datePickerDialog.datePicker.minDate = minCalendar.timeInMillis
        
        datePickerDialog.show()
    }

    /**
     * Clear all cached data
     */
    private fun clearAllData() {
        overallPerformanceData = null
        typingPerformanceData = null
        sleepPerformanceData = null
        activityPerformanceData = null
        gpsPerformanceData = null
        callPerformanceData = null
        deviceInteractionData = null
    }

    /**
     * Load all data from database
     */
    private fun loadAllData() {
        val userUid = currentUserUid
        if (userUid == null) {
            // Print not user UID found
            println("No user UID found, cannot load data.")
            showNoDataState()
            return
        }

        // Prevent multiple simultaneous loads
        if (isLoading) {
            println("Already loading data, skipping duplicate request")
            return
        }

        println("Loading data for user: $userUid on date: $currentDate")

        // Clear old data before loading new data
        clearAllData()

        isLoading = true
        
        lifecycleScope.launch {
            try {
                val kotlinxDate = kotlinx.datetime.LocalDate(currentDate.year, currentDate.monthValue, currentDate.dayOfMonth)
                // Load all data in parallel
                val overallJob = lifecycleScope.launch {
                    overallPerformanceData = databaseService.calculateOverallPerformance(kotlinxDate, userUid)
                }
                val typingJob = lifecycleScope.launch {
                    typingPerformanceData = databaseService.calculateTypingOverallScorePercentages(kotlinxDate, userUid)
                }
                val sleepJob = lifecycleScope.launch {
                    sleepPerformanceData = databaseService.calculateSleepPerformance(kotlinxDate, userUid)
                }
                val activityJob = lifecycleScope.launch {
                    activityPerformanceData = databaseService.calculateActivityPerformance(kotlinxDate, userUid)
                }
                val gpsJob = lifecycleScope.launch {
                    gpsPerformanceData = databaseService.calculateGpsMobilityPerformance(kotlinxDate, userUid)
                }
                val callJob = lifecycleScope.launch {
                    callPerformanceData = databaseService.calculateCallPerformance(kotlinxDate, userUid)
                }
                val deviceJob = lifecycleScope.launch {
                    deviceInteractionData = databaseService.calculateDeviceInteractionPerformance(kotlinxDate, userUid)
                }

                // Wait for all jobs to complete
                overallJob.join()
                typingJob.join()
                sleepJob.join()
                activityJob.join()
                gpsJob.join()
                callJob.join()
                deviceJob.join()

                // Update UI with loaded data
                hideLoadingState()
                updateUIWithData()
                
            } catch (e: Exception) {
                hideLoadingState()
                showNoDataState()
                e.printStackTrace()
            } finally {
                isLoading = false
            }
        }
    }

    /**
     * Update welcome message with current date
     */
    private fun updateWelcomeMessage() {
        val dateText = formatDateForDisplay(currentDate)
        binding.welcomeTextView.text = dateText
    }

    /**
     * Format date for display
     */
    private fun formatDateForDisplay(date: LocalDate): String {
        val months = arrayOf(
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        )
        return "${date.dayOfMonth} ${months[date.monthValue - 1]}, ${date.year}"
    }

    /**
     * Show loading animation for all cards
     */
    private fun showLoadingState() {
        // Hide all card content and show loading animation
        setCardLoadingState(binding.cardProfile, true)
        setCardLoadingState(binding.cardSleep, true)
        setCardLoadingState(binding.cardActivityPerformance, true)
        setCardLoadingState(binding.cardMobility, true)
        setCardLoadingState(binding.cardDeviceInteractionData, true)
        setCardLoadingState(binding.cardCallData, true)
        
        // Update overall performance message
        binding.insightOfTheDayTextView.text = "Loading your daily insights..."
        binding.overallScore.text = "Calculating..."
    }

    /**
     * Hide loading animation
     */
    private fun hideLoadingState() {
        setCardLoadingState(binding.cardProfile, false)
        setCardLoadingState(binding.cardSleep, false)
        setCardLoadingState(binding.cardActivityPerformance, false)
        setCardLoadingState(binding.cardMobility, false)
        setCardLoadingState(binding.cardDeviceInteractionData, false)
        setCardLoadingState(binding.cardCallData, false)
    }

    /**
     * Set loading state for a specific card
     */
    private fun setCardLoadingState(card: CardView, isLoading: Boolean) {
        if (isLoading) {
            // Create loading animation
            createLoadingAnimation(card)
        } else {
            // Remove loading animation
            removeLoadingAnimation(card)
        }
    }

    /**
     * Create a subtle loading animation for cards
     */
    private fun createLoadingAnimation(card: CardView) {
        val animator = ValueAnimator.ofFloat(0.7f, 1.0f)
        animator.duration = 1500
        animator.repeatCount = ValueAnimator.INFINITE
        animator.repeatMode = ValueAnimator.REVERSE
        animator.interpolator = AccelerateDecelerateInterpolator()
        
        animator.addUpdateListener { animation ->
            val alpha = animation.animatedValue as Float
            card.alpha = alpha
        }
        
        card.tag = animator
        animator.start()
    }

    /**
     * Remove loading animation from card
     */
    private fun removeLoadingAnimation(card: CardView) {
        val animator = card.tag as? ValueAnimator
        animator?.cancel()
        card.alpha = 1.0f
        card.tag = null
    }

    /**
     * Show no data state for all components
     */
    private fun showNoDataState() {
        hideLoadingState()
        
        val noDataMessage = "The system does not know you yet!! Keep living!"
        
        // Update overall performance
        binding.insightOfTheDayTextView.text = noDataMessage
        binding.overallScore.text = "Score: Not available yet"
        
        // Update all card content to show no data message
        updateCardWithNoData(binding.cardProfile, "Typing Performance", noDataMessage)
        updateCardWithNoData(binding.cardSleep, "Sleep Performance", noDataMessage)
        updateCardWithNoData(binding.cardActivityPerformance, "Activity Performance", noDataMessage)
        updateCardWithNoData(binding.cardMobility, "Mobility Brief", noDataMessage)
        updateCardWithNoData(binding.cardDeviceInteractionData, "Device Interaction", noDataMessage)
        updateCardWithNoData(binding.cardCallData, "Social Interaction", noDataMessage)
    }

    /**
     * Update a card with no data message
     */
    private fun updateCardWithNoData(card: CardView, title: String, message: String) {
        // Clear the card content and show centered message
        val context = requireContext()
        
        // Find the main LinearLayout inside the card
        val cardContent = card.getChildAt(0) as? LinearLayout
        cardContent?.let { layout ->
            // Clear all existing content except the title
            val titleView = layout.getChildAt(0) as? TextView
            layout.removeAllViews()
            
            // Re-add the title
            titleView?.let { layout.addView(it) }
            
            // Create centered message TextView
            val messageTextView = TextView(context).apply {
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    topMargin = (20 * resources.displayMetrics.density).toInt()
                    bottomMargin = (20 * resources.displayMetrics.density).toInt()
                }
                text = message
                setTextColor(resources.getColor(R.color.white_in_card, null))
                textSize = 16f
                typeface = resources.getFont(R.font.montserrat_light)
                gravity = Gravity.CENTER
                textAlignment = View.TEXT_ALIGNMENT_CENTER
            }
            
            layout.addView(messageTextView)
        }
    }

    /**
     * Update UI with loaded data
     */
    private fun updateUIWithData() {
        // Update overall performance
        overallPerformanceData?.let { (score, decision) ->
            // Check if decision is "No Data" or empty
            if (decision.isBlank() || decision.equals("No Data", ignoreCase = true)) {
                binding.insightOfTheDayTextView.text = "For this day we are not yet ready to evaluate your performance!! 🤙"
                binding.overallScore.text = "Final System Decision: $decision"
            } else {
//                val formattedScore = (score * 100).toInt() // Convert to 0-100 scale
                
                val insightMessage = when (decision) {
                    "Excellent" -> "Your overall cognitive performance was excellent!\nYou were at your peak today! 🌟"
                    "Very Good" -> "Your overall cognitive performance was very good!\nKeep up the great work! 😊"
                    "Normal" -> "Your overall cognitive performance was normal.\nA steady day! 👍"
                    "Very Bad" -> "Your overall cognitive performance was challenging that day.\nTake some time to rest and recharge. 💙"
                    "Critical" -> "Your overall cognitive performance needs attention.\nPlease prioritize self-care and consider reaching out for support\nif you think you need it. ❤️"
                    else -> "Your overall cognitive performance was $decision!\nKeep going! 😊"
                }
                
                binding.insightOfTheDayTextView.text = insightMessage
                binding.overallScore.text = "Final System Decision: $decision"
            }
        }

        // Update typing performance data
        updateTypingPerformanceUI()
        
        // Update sleep performance data
        updateSleepPerformanceUI()
        
        // Update activity performance data
        updateActivityPerformanceUI()
        
        // Update GPS mobility data
        updateGPSMobilityUI()
        
        // Update device interaction data
        updateDeviceInteractionUI()
        
        // Update call data
        updateCallDataUI()
    }

    /**
     * Update typing performance UI
     */
    private fun updateTypingPerformanceUI() {
        typingPerformanceData?.let { data ->
            // Debug log to check data
            println("Critical: ${data.percentage_critical}%")
            println("Very Bad: ${data.percentage_very_bad}%") 
            println("Normal: ${data.percentage_normal}%")
            println("Very Good: ${data.percentage_very_good}%")
            println("Excellent: ${data.percentage_excellent}%")
            
            // Create categories for segmented bar
            val categories = listOf(
                SegmentCategory("Critical", data.percentage_critical.toFloat() / 100f, Color.parseColor("#FF0000"), android.R.color.white),
                SegmentCategory("Very Bad", data.percentage_very_bad.toFloat() / 100f, Color.parseColor("#FF6600"), android.R.color.white),
                SegmentCategory("Normal", data.percentage_normal.toFloat() / 100f, Color.parseColor("#FFCC00"), android.R.color.black),
                SegmentCategory("Very Good", data.percentage_very_good.toFloat() / 100f, Color.parseColor("#66CC00"), android.R.color.black),
                SegmentCategory("Excellent", data.percentage_excellent.toFloat() / 100f, Color.parseColor("#00CC66"), android.R.color.white)
            )
            
            // Set the segmented bar
            val segmentedBar = binding.root.findViewById<com.levantis.logmyself.ui.charts.bar_charts.SegmentedBarView>(
                com.levantis.logmyself.R.id.typingPerformanceSegmentedBar
            )
            segmentedBar?.setCategories(categories)
            
            // Determine the dominant category and create message
            val percentages = mapOf(
                "Critical" to data.percentage_critical,
                "Very Bad" to data.percentage_very_bad,
                "Normal" to data.percentage_normal,
                "Very Good" to data.percentage_very_good,
                "Excellent" to data.percentage_excellent
            )
            
            val dominantCategory = percentages.maxByOrNull { it.value }
            val message = when {
                dominantCategory?.value == 0.0 -> "No typing data available for analysis today! 📝"
                dominantCategory?.key == "Critical" -> "Today your typing was in a very critical day!! 🚨"
                dominantCategory?.key == "Very Bad" -> "Today your typing was in a very bad day!! 😔"
                dominantCategory?.key == "Normal" -> "Today your typing performance was normal! ⭐"
                dominantCategory?.key == "Very Good" -> "Today your typing was very good! Keep it up! 😊"
                dominantCategory?.key == "Excellent" -> "Excellent typing performance today! You're on fire! 🔥"
                else -> "Typing performance analyzed! 📊"
            }
            
            val messageTextView = binding.root.findViewById<TextView>(
                com.levantis.logmyself.R.id.typingPerformanceMessageTextView
            )
            messageTextView?.text = message
            
        } ?: run {
            // Show no data message for typing performance
            updateCardWithNoData(binding.cardProfile, "Typing Performance", "The system does not know you yet!!\nMaybe you didnt generate typing data that day\nUse LogBoard app to generate data")
        }
    }

    /**
     * Update sleep performance UI
     */
    private fun updateSleepPerformanceUI() {
        sleepPerformanceData?.let { data ->
            // Convert minutes to hours and minutes
            val totalHours = (data.main_sleep_duration / 60).toInt()
            val totalMinutes = (data.main_sleep_duration % 60).toInt()
            binding.totalSleepTimeTextView.text = "${totalHours}h and ${totalMinutes}min"
            
            // Parse and format start/end times to show only time
            val startDateTime = data.estimated_start_date_time?.let { dateTime ->
                val date = dateTime.substringBefore("T")
                val time = dateTime.substringAfter("T").substringBefore(".")
                val formattedDate = date.substringAfter("-").replace("-", "-")
                "$formattedDate $time"
            }
            val endDateTime = data.estimated_end_date_time?.let { dateTime ->
                val date = dateTime.substringBefore("T")
                val time = dateTime.substringAfter("T").substringBefore(".")
                val formattedDate = date.substringAfter("-").replace("-", "-")
                "$formattedDate $time"
            }
            binding.sleepStartTimeEndTimeTextView.text = "from $startDateTime to $endDateTime"
            
            // Sleep quality score
            data.sleep_quality_score?.let { score ->
                val percentage = (score * 100).toInt()
                binding.sleepQualityScoreTextView.text = "Sleep Quality Score $percentage out of 100"
            } ?: run {
                binding.sleepQualityScoreTextView.text = "Sleep Quality Score not available"
            }

            // Set up the nap text view
            // We have info.total_nap_duration and info.number_of_naps
            val napDuration = data.total_nap_duration
            val numberOfNaps = data.number_of_naps
            if (numberOfNaps > 0 && napDuration > 0) {
                val napDurationHours = (napDuration / 60.0)
                val napDurationFormatted = if (napDurationHours >= 1.0) {
                    String.format("%.1fh", napDurationHours)
                } else {
                    "${napDuration.toInt()}min"
                }
                binding.napMessageTextView.text = "Also found $numberOfNaps nap-sleep's of $napDurationFormatted duration"
            } else {
                binding.napMessageTextView.text = "Looks like you were nap-free today 💤"
            }
            
            // Overall sleep message based on cognitive decision
            val sleepMessage = when (data.cognitive_decision) {
                "Excellent" -> "Overall, your sleep is excellent, with scores much better than average 😴"
                "Very Good" -> "Your sleep quality is very good, keep it up! 😊"
                "Normal" -> "Your sleep is within normal range ⭐"
                "Very Bad" -> "Your sleep needs improvement, try to get better rest 😴"
                "Critical" -> "Your sleep quality is concerning, please prioritize better sleep habits 🚨"
                else -> "Sleep data analyzed successfully ✅"
            }
            binding.overallMessageAboutSleepPerformanceTextView.text = sleepMessage
            
        } ?: run {
            // Show no data message for sleep performance
            updateCardWithNoData(binding.cardSleep, "Sleep Performance", "The system does not know you yet!!\nKeep living!")
        }
    }

    /**
     * Update activity performance UI
     */
    private fun updateActivityPerformanceUI() {
        activityPerformanceData?.let { data ->
            // Activity entropy and inactivity
            data.inactivity_percentage?.let { inactivity ->
                val score = inactivity.toInt()
                if (score > 0) {
                    binding.inactivityPercentageTextView.text = "Inactivity Score $score out of 100"
                } else
                    binding.inactivityPercentageTextView.text = "Inactivity can not be calculated, sorry!"
            }
            
            data.activity_entropy?.let { entropy ->
                val score = (entropy * 100).toInt() // Scale entropy to 0-100
                if (score > 0) {
                    if (score < 50) {
                        binding.activityEntropyTextView.text = "Activity Diversity Score is very low ($score)"
                    } else if (score >= 50 && score <= 100) {
                        binding.activityEntropyTextView.text = "Activity Diversity Score is low ($score)"
                    } else if (score > 100 && score <= 250) {
                        binding.activityEntropyTextView.text = "Activity Diversity Score is medium ($score)"
                    } else if (score > 250 && score <= 450) {
                        binding.activityEntropyTextView.text = "Activity Diversity Score is high ($score)"
                    } else if (score > 450) {
                        binding.activityEntropyTextView.text = "Activity Diversity Score is very high ($score)"
                    }
                } else {
                    binding.activityEntropyTextView.text = "You seemed devoted to a single activity"
                }
            }
            
            // Active minutes
            data.daily_active_minutes?.let { minutes ->
                val hours = (minutes / 60).toInt()
                val mins = (minutes % 60).toInt()
                if (hours > 0 && mins > 0) {
                    binding.activeMinutesTextView.text = "You were active for ${hours}h ${mins}min in total."
                } else {
                    binding.activeMinutesTextView.text = "You were not active for any time that day!!,\nWe know you can do better! 😃"
                }
            }
            
            // Overall activity message
            val activityMessage = when (data.cognitive_decision) {
                "Excellent" -> "You seemed very active today, with high alternation between different activities, that is very good!! 💪"
                "Very Good" -> "Great activity levels today, keep moving! 🏃‍♂️"
                "Normal" -> "Your activity levels are normal for today ⭐"
                "Very Bad" -> "Try to be more active throughout the day 🚶‍♀️"
                "Critical" -> "Your activity levels are very low, try to move more 🏃‍♀️"
                else -> "Activity data analyzed successfully ✅"
            }
            binding.overallMessageAboutAcitvityPerformanceTextView.text = activityMessage

            // Update the activity per day sections
            // Take the top activty for each day section
            
			// Iterate the activity_distribution_per_day_section_analysis and for section take the activity with the higer percentage
			// Clear previous values
			binding.topMorningActivityTextView.text = "-"
			binding.topAfternoonActivityTextView.text = "-"
			binding.topEveningActivityTextView.text = "-"
			binding.topLateEveningActivityTextView.text = "-"
			binding.topNightActivityTextView.text = "-"

			// Debug: Check how many distribution entries we have
			println("Total activity distribution entries: ${data.activity_distribution_per_day_section_analysis?.size ?: 0}")
			
			data.activity_distribution_per_day_section_analysis?.forEach { dist ->
				println("Processing section: ${dist.day_section}")
				val candidates = listOf(
					"In Vehicle" to dist.in_vehicle,
					"On Bicycle" to dist.on_bicycle,
					"On Foot" to dist.on_foot,
					"Still" to dist.still,
					"Tilting" to dist.tilting,
					"Unknown" to dist.unknown
				).filter { it.second != null }
				val top = candidates.maxByOrNull { it.second ?: Double.NEGATIVE_INFINITY }
				top?.let { (label, value) ->
					println("Top activity for section ${dist.day_section}: $label ($value)")
					when (dist.day_section?.lowercase()) {
                        "morning" -> binding.topMorningActivityTextView.text = label
                        "afternoon" -> binding.topAfternoonActivityTextView.text = label
                        "evening" -> binding.topEveningActivityTextView.text = label
						"late evening" -> binding.topLateEveningActivityTextView.text = label
                        "night" -> binding.topNightActivityTextView.text = label
                    }
                }

			}
			
            
        } ?: run {
            // Show no data message for activity performance
            updateCardWithNoData(binding.cardActivityPerformance, "Activity Performance", "The system does not know you yet!!\nKeep living!")
        }
    }

    /**
     * Update GPS mobility UI
     */
    private fun updateGPSMobilityUI() {
        gpsPerformanceData?.let { data ->
            // Home time
            data.total_time_spend_in_home_seconds?.let { seconds ->
                val hours = (seconds / 3600).toInt()
                val minutes = ((seconds % 3600) / 60).toInt()
                if (hours > 0 && minutes > 0) {
                    binding.totalTimeHomeTextView.text = "Total time at home was ${hours}h and ${minutes}min"
                } else {
                    binding.totalTimeHomeTextView.text = "You spent no time at\nhome that day!!,\namazing! 😃"
                }
            }
            
            // Time period active message
            val timePeriodMessage = when (data.time_period_active) {
                1 -> "Most of your activity\nwas in the morning! ☀️"
                2 -> "Activity distributed\nthroughout the day"
                3 -> "Most of your activity\nwas in the evening! 🌅"
                else -> "No significant\nmovement was\nobserved on this day ☹️"
            }
            binding.timePeriodActiveMessageTextView.text = timePeriodMessage
            
            // Traveling time and first movement
            data.total_time_spend_travelling_seconds?.let { seconds ->
                val minutes = (seconds / 60).toInt()
                val firstMove = data.first_move_timestamp_after_threeAm?.let { timestamp ->
                    // Extract time from ISO forma 2025-07-11T17:37:42+00:00
                    if (timestamp.contains("T")) {
                        val timePart = timestamp.substringAfter("T").substringBefore("+")
                        // Remove seconds for cleaner display (HH:MM)
                        timePart.substringBeforeLast(":")
                    } else {
                        "N/A"
                    }
                } ?: "N/A"
                if (minutes > 0 && firstMove != "N/A") {
                    binding.travellingMessageTextView.text = "You spend ${minutes}min\ntravelling! with\nfirst outdoor movement\nat $firstMove"
                } else {
                    binding.travellingMessageTextView.text = "You spent no time\ntravelling that day!!,\nWe know you can do better! 😃"
                }
            }
            
            // Key locations
            data.number_of_unique_locations?.let { locations ->
                data.average_time_spend_in_locations_hours?.let { avgTime ->
                    val hours = avgTime.toInt()
                    val minutes = ((avgTime - hours) * 60).toInt()
                    // Exclude home location from the count
                    val nonHomeLocations = if (locations > 0) locations - 1 else 0
                    if (nonHomeLocations > 0 && hours > 0 && minutes > 0) {
                        binding.keyLocVisitsMessageTextView.text = "and you visit $nonHomeLocations key-locations\nwith average stay\ntime of ${hours}h and ${minutes}min"
                    } else {
                        binding.keyLocVisitsMessageTextView.text = "You visited no key-locations\nthat day!!,Is good to go\nout more! 🌞"
                    }
                }
            }
            
            // Furthest distance timestamp
            // Only show furthest distance if we visited more than one location (excluding home)
            val nonHomeLocations = data.number_of_unique_locations?.let { if (it > 0) it - 1 else 0 } ?: 0
            if (nonHomeLocations > 1) {
                data.max_distance_timestamp?.let { timestamp ->
                    // Extract time from ISO format 2025-07-11T17:37:42+00:00
                    val timeOnly = if (timestamp.contains("T")) {
                        val timePart = timestamp.substringAfter("T").substringBefore("+")
                        // Remove seconds for cleaner display (HH:MM)
                        timePart.substringBeforeLast(":")
                    } else {
                        "N/A"
                    }
                    
                    if (timeOnly != "N/A") {
                        binding.furthersDistanceReachedTimestampMessageTextView.text = "Furthest distance\nfrom Home 🏠\nreached at $timeOnly"
                    } else {
                        binding.furthersDistanceReachedTimestampMessageTextView.text = "No furthest distance reached that day!!"
                    }
                }
            } else {
                binding.furthersDistanceReachedTimestampMessageTextView.text = "No furthest distance reached that day!!"
            }
            
            // Overall mobility message
            val mobilityMessage = when (data.cognitive_decision) {
                "Excellent" -> "Outstanding mobility patterns today! 🚀"
                "Very Good" -> "Great mobility with good movement patterns! 👍"
                "Normal" -> "Overall your mobility seems good,\nwith decent amount of\nmovement through the day! 👍"
                "Very Bad" -> "Try to get out more and explore different places 🚶‍♂️"
                "Critical" -> "Very limited mobility today, try to move around more 🏃‍♀️"
                else -> "Mobility data analyzed successfully ✅\nKeep it up!"
            }
            binding.overallMobilityMessageTextView.text = mobilityMessage
            
        } ?: run {
            // Show no data message for GPS mobility
            updateCardWithNoData(binding.cardMobility, "Mobility Brief", "The system does not know you yet!!\nKeep living!")
        }
    }

    /**
     * Update device interaction UI
     */
    private fun updateDeviceInteractionUI() {
        deviceInteractionData?.let { data ->
            // Screen time
            data.total_screen_time_sec?.let { seconds ->
                val hours = (seconds / 3600).toInt()
                val minutes = ((seconds % 3600) / 60).toInt()
                if (hours > 0 && minutes > 0) {
                    binding.totalScreenTimeTextView.text = "Total screen time was ${hours}h and ${minutes}min"
                } else {
                    binding.totalScreenTimeTextView.text = "You spent no time on\nyour device that day!!"
                }
            }
            
            // Low light time
            data.total_low_light_time_sec?.let { seconds ->
                val minutes = (seconds / 60).toInt()
                if (minutes > 0) {
                    binding.totalLowLightTimeMessageTextView.text = "Spend ${minutes}m in\ndark environments 🌚"
                } else {
                    binding.totalLowLightTimeMessageTextView.text = "No time spent in dark\nenvironments that day,\ngood job!!"
                }
            }
            
            // Device drop events
            data.total_device_drop_events?.let { drops ->
                if (drops > 0) {
                    binding.totalDeviceDropEventsMessageTextView.text = "you drop the\ndevice $drops times\nthat day"
                } else {
                    binding.totalDeviceDropEventsMessageTextView.text = "Congratulations!\nYou had zero device\ndrops today."
                }
            }
            
            // Overall device interaction message
            val deviceMessage = when (data.cognitive_decision) {
                "Excellent" -> "Excellent device usage patterns! 📱✨"
                "Very Good" -> "Good device interaction habits! 👍"
                "Normal" -> "In general your device interaction seems fine,\nbut try to reduce screen time\nespecially before sleep! 📵"
                "Very Bad" -> "Consider reducing screen time for better wellbeing 📵"
                "Critical" -> "Excessive device usage detected, please take breaks 🚨"
                else -> "Device interaction data analyzed successfully ✅\nStay on track!"
            }
            binding.overallDeviceInteractionMessageTextView.text = deviceMessage
            
        } ?: run {
            // Show no data message for device interaction
            updateCardWithNoData(binding.cardDeviceInteractionData, "Device Interaction", "The system does not know you yet!!\nKeep living!"    )
        }
    }

    /**
     * Update call data UI
     */
    private fun updateCallDataUI() {
        callPerformanceData?.let { data ->
            val day_call_ratio = data.day_call_ratio
            val night_call_ratio = data.night_call_ratio

            if (day_call_ratio != null && night_call_ratio != null &&
                day_call_ratio >= 0 && day_call_ratio <= 100 &&
                night_call_ratio >= 0 && night_call_ratio <= 100 &&
                (day_call_ratio + night_call_ratio) > 0
            ) {
                // Segment bar update
                val bar = binding.segmentedBar
                val dayRatio = (day_call_ratio.toFloat() / 100f).coerceIn(0f, 1f)
                val nightRatio = (night_call_ratio.toFloat() / 100f).coerceIn(0f, 1f)
                bar.setCategories(
                    listOf(
                        SegmentCategory("Night calls", nightRatio, Color.parseColor("#272757"), android.R.color.white),
                        SegmentCategory("Day calls", dayRatio, Color.parseColor("#FFCC33"), android.R.color.black)
                    )
                )
            } else {
                // do nothing
            }

            // Average call duration
            data.avg_call_duration?.let { duration ->
                val minutes = (duration / 60).toInt()
                if (minutes > 0) {
                    binding.avgCallDurationMessageTextView.text = "Average call was\n${minutes}min"
                } else {
                    binding.avgCallDurationMessageTextView.text = "Cannot calculate average call duration,\nmaybe you use VoIP calls"
                }
            }
            
            // Total calls
            data.total_calls_in_a_day?.let { calls ->
                if (calls > 0) {
                    binding.totalCallsMessageTextView.text = "With total of $calls\ncalls that day 🤙"
                } else {
                    binding.totalCallsMessageTextView.text = "You made no calls that day 🤷‍♂️"
                }
            }
            
            // Overall call message
            val callMessage = when (data.cognitive_decision) {
                "Excellent" -> "Excellent social interaction through calls! 📞✨"
                "Very Good" -> "Great communication patterns today! 📞"
                "Normal" -> "Social interaction through the device was normal,\nbut try to increase it a bit! 📞"
                "Very Bad" -> "Consider reaching out to friends and family more 📞"
                "Critical" -> "Very limited social interaction, try to connect with others 📞"
                else -> "Social interaction data analyzed successfully ✅\nKeep it up!"
            }
            binding.overallCallMessageTextView.text = callMessage
            
        } ?: run {
            // Show no data message for call data
            updateCardWithNoData(binding.cardCallData, "Social Interaction", "The system does not know you yet!!\nKeep living!")
        }
    }

    /**
     * Format timestamp for display (extract time portion)
     */
    private fun formatTimestamp(timestamp: String): String {    
        return try {
            // Assuming timestamp is in format "YYYY-MM-DD HH:MM:SS" or similar
            if (timestamp.contains(" ")) {
                val timePart = timestamp.split(" ")[1]
                if (timePart.contains(":")) {
                    val parts = timePart.split(":")
                    "${parts[0]}:${parts[1]}"
                } else timePart
            } else timestamp
        } catch (e: Exception) {
            timestamp
        }
    }

    private fun createEndAlignedAutoSizingTextView(text: String, ): TextView {
        val context = requireContext()
        val density = resources.displayMetrics.density

        return TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = (5 * density).toInt()
                bottomMargin = (5 * density).toInt()
            }
            this.text = text
            maxLines = 3
            setTextColor(Color.parseColor("#FFFFFF"))
            setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 18f)
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            textAlignment = View.TEXT_ALIGNMENT_TEXT_END
            androidx.core.widget.TextViewCompat.setAutoSizeTextTypeUniformWithConfiguration(
                this,
                12, // min sp
                20, // max sp
                1,  // step sp
                android.util.TypedValue.COMPLEX_UNIT_SP
            )
        }
    }

    /* The following function is responsible
    for loading all components in the xml file
    * that need to be added dynamically */
    private fun loadFragmentView() {
        // TYPING SUMMARY
        val typingSummaryParent = binding.typingSummaryLinearLayout // parent of the LinearLayout for Typing Summary
        for (a in 0 until 10) {
            //TODO: metricTitle and metricValue get them from the DB
            createTypingSummaryComp(typingSummaryParent, "Words Typed", "1000")
        }
        // SLEEP SUMMARY
        val sleepSummaryParent = binding.sleepSummaryLinearLayout // parent of the LinearLayout for Sleep Summary
        createSleepSummaryComp(sleepSummaryParent, "8h 30m", "95% confidence")
        // QUOTE OF THE DAY - Commented out since quoteOfTheDayLinearLayout doesn't exist in current layout
        // val screenSummaryParent = binding.quoteOfTheDayLinearLayout // parent of the LinearLayout for Screen Summary
        // createQuoteOfTheDayComponent(screenSummaryParent, ""Who looks outside, dreams; who looks inside, awakes"", "Carl Jung")
        // SCREEN SUMMARY - Commented out since screenTimeLinearLayout doesn't exist in current layout
        // val screenTimeParent = binding.screenTimeLinearLayout // parent of the LinearLayout for Screen Summary
        // createScreenTimeComponent(screenTimeParent, "5h 30m", "Instagram")
        // MOBILITY BRIEF SUMMARY
        val mobilitySummaryParent = binding.mobilityLinearLayout // parent of the LinearLayout for Mobility Summary
        createMobilityComponents(
            mobilitySummaryParent,
            "2h 30m",
            "5km",
            "10 locations",
            "Low" // Low - Medium - High
        )
        // LOW LIGHT EXPOSURE - Commented out since lowLightExposureLinearLayout doesn't exist in current layout
        // val lowLightExposureParent = binding.lowLightExposureLinearLayout // parent of the LinearLayout for Low Light Exposure
        // createTotalTimeInDarkComponent(
        //     lowLightExposureParent,
        //     "1h 30m"
        // )
    }

    /** This function creates a LinearLayout containing metric components (ImageView and TextViews)
     * and adds it to the provided parent LinearLayout. Components that display the metric title and value.
     * @param parent: The LinearLayout to which the metric components will be added.
     * @param metricTitle: The title of the metric to display.
     * @param metricValue: The value of the metric to display.
     */
    private fun createTypingSummaryComp(parent: LinearLayout, metricTitle: String, metricValue: String) {
        val context = requireContext()

        // Create the outer LinearLayout
        val metricLayout = LinearLayout(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            ).apply {
                marginEnd = (5 * resources.displayMetrics.density).toInt()
            }
            gravity = android.view.Gravity.CENTER
            orientation = LinearLayout.VERTICAL
            setPadding(10, 10, 10, 10)
            setBackgroundResource(R.drawable.border_background)
        }

        // Create the ImageView
        val imageView = ImageView(context).apply {
            layoutParams = LinearLayout.LayoutParams(70, 70)
            setImageResource(R.drawable.profile_pic_big_150)
            contentDescription = "Profile Image"
        }

        // Create the first TextView (metric title)
        val titleTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = metricTitle
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 15f
            typeface = resources.getFont(R.font.montserrat_light)
        }

        // Create the second TextView (metric value)
        val valueTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = metricValue
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
        }

        // Add views to the outer LinearLayout
        metricLayout.addView(imageView)
        metricLayout.addView(titleTextView)
        metricLayout.addView(valueTextView)

        // Add the outer LinearLayout to the parent layout
        parent.addView(metricLayout)
    }

    private fun createSleepSummaryComp(parent: LinearLayout, duration: String, confidence: String) {
        val context = requireContext()

        // Create the inner LinearLayout
        val innerLayout = LinearLayout(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            orientation = LinearLayout.VERTICAL
        }

        // Create the description TextView
        val descriptionTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "Last Sleep duration"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        // Create the duration TextView
        val durationTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = duration
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        // Create the confidence TextView
        val confidenceTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = confidence
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 13f
            typeface = resources.getFont(R.font.montserrat_extralightitalic)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        // Add views to the inner LinearLayout
        innerLayout.addView(descriptionTextView)
        innerLayout.addView(durationTextView)
        innerLayout.addView(confidenceTextView)

        // Add views to the outer LinearLayout
        parent.addView(innerLayout)
    }

    private fun createQuoteOfTheDayComponent(parent: LinearLayout, message: String, writer: String) {
        val context = requireContext()

        val quoteTextView = TextView(context).apply {
            id = View.generateViewId()
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = (5 * resources.displayMetrics.density).toInt()
            }
            typeface = ResourcesCompat.getFont(context, R.font.montserrat_bold)
            gravity = Gravity.CENTER
            setLineSpacing(8f * resources.displayMetrics.density, 1.0f)
            text = message
            textAlignment = View.TEXT_ALIGNMENT_CENTER
            setTextColor(ContextCompat.getColor(context, R.color.white_in_card))
            textSize = 25f
        }

        val quoteWriterView = TextView(context).apply {
            id = View.generateViewId()
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT
            ).apply {
                topMargin = (5 * resources.displayMetrics.density).toInt()
            }
            typeface = ResourcesCompat.getFont(context, R.font.montserrat_light)
            gravity = Gravity.CENTER
            text = "- $writer"
            textAlignment = View.TEXT_ALIGNMENT_CENTER
            setTextColor(ContextCompat.getColor(context, R.color.white_in_card))
            textSize = 15f
        }

        parent.addView(quoteTextView)
        parent.addView(quoteWriterView)
    }

    private fun createScreenTimeComponent(parent: LinearLayout, totalScreenTime: String, mostUsedAppName: String) {
        val context = requireContext()

        val descriptionTextView_1 = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "Total Screen On Time"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        val totalScreenTimeTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = totalScreenTime
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        val descriptionTextView_2 = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "Favourite App"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        val favouriteAppTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = mostUsedAppName
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        parent.addView(descriptionTextView_1)
        parent.addView(totalScreenTimeTextView)
        parent.addView(descriptionTextView_2)
        parent.addView(favouriteAppTextView)
    }

    private fun createMobilityComponents(
        parent: LinearLayout,
        totalInHomeTime: String,
        totalDistanceTravel: String,
        locationDiversity: String,
        warderingBehavior: String
    ) {
        val context = requireContext()

        // Create in home time
        val descriptionTextView_1 = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "In-home time"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_START
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        val totalInHomeTimeTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = totalInHomeTime
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_START
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        // Create total distance travel
        val descriptionTextView_2 = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "Total distance travel"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_END
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        val totalDistanceTravelTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = totalDistanceTravel
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_END
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        // Create location diversity
        val descriptionTextView_3 = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "Location diversity"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_START
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        val locationDiversityTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = locationDiversity
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_START
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        // Create wardering behavior
        val descriptionTextView_4 = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "Wandering behavior"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_END
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        val warderingBehaviorTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = warderingBehavior
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_END
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        // Add all views to the parent layout
        parent.addView(descriptionTextView_1)
        parent.addView(totalInHomeTimeTextView)
        //
        parent.addView(createLineSeparation(context))
        //
        parent.addView(descriptionTextView_2)
        parent.addView(totalDistanceTravelTextView)
        //
        parent.addView(createLineSeparation(context))
        //
        parent.addView(descriptionTextView_3)
        parent.addView(locationDiversityTextView)
        //
        parent.addView(createLineSeparation(context))
        //
        parent.addView(descriptionTextView_4)
        parent.addView(warderingBehaviorTextView)
    }

    private fun createTotalTimeInDarkComponent(parent: LinearLayout, totalTimeInDark: String) {
        val context: Context = requireContext()

        val descriptionTextView_1 = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = "Time in Dark Environments"
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_START
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_light)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        val totalTimeInDarkTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            text = totalTimeInDark
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textAlignment = View.TEXT_ALIGNMENT_TEXT_START
            textSize = 25f
            typeface = resources.getFont(R.font.montserrat_bold)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        parent.addView(descriptionTextView_1)
        parent.addView(totalTimeInDarkTextView)
    }

    // Function to create a new line separation view
    fun createLineSeparation(context: Context): View {
        return View(context).apply {
            id = View.generateViewId()
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                (1 * resources.displayMetrics.density).toInt()
            ).apply {
                topMargin = (20 * resources.displayMetrics.density).toInt()
                bottomMargin = (20 * resources.displayMetrics.density).toInt()
            }
            setBackgroundColor(android.graphics.Color.parseColor("#BBBBBB"))
        }
    }

}