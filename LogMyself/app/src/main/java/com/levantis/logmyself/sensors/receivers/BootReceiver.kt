package com.levantis.logmyself.sensors.receivers

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.core.content.ContextCompat
import com.levantis.logmyself.background.BackgroundMonitoringService

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (Intent.ACTION_BOOT_COMPLETED == intent.action) {
            Log.i("BootReceiver", "Device booted, starting service...")
            val serviceIntent = Intent(context, BackgroundMonitoringService::class.java)
            ContextCompat.startForegroundService(context, serviceIntent)
        }
    }
}
