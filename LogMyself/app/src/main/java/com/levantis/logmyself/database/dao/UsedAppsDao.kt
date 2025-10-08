package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.UsedAppsData

@Dao
interface UsedAppsDao {
    @Insert
    suspend fun insertUsedApps(usedApps: List<UsedAppsData>)
}