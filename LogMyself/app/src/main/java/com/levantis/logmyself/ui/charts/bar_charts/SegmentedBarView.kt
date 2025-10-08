package com.levantis.logmyself.ui.charts.bar_charts

import android.R
import android.content.Context
import android.graphics.Typeface
import android.util.AttributeSet
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat


data class SegmentCategory(
    val label: String,
    val percent: Float,      // value 0.0 - 1.0
    val colorInt: Int,       // raw ARGB color int (e.g., Color.parseColor("#FFCC33"))
    val textColorRes: Int? = R.color.white
)

class SegmentedBarView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : LinearLayout(context, attrs) {

    private val container: LinearLayout = LinearLayout(context).apply {
        orientation = HORIZONTAL
        layoutParams = LayoutParams(
            LayoutParams.MATCH_PARENT,
            60  // bar height (you can make it attr later)
        )
        weightSum = 1f
        clipToOutline = true // for rounded corners if background is shaped
    }

    init {
        orientation = VERTICAL
        addView(container)
    }

    fun setCategories(categories: List<SegmentCategory>) {
        container.removeAllViews()

        val total = categories.sumOf { it.percent.toDouble() }.toFloat()
        val safeTotal = if (total > 0f) total else 1f

        for (cat in categories) {
            val weight = cat.percent / safeTotal

            val segment = FrameLayout(context).apply {
                layoutParams = LayoutParams(0, LayoutParams.MATCH_PARENT, weight)
                setBackgroundColor(cat.colorInt)

                val label = TextView(context).apply {
                    text = "${cat.label} ${(weight * 100).toInt()}%"
                    setTextColor(ContextCompat.getColor(context, cat.textColorRes!!))
                    textSize = 12f
                    setTypeface(typeface, Typeface.BOLD)
                    gravity = Gravity.CENTER
                }

                addView(label, FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    Gravity.CENTER
                ))
            }

            container.addView(segment)
        }
    }
}
