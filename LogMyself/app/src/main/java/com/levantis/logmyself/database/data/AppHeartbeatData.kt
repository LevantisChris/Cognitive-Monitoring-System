package com.levantis.logmyself.database.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "app_heartbeat_logs")
class AppHeartbeatData (
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val timestamp: LocalDateTime,
    val status: Boolean // alive: true, dead: false
)