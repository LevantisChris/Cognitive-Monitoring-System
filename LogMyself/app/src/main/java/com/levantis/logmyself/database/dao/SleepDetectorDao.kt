package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.SleepDetectorData

@Dao
interface SleepDetectorDao {

    @Insert
    suspend fun insertSleepData(sleepData: SleepDetectorData): Long

}