package com.levantis.logmyself.ui.typing

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import com.levantis.logmyself.R
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color.Companion.Green
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.unit.dp
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.github.mikephil.charting.charts.BubbleChart
import com.github.mikephil.charting.charts.ScatterChart
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.BubbleData
import com.github.mikephil.charting.data.BubbleDataSet
import com.github.mikephil.charting.data.BubbleEntry
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.ScatterData
import com.github.mikephil.charting.data.ScatterDataSet
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter
import com.levantis.logmyself.databinding.FragmentTypingBinding
import com.levantis.logmyself.ui.charts.IntensityGraphView.IntensityDataPoint
import com.levantis.logmyself.ui.charts.PressureBubbleChartView
import com.levantis.logmyself.ui.charts.rememberMarker
import com.patrykandpatrick.vico.compose.axis.horizontal.rememberBottomAxis
import com.patrykandpatrick.vico.compose.chart.Chart
import com.patrykandpatrick.vico.compose.chart.line.lineChart
import com.patrykandpatrick.vico.compose.chart.scroll.rememberChartScrollState
import com.patrykandpatrick.vico.compose.component.shape.shader.fromBrush
import com.patrykandpatrick.vico.compose.style.ProvideChartStyle
import com.patrykandpatrick.vico.core.chart.line.LineChart
import com.patrykandpatrick.vico.core.component.shape.shader.DynamicShaders
import com.patrykandpatrick.vico.core.entry.ChartEntryModelProducer
import com.patrykandpatrick.vico.core.entry.FloatEntry
import java.time.LocalDate
import java.time.LocalDateTime
import kotlin.random.Random
import androidx.core.graphics.toColorInt
import androidx.core.view.marginBottom
import com.github.mikephil.charting.charts.RadarChart
import com.github.mikephil.charting.data.RadarDataSet
import com.github.mikephil.charting.data.RadarEntry
import com.levantis.logmyself.ui.charts.IntensityGraphView
import com.patrykandpatrick.vico.compose.axis.vertical.rememberStartAxis
import com.patrykandpatrick.vico.core.axis.AxisItemPlacer


class TypingFragment : Fragment() {

    private var _binding: FragmentTypingBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val typingViewModel =
            ViewModelProvider(this).get(TypingViewModel::class.java)

        _binding = FragmentTypingBinding.inflate(inflater, container, false)
        val root: View = binding.root

        return root
    }

    /** Functions to check if LogBoard is installed in the device
    * @param context The context of the application
    * @param packageName The package name of the app to check
    *  */
//    fun isAppInstalled(context: Context, packageName: String): Boolean {
//        return try {
//            context.packageManager.getPackageInfo(packageName, PackageManager.GET_ACTIVITIES)
//            true
//        } catch (e: PackageManager.NameNotFoundException) {
//            false
//        }
//    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        // loadFragmentsViews()
    }

    /* The following function is responsible
    for loading all components in the xml file
    * that need to be added dynamically */
    private fun loadFragmentsViews() {
        // Today stats chart
        val todaySParent = binding.todayBasicMetricsLinearLayout
        createTodayStatsComp(todaySParent, "15", "Words/second", "5", "Chars/second", "10", "Backspace Bursts", "2.3", "Average IKI")
        // Pressure per typing session - bubble chart
        val pressureChartParent = binding.bubbleGraphChartViewLinearLayout
        createPressureBubbleChartView(pressureChartParent)
        // Line Chart with Vico - Show trends over time for typing speed
        //var lineChartView = binding.chartView
        var lineChartParent = binding.linearChartSecWordSecondLinearLayout
        createLineChartView(lineChartParent)
        // Keyboard Usage chart with metrics over sectors of the day
        var parentLinearLayout = binding.keyboardUseLinearLayout
        var radarChart = binding.radarChart
        createRadarChart(radarChart)
        // TODO: Stats only for the two most popular day sectors.
        createMetricsOverSectorsOfDay( // Morning
            parentLinearLayout,
            "Morning Typing Stats",
            listOf(
                Pair("Character per second", "2.3 chars"),
                Pair("Words per second", "1.5 words"),
                Pair("Average IKI", "5.3 sec"),
                Pair("Average words per session", "85 words"),
                Pair("Average backspaces per session", "15 backspaces")
            )
        )
        createMetricsOverSectorsOfDay( // Night
            parentLinearLayout,
            "Night Typing Stats",
            listOf(
                Pair("Character per second", "2.3 chars"),
                Pair("Words per second", "1.5 words"),
                Pair("Average IKI", "5.3 sec"),
                Pair("Average words per session", "85 words"),
                Pair("Average backspaces per session", "15 backspaces")
            )
        )
        // Efficiency chart
        // TODO: Load data from the database for the last 300 sessions
        var efficiencyChartParent = binding.efficiencyLinearLayout
        createLineChartView(efficiencyChartParent)
        // Activity volume
        var activityVolumeParent = binding.activityVolumeLinearLayout
        createLineChartView(activityVolumeParent)

    }

    private fun createMetricsOverSectorsOfDay(parent: LinearLayout, title: String, metrics: List<Pair<String, String>>) {
        val context = requireContext()

        // Create the outer TextView title
        val titleTextView = TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ) .apply {
                bottomMargin = (15 * resources.displayMetrics.density).toInt()
            }
            text = title
            setTextColor(resources.getColor(R.color.white_in_card, null))
            textSize = 15f
            typeface = resources.getFont(R.font.montserrat_light)
        }

        // Create the outer HorizontalScrollView and also the outer LinearLayout that the metric squares will be added
        val scrollView = HorizontalScrollView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            isHorizontalScrollBarEnabled = false
        }
        val horizontalLinearLayout = LinearLayout(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            orientation = LinearLayout.HORIZONTAL
        }

        // For every metric pair in List, create a metric square
        for (metric in metrics) {
            val metricTitle = metric.first
            val metricValue = metric.second
            createMetricSquare(horizontalLinearLayout, metricTitle, metricValue)
        }

        // Add the components in the view
        parent.addView(createLineSeparation(context))
        parent.addView(titleTextView)
        scrollView.addView(horizontalLinearLayout)
        parent.addView(scrollView)
    }

    /**
     * This function is responsible for creating a metric square component.
     * @param: parent is the linear layout the component will be added
     * @param: metricTitle is the title of the metric
     * @param: metricValue is the value of the metric
     */
    private fun createMetricSquare(parent: LinearLayout, metricTitle: String, metricValue: String) {
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
            textSize = 12f
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
            textSize = 18f
            typeface = resources.getFont(R.font.montserrat_bold)
        }

        // Add views to the outer LinearLayout
        metricLayout.addView(imageView)
        metricLayout.addView(titleTextView)
        metricLayout.addView(valueTextView)

        // Add the outer LinearLayout to the parent layout
        parent.addView(metricLayout)
    }

    /**
     * Radar chart that will show the typing activity over the sectors of a day.
     * Here we create all the chart.
     * @param: chart is the radar chart that will be created
     * @param: dataValues, percentage of use calculated for each sector of the day
     * */
    private fun createRadarChart(chart: RadarChart, percentageUsage: List<Float> = emptyList()) {
        // Labels for the sectors of the day
        val labels = listOf("Morning", "Afternoon", "Night", "Evening")

        // Define data values for each sector
        // TODO: Calculate the values based on the user's typing activity in the sectors of the day
        // (percentageUsage) == dataValues
        val dataValues = listOf(50f, 20f, 10f, 20f) // Example values: each corresponds to a sector (think of it as a percentage of the day)

        // Create RadarEntries
        val entries = dataValues.mapIndexed { index, value ->
            com.github.mikephil.charting.data.RadarEntry(value)
        }

        // Create a RadarDataSet
        val dataSet = com.github.mikephil.charting.data.RadarDataSet(entries, "Daily Activity").apply {
            color = Color.GREEN
            fillColor = Color.GREEN
            setDrawFilled(true)
            lineWidth = 2f
            setDrawValues(false)
        }

        // Create RadarData
        val radarData = com.github.mikephil.charting.data.RadarData(dataSet).apply {
            setValueTextColor(Color.WHITE)
            setValueTextSize(12f)
        }

        chart.apply {
            data = radarData
            description.isEnabled = false
            webColor = Color.LTGRAY
            webColorInner = Color.LTGRAY
            webLineWidth = 1f
            webLineWidthInner = 1f
            webAlpha = 100

            xAxis.apply {
                valueFormatter = IndexAxisValueFormatter(labels)
                textColor = Color.WHITE
                textSize = 12f
            }

            yAxis.apply {
                axisMinimum = 0f
                setDrawLabels(false) // Hide the numbers
                textColor = Color.TRANSPARENT // Ensure numbers are not visible
            }

            legend.apply {
                textColor = Color.WHITE
                textSize = 14f
            }

            isRotationEnabled = false // Disable orientation changes

            animateXY(1000, 1000)

            invalidate()
        }
    }

    /**
     * This function is responsible for creating the components
     * inside the parent linear layout of the today stats
     * @param:
     * */
    private fun createTodayStatsComp(
        parent: LinearLayout,
        topLeftValue: String,
        topLeftDescription: String,
        topRightValue: String,
        topRightDescription: String,
        bottomLeftValue: String,
        bottomLeftDescription: String,
        bottomRightValue: String,
        bottomRightDescription: String
    ) {
        // Create top row
        createHorizontalTextViewRow(parent, topLeftValue, topLeftDescription, topRightValue, topRightDescription)
        // Create bottom row
        createHorizontalTextViewRow(parent, bottomLeftValue, bottomLeftDescription, bottomRightValue, bottomRightDescription)
    }

    private fun createHorizontalTextViewRow(
        parent: LinearLayout,
        leftText: String,
        leftDescription: String,
        rightText: String,
        rightDescription: String
    ) {
        val context = requireContext()

        val rowLayout = LinearLayout(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = (5 * resources.displayMetrics.density).toInt()
            }
            orientation = LinearLayout.HORIZONTAL
        }

        rowLayout.addView(createTextViewContainer(leftText, leftDescription))
        rowLayout.addView(createTextViewContainer(rightText, rightDescription))
        parent.addView(rowLayout)
    }

    private fun createTextViewContainer(valueStr: String, descriptionStr: String): LinearLayout {
        val leftTextViewContainer = LinearLayout(context).apply {
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT).apply {
                weight = 1f
                marginEnd = (5 * resources.displayMetrics.density).toInt()
            }
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(resources.getColor(R.color.main_200, null))

            val valueTextView = TextView(context).apply {
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                text = valueStr
                gravity = Gravity.CENTER
                setTextColor(Color.WHITE)
                textSize = 25f
                setTypeface(typeface, Typeface.BOLD)
                typeface = resources.getFont(R.font.montserrat_medium)
            }

            val descriptionTextView = TextView(context).apply {
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                text = descriptionStr
                gravity = Gravity.CENTER
                setTextColor(Color.WHITE)
                textSize = 12f
                typeface = resources.getFont(R.font.montserrat_light)
            }

            addView(valueTextView)
            addView(descriptionTextView)
        }
        return leftTextViewContainer
    }

    /**
     * Function to add the Bubble Graph dynamically in the code
     * @param: parent is the linear layout the component will be added
     * @param: is a list of the values, index, pressure applied in typing session as a Pair */
    private fun createPressureBubbleChartView(parent: LinearLayout, listOfValues: List<Pair<Int, Float>> = emptyList()) {
        val context = requireContext()

        val pressureChartView = PressureBubbleChartView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                (400 * resources.displayMetrics.density).toInt() // Convert dp to pixels
            )
        }

        pressureChartView.pressureData = List(24*24) { dayIndex ->
            Pair(
                dayIndex,
                (0..100).random() / 100f // Random PressureValue (0.0f to 1.0f)
            )
        }

        parent.addView(pressureChartView)
    }

    /**
     * Create the line chart using Vico library.
     * @param: parent is the linear layout the component will be added
     * */
    private fun createLineChartView(parent: LinearLayout) {
        val context = requireContext()
        val composeView = ComposeView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            setContent {
                val modelProducer = remember { ChartEntryModelProducer() }
                val datasetForModel = remember { mutableStateListOf(listOf<FloatEntry>()) }
                val datasetLineSpec = remember { arrayListOf<LineChart.LineSpec>() }
                val scrollState = rememberChartScrollState()

                datasetForModel.clear()
                datasetLineSpec.clear()
                var xPos = 0f
                var dataPoints = arrayListOf<FloatEntry>()
                datasetLineSpec.add(
                    LineChart.LineSpec(
                        lineColor = Green.toArgb(),
                        lineBackgroundShader = DynamicShaders.fromBrush(
                            brush = Brush.verticalGradient(
                                listOf(
                                    Green.copy(alpha = 0.1f),
                                    Green.copy(alpha = 0.5f),
                                )
                            )
                        )
                    )
                )
                for (i in 1..150) {
                    val randomFloat = (1..150).random().toFloat()
                    dataPoints.add(FloatEntry(x = xPos, y = randomFloat))
                    xPos += 1f
                }
                datasetForModel.add(dataPoints)
                modelProducer.setEntries(datasetForModel)

                val marker = rememberMarker()

                ProvideChartStyle {
                    Chart(
                        chart = lineChart(
                            lines = datasetLineSpec
                        ),
                        chartModelProducer = modelProducer,
                        startAxis = rememberStartAxis(
                            title = "Testing start Axis",
                            tickLength = 0.dp,
                            valueFormatter = {
                                value, _ ->
                                value.toInt().toString()
                            },
                            itemPlacer = AxisItemPlacer.Vertical.default(
                                maxItemCount = 8
                            ),
                        ),
                        bottomAxis = rememberBottomAxis(
                            title = "Testing bottom Axis",
                            tickLength = 0.dp,
                            valueFormatter = {
                                    value, _ ->
                                ((value.toInt()) + 1).toString()
                            },
                            guideline = null,
                        ),
                        marker = marker,
                        chartScrollState = scrollState,
                        isZoomEnabled = true,
                    )
                }
            }
        }
        parent.addView(composeView)
    }

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