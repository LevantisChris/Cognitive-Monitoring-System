package com.levantis.logmyself.analysis_database.data_classes

import kotlinx.serialization.Serializable

@Serializable
data class BaselineMetrics(
    val metric_name: String,
    val baseline_mean: Double,
    val baseline_std: Double,
    val baseline_median: Double,
    val baseline_mad: Double
)
