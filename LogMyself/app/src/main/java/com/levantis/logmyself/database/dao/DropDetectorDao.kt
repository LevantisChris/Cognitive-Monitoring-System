package com.levantis.logmyself.database.dao

import androidx.room.Dao
import androidx.room.Insert
import com.levantis.logmyself.database.data.DropDetectorData

@Dao
interface DropDetectorDao {

    @Insert
    suspend fun insertDropData(dropData: DropDetectorData)

}