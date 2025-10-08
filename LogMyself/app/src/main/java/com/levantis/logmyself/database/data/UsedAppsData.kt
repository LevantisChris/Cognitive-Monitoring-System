package com.levantis.logmyself.database.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(
    tableName = "used_apps",
    foreignKeys = [
        androidx.room.ForeignKey(
            entity = SleepDetectorData::class,
            parentColumns = ["id"],
            childColumns = ["sleepEventId"],
            onDelete = androidx.room.ForeignKey.CASCADE
        )
    ]
)
data class UsedAppsData (
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    @ColumnInfo(name = "sleepEventId")
    val sleepEventId: Int,
    val appName: String,
    val usageDuration: Long
)