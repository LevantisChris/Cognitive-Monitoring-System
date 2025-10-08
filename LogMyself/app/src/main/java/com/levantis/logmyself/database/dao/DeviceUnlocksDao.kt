package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.DeviceUnlocksData

@Dao
interface DeviceUnlocksDao {

    @Insert
    suspend fun insertDeviceUnlocksData(deviceUnlocksData: DeviceUnlocksData)

}