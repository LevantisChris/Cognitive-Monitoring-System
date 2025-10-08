package com.levantis.logmyself.database.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "call_events_data")
class CallEventsData(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val callType: Int?,
    val callDescription: String?,
    val callDuration: Int?,
    val callDate: LocalDateTime,
)