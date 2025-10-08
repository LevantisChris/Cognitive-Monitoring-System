package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.UserActivitiesData

@Dao
interface UserActivitiesDao {
    @Insert
    suspend fun insertUserActivitiesData(userActivitiesData: UserActivitiesData)
}