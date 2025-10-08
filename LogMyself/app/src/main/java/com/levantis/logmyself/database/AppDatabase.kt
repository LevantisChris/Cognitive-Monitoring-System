package com.levantis.logmyself.database

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.levantis.logmyself.database.dao.AppHeartbeatDao
import com.levantis.logmyself.database.dao.CallEventsDao
import com.levantis.logmyself.database.dao.DeviceUnlocksDao
import com.levantis.logmyself.database.dao.DropDetectorDao
import com.levantis.logmyself.database.dao.LowLightDetectorDao
import com.levantis.logmyself.database.dao.PowerChargingDao
import com.levantis.logmyself.database.dao.ScreenTimeDao
import com.levantis.logmyself.database.dao.SleepDetectorDao
import com.levantis.logmyself.database.dao.UsedAppsDao
import com.levantis.logmyself.database.dao.UserActivitiesDao
import com.levantis.logmyself.database.data.AppHeartbeatData
import com.levantis.logmyself.database.data.CallEventsData
import com.levantis.logmyself.database.data.DeviceUnlocksData
import com.levantis.logmyself.database.data.DropDetectorData
import com.levantis.logmyself.database.data.LowLightExpoDetectorData
import com.levantis.logmyself.database.data.PowerChargingData
import com.levantis.logmyself.database.data.ScreenTimeData
import com.levantis.logmyself.database.data.SleepDetectorData
import com.levantis.logmyself.database.data.UsedAppsData
import com.levantis.logmyself.database.data.UserActivitiesData
import com.levantis.logmyself.database.util.Converters

@Database(
    entities = [
        ScreenTimeData::class,
        UsedAppsData::class,
        SleepDetectorData::class,
        DropDetectorData::class,
        LowLightExpoDetectorData::class,
        DeviceUnlocksData::class,
        UserActivitiesData::class,
        AppHeartbeatData::class,
        PowerChargingData::class,
        CallEventsData::class
    ],
    version = 1)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun screenTimeDao(): ScreenTimeDao
    abstract fun sleepDetectorDao(): SleepDetectorDao
    abstract fun dropDetectorDao(): DropDetectorDao
    abstract fun lowLightExpoDao(): LowLightDetectorDao
    abstract fun deviceUnlocksDao(): DeviceUnlocksDao
    abstract fun userActivitiesDao(): UserActivitiesDao
    abstract fun callEventsDao(): CallEventsDao
    //
    abstract fun usedAppsDao(): UsedAppsDao
    abstract fun appHeartbeatDao(): AppHeartbeatDao
    abstract fun powerChargingDao(): PowerChargingDao
}