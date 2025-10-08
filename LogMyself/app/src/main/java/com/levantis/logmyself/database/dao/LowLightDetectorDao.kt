package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.LowLightExpoDetectorData

@Dao
interface LowLightDetectorDao {

    @Insert
    suspend fun insertLowLightData(lowLightData: LowLightExpoDetectorData)

}