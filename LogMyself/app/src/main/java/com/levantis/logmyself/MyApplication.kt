package com.levantis.logmyself

import android.app.Application
import android.app.PendingIntent
import android.content.Intent
import com.levantis.logmyself.background.BackgroundMonitoringService

class MyApplication :Application() {
    override fun onCreate() {
        super.onCreate()

        // Delete the database if it exists
        deleteDatabase("app_database")

        // Start the foreground service
        startBackService()
    }

    private fun startBackService() {
        val serviceIntent = Intent(this, BackgroundMonitoringService::class.java)
        //startForegroundService(serviceIntent)
        val pendingIntent = PendingIntent.getService(
            this, 0, serviceIntent, PendingIntent.FLAG_IMMUTABLE
        )
        pendingIntent.send()
    }
}