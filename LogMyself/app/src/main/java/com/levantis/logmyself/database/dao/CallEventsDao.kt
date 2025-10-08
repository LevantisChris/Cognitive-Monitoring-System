package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.CallEventsData

@Dao
interface CallEventsDao {

    @Insert
    suspend fun insertCallEvent(callEvent: CallEventsData)

}