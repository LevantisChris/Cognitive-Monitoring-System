package com.levantis.logmyself.database.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "low_light_exposures")
data class LowLightExpoDetectorData(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val startTime: LocalDateTime,
    val endTime: LocalDateTime,
    val duration: Long,
    val validStartTime: Long,
    val validEndTime: Long,
    val lowLightThreshold: Float
)
