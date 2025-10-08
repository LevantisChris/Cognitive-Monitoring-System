package com.levantis.logmyself.database.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "user_activities")
data class UserActivitiesData(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val activityType: String,
    val confidence: Int,
    val timestamp: LocalDateTime,
//    val transitionType: String
)
