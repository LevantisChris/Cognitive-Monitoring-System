package com.levantis.logmyself.database.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "device_unlocks")
data class DeviceUnlocksData(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val timestamp: LocalDateTime
)
