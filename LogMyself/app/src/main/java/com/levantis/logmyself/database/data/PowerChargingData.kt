package com.levantis.logmyself.database.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "power_charging_data")
class PowerChargingData (
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val startTime: LocalDateTime,
    val endTime: LocalDateTime
)