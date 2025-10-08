package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.PowerChargingData

@Dao
interface PowerChargingDao {
    @Insert
    suspend fun insertPowerPluginsData(lowLightData: PowerChargingData)
}