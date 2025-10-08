package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.AppHeartbeatData

@Dao
interface AppHeartbeatDao {
    @Insert
    suspend fun insertAppHeartbeat(heartbeat: AppHeartbeatData)
}