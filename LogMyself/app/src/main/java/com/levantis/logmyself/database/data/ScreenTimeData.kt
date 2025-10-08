package com.levantis.logmyself.database.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "screen_time_data")
data class ScreenTimeData(
    @PrimaryKey(autoGenerate = true)
    @ColumnInfo(name = "id")
    var id: Int = 0,
    @ColumnInfo(name = "time_start")
    var timeStart: LocalDateTime,
    @ColumnInfo(name = "time_end")
    var timeEnd: LocalDateTime,
    @ColumnInfo(name = "duration")
    var duration: Long,
)
