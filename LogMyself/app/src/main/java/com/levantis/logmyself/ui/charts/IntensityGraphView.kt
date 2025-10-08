package com.levantis.logmyself.ui.charts

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.util.AttributeSet
import android.view.View
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import kotlin.math.max
import kotlin.math.roundToInt
import androidx.core.graphics.toColorInt
import java.time.LocalDateTime
import java.time.LocalTime

class IntensityGraphView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    // --- Configuration ---
    private val daysToShow = 15 // Minimum number of days to show
    private var dayHeight = 150f // Height allocated for each day row
    private val verticalPadding = 40f
    private val horizontalPadding = 30f
    private val yAxisLabelWidth = 180f // Space for date labels on the left
    private val xAxisLabelHeight = 60f // Space for sector labels at the bottom
    private val pointRadius = 15f
    private val gridStrokeWidth = 1f
    private val axisLabelTextSize = 35f

    // --- Data ---
    private var dataPoints: List<IntensityDataPoint> = emptyList()
    private var groupedData: Map<LocalDate, List<IntensityDataPoint>> = emptyMap()
    private var sortedDates: List<LocalDate> = emptyList()

    // --- Drawing ---
    private val gridPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.LTGRAY
        style = Paint.Style.STROKE
        strokeWidth = gridStrokeWidth
    }

    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.BLACK
        textSize = axisLabelTextSize
        textAlign = Paint.Align.CENTER
    }

    private val pointPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }

    private val textBounds = Rect() // For measuring text height
    private val dateFormatter = DateTimeFormatter.ofPattern("MMM dd") // e.g., Apr 26

    // --- Scrolling ---
    private var scrollOffset = 0

    fun setData(points: List<IntensityDataPoint>) {
        dataPoints = points
        // Group points by date and sort dates descending (most recent first)
        groupedData = points.groupBy { it.dateTime.toLocalDate() }
        sortedDates = groupedData.keys.sortedDescending()
        requestLayout() // Recalculate dimensions
        invalidate() // Redraw
    }

    // Called by the Activity/Fragment when the ScrollView scrolls
    fun setScrollOffset(offset: Int) {
        if (offset != scrollOffset) {
            scrollOffset = offset
            invalidate() // Trigger redraw with new visible area
        }
    }

    // --- Intensity to Color Mapping ---
    private fun mapIntensityToColor(intensity: Int): Int {
        // Example: Simple threshold mapping (adjust as needed)
        return when {
            intensity < 5 -> "#AEEEEE".toColorInt() // Pale Turquoise
            intensity < 10 -> "#40E0D0".toColorInt() // Turquoise
            intensity < 20 -> "#FFD700".toColorInt() // Gold
            intensity < 40 -> "#FFA500".toColorInt() // Orange
            else -> "#FF4500".toColorInt() // OrangeRed
        }
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val desiredWidth = MeasureSpec.getSize(widthMeasureSpec) // Use available width

        // Calc desired height based on number of days or minimum days
        val numDays = max(sortedDates.size, daysToShow)
        val desiredHeight = (numDays * dayHeight + 2 * verticalPadding + xAxisLabelHeight).roundToInt()

        // Set the calculated dimensions for the view.
        // This view will be larger than the screen if numDays * dayHeight is large.
        setMeasuredDimension(desiredWidth, desiredHeight)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        if (sortedDates.isEmpty()) return // Nothing to draw

        // Calculate drawing area dimensions
        val viewWidth = width.toFloat()
        // val viewHeight = height.toFloat() // Total height of the view

        val graphContentWidth = viewWidth - 2 * horizontalPadding - yAxisLabelWidth
        val sectorWidth = graphContentWidth / TimeSectorsInOrder.size
        val graphStartX = horizontalPadding + yAxisLabelWidth

        // Get visible area bounds (clipBounds accounts for scrolling within ScrollView)
        val visibleRect = Rect()
        canvas.getClipBounds(visibleRect)
        // val visibleTop = visibleRect.top // scrollOffset should be equivalent
        // val visibleBottom = visibleRect.bottom

        // --- 1. Draw X-axis Labels (Sectors) ---
        val xAxisY = height - verticalPadding - (xAxisLabelHeight / 2) // Center vertically in the bottom space
        if (xAxisY > visibleRect.top && xAxisY < visibleRect.bottom) { // Draw only if visible
            TimeSectorsInOrder.forEachIndexed { index, sector ->
                val labelX = graphStartX + index * sectorWidth + sectorWidth / 2
                canvas.drawText(sector.name.lowercase().replaceFirstChar { it.titlecase() }, labelX, xAxisY + textBounds.height() / 2, textPaint)
            }
        }

        // --- 2. Draw Grid & Y-axis Labels (Dates) ---
        sortedDates.forEachIndexed { index, date ->
            val dayRowY = verticalPadding + index * dayHeight // Top of the day row

            // Optimization: Only draw if the row is potentially visible
            if (dayRowY + dayHeight >= visibleRect.top && dayRowY <= visibleRect.bottom) {

                // Draw Horizontal Grid Line (separator between days)
                canvas.drawLine(
                    graphStartX,
                    dayRowY,
                    viewWidth - horizontalPadding,
                    dayRowY,
                    gridPaint
                )

                // Draw Y-axis Label (Date) - centered vertically in the row
                val dateLabelY = dayRowY + dayHeight / 2 + textBounds.height() / 2
                val dateText = date.format(dateFormatter)
                textPaint.textAlign = Paint.Align.RIGHT // Align date to the right edge of label area
                canvas.drawText(
                    dateText,
                    horizontalPadding + yAxisLabelWidth - 10f, // 10f padding from grid line
                    dateLabelY,
                    textPaint
                )
            }
        }
        // Draw final horizontal line at the bottom if needed
        val finalLineY = verticalPadding + sortedDates.size * dayHeight
        if(finalLineY >= visibleRect.top && finalLineY <= visibleRect.bottom) {
            canvas.drawLine(graphStartX, finalLineY, viewWidth - horizontalPadding, finalLineY, gridPaint)
        }


        // --- 3. Draw Vertical Grid Lines (Sector Separators) ---
        textPaint.textAlign = Paint.Align.CENTER // Reset alignment for points
        TimeSectorsInOrder.indices.forEach { index ->
            val lineX = graphStartX + index * sectorWidth
            // Draw vertical line from top padding to start of x-axis labels
            canvas.drawLine(lineX, verticalPadding, lineX, height - verticalPadding - xAxisLabelHeight, gridPaint)
        }
        // Draw last vertical line on the right edge
        val lastLineX = graphStartX + TimeSectorsInOrder.size * sectorWidth
        canvas.drawLine(lastLineX, verticalPadding, lastLineX, height - verticalPadding - xAxisLabelHeight, gridPaint)


        // --- 4. Draw Data Points ---
        sortedDates.forEachIndexed { dateIndex, date ->
            val dayRowY = verticalPadding + dateIndex * dayHeight
            val pointCenterY = dayRowY + dayHeight / 2

            // Optimization: Only process points for potentially visible rows
            if (dayRowY + dayHeight >= visibleRect.top && dayRowY <= visibleRect.bottom) {
                groupedData[date]?.forEach { point ->
                    val sector = mapTimeToSector(point.dateTime.toLocalTime())
                    val sectorIndex = TimeSectorsInOrder.indexOf(sector)

                    if (sectorIndex != -1) { // Should always be found
                        val pointCenterX = graphStartX + sectorIndex * sectorWidth + sectorWidth / 2

                        pointPaint.color = mapIntensityToColor(point.intensity)
                        canvas.drawCircle(pointCenterX, pointCenterY, pointRadius, pointPaint)
                    }
                }
            }
        }

        // Measure text height once (approximation is okay here)
        textPaint.getTextBounds("Test", 0, 4, textBounds)
    }

    enum class TimeSector {
        NIGHT, // 00:00 - 05:59
        MORNING, // 06:00 - 11:59
        AFTERNOON, // 12:00 - 17:59
        EVENING // 18:00 - 23:59
    }

    fun mapTimeToSector(time: LocalTime): TimeSector {
        return when (time.hour) {
            in 0..5 -> TimeSector.NIGHT
            in 6..11 -> TimeSector.MORNING
            in 12..17 -> TimeSector.AFTERNOON
            else -> TimeSector.EVENING // 18..23
        }
    }

    val TimeSectorsInOrder = listOf(
        TimeSector.NIGHT,
        TimeSector.MORNING,
        TimeSector.AFTERNOON,
        TimeSector.EVENING
    )

    data class IntensityDataPoint(
        val dateTime: LocalDateTime,
        val intensity: Int // Example: Number of key presses, duration, etc.
    )
}