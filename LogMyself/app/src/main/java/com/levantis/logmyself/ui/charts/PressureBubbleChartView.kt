package com.levantis.logmyself.ui.charts

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View

class PressureBubbleChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)

    // Each entry: Pair<DayIndex (0-29), PressureValue (0f - 1f)>
    var pressureData: List<Pair<Int, Float>> = emptyList()
        set(value) {
            field = value
            invalidate()
        }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (pressureData.isEmpty()) return

        val columns = 24
        val rows = 24
        val maxRadius = minOf(width / (columns * 2f), height / (rows * 2f)) * 0.9f
        val cellWidth = width / columns.toFloat()
        val cellHeight = height / rows.toFloat()

        pressureData.forEach { (dayIndex, pressureValue) ->
            if (dayIndex >= (24*24)) return@forEach

            val row = dayIndex / columns
            val col = dayIndex % columns

            val centerX = col * cellWidth + cellWidth / 2
            val centerY = row * cellHeight + cellHeight / 2

            val radius = pressureToRadius(pressureValue, maxRadius)
            paint.color = pressureToColor(pressureValue)

            canvas.drawCircle(centerX, centerY, radius, paint)
        }
    }

    private fun pressureToRadius(pressure: Float, maxRadius: Float): Float {
        val normalized = pressure.coerceIn(0f, 1f)
        return normalized * maxRadius
    }

    private fun pressureToColor(pressure: Float): Int {
        val normalized = pressure.coerceIn(0f, 1f)
        val hue = 260f - (normalized * 260f)  // 260° (purple) to 60° (yellow)
        return Color.HSVToColor(floatArrayOf(hue, 1f, 1f))
    }
}

