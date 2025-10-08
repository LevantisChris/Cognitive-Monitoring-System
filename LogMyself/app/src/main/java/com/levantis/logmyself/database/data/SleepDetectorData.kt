package com.levantis.logmyself.database.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "sleep_events")
data class SleepDetectorData(
    @PrimaryKey(autoGenerate = true)
    @ColumnInfo(name = "id")
    val id: Int = 0,
    val confidence: Int,
    val light: Int,
    val motion: Int,
    val timestampNow: LocalDateTime,
    val timestampPrevious: LocalDateTime,
    val screenOnDuration: Long,
)
