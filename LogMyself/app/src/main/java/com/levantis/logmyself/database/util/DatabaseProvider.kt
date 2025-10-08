package com.levantis.logmyself.database.util

import android.content.Context
import androidx.room.Room
import com.levantis.logmyself.database.AppDatabase
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
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

object DatabaseProvider {
    private var instance: AppDatabase? = null

    fun getDatabase(context: Context): AppDatabase {
        if (instance == null) {
            synchronized(AppDatabase::class) {
                instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "app_database"
                ).build()
            }
        }
        return instance!!
    }

    fun insertScreenTimeData(context: Context, screenTimeData: ScreenTimeData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.screenTimeDao().insertScreenTimeData(screenTimeData)
        }
    }

    suspend fun insertSleepEventsData(context: Context, sleepDetectorData: SleepDetectorData): Int {
        val database = getDatabase(context)
        return database.sleepDetectorDao().insertSleepData(sleepDetectorData).toInt()
    }

    fun insertDropDetectorData(context: Context, dropDetectorData: DropDetectorData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.dropDetectorDao().insertDropData(dropDetectorData)
        }
    }

    fun insertLowLightExpoDetectorData(context: Context, lowLightExpoDetectorData: LowLightExpoDetectorData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.lowLightExpoDao().insertLowLightData(lowLightExpoDetectorData)
        }
    }

    fun insertDeviceUnlocksData(context: Context, deviceUnlocksData: DeviceUnlocksData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.deviceUnlocksDao().insertDeviceUnlocksData(deviceUnlocksData)
        }
    }

    fun insertUsedAppsData(context: Context, usedAppsDataList: List<UsedAppsData>) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.usedAppsDao().insertUsedApps(usedAppsDataList)
        }
    }

    fun insertUserActivitiesData(context: Context, userActivitiesData: UserActivitiesData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.userActivitiesDao().insertUserActivitiesData(userActivitiesData)
        }
    }

    fun insertAppHeartbeatData(context: Context, appHeartbeat: AppHeartbeatData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.appHeartbeatDao().insertAppHeartbeat(appHeartbeat)
        }
    }

    fun insertPowerChargingData(context: Context, powerChargingData: PowerChargingData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.powerChargingDao().insertPowerPluginsData(powerChargingData)
        }
    }

    fun insertCallEventsData(context: Context, callEventsData: CallEventsData) {
        val database = getDatabase(context)
        CoroutineScope(Dispatchers.IO).launch {
            database.callEventsDao().insertCallEvent(callEventsData)
        }
    }
}