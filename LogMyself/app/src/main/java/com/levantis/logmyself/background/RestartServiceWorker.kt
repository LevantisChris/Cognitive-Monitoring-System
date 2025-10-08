package com.levantis.logmyself.background

import android.annotation.SuppressLint
import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.SystemClock
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.work.Worker
import androidx.work.WorkerParameters


class RestartServiceWorker(context: Context, workerParams: WorkerParameters) : Worker(context, workerParams) {
    @SuppressLint("ScheduleExactAlarm")
    override fun doWork(): Result {
        try {
            val alarmManager = applicationContext.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val restartIntent = Intent(applicationContext, BackgroundMonitoringService::class.java)
            val pendingIntent = PendingIntent.getService(
                applicationContext,
                0,
                restartIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            // Schedule the service to restart after 5 seconds
            alarmManager.setExact(
                AlarmManager.ELAPSED_REALTIME_WAKEUP,
                SystemClock.elapsedRealtime() + 5000,
                pendingIntent
            )
            Log.i("RestartServiceWorker", "Service restart scheduled with AlarmManager.")
            return Result.success()
        } catch (e: Exception) {
            Log.e("RestartServiceWorker", "Failed to schedule service restart", e)
            return Result.failure()
        }
    }
}