package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import com.levantis.logmyself.database.data.ScreenTimeData

@Dao
interface ScreenTimeDao {
    @Insert
    suspend fun insertScreenTimeData(screenTimeData: ScreenTimeData)
}