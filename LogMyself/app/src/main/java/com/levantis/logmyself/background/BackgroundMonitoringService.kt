package com.levantis.logmyself.background

import android.Manifest
import android.R
import android.app.ActivityManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.annotation.RequiresPermission
import androidx.core.app.NotificationCompat
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.google.android.gms.location.ActivityRecognition
import com.google.android.gms.location.ActivityTransition
import com.google.android.gms.location.ActivityTransitionRequest
import com.google.android.gms.location.DetectedActivity
import com.levantis.logmyself.auth.AuthManager
import com.levantis.logmyself.database.data.AppHeartbeatData
import com.levantis.logmyself.database.util.DatabaseProvider
import com.levantis.logmyself.sensors.DetectorsManager
import com.levantis.logmyself.sensors.receivers.ActivityRecognitionReceiver
import com.levantis.logmyself.sensors.receivers.IntentEvtReceiver
import java.time.LocalDateTime
import java.util.concurrent.TimeUnit

class BackgroundMonitoringService : Service() {

    private lateinit var detectorsManager: DetectorsManager

    // Handler - Appheartbeat
    private val handler = Handler(Looper.getMainLooper())
    private val heartbeatIntervalMillis = 5 * 60 * 1000L // 5 minutes
    private val heartbeatRunnable = object : Runnable {
        override fun run() {
            logHeartbeat(true) // true = service is alive
            handler.postDelayed(this, heartbeatIntervalMillis)
        }
    }

    // Reference
    private var intentEvtReceiver: IntentEvtReceiver? = null

    @RequiresPermission(allOf = [Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION])
    override fun onCreate() {
        super.onCreate()

        // Start foreground service immediately to avoid "did not start in time" exception
        createNotificationChannel()
        val notification: Notification = NotificationCompat.Builder(this, "MonitoringServiceChannel")
            .setContentTitle("Monitoring in Background")
            .setContentText("Gathering sleep, drop, and light data.")
            .setSmallIcon(R.drawable.ic_menu_info_details)
            .build()
        startForeground(1, notification)

        detectorsManager = DetectorsManager(this)

        // The service must not start if the user is not authenticated
        if (!AuthManager.isUserAuthenticated()) {
            Log.i("BackgroundMonitoringService", "User not authenticated. Stopping service.")
            stopSelf()
            return
        }

        // Initialize the database
        DatabaseProvider.getDatabase(this)

        // Initialize DetectorsManager and start monitoring
        detectorsManager.startMonitoringDropDetection() // does not need any permission
        detectorsManager.startMonitoringLowLightDetection() // only WAKE_LOCK permission is needed (also might need light sensor permission, but this is handled in the class)
        detectorsManager.startMonitoringSleepDetection() // needs Activity Detection permission
        detectorsManager.startMonitoringCallDetection() // needs call permissions
        detectorsManager.startMonitoringFusionLocationDetector() // needs location permissions (at least one)
        detectorsManager.startMonitoringProximityDetector() // does not need any permission
        detectorsManager.startMonitoringNotificationDetector() // needs notification permission

        registerAllReceivers()

        // Start app heartbeat logging
        handler.post(heartbeatRunnable)
    }

    private fun logHeartbeat(status: Boolean) {
        val appHeartBeatData = AppHeartbeatData(
            timestamp = LocalDateTime.now(),
            status = status
        )
        DatabaseProvider.insertAppHeartbeatData(this, appHeartBeatData)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Keep the service running
        return START_STICKY
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        Log.i("BackgroundMonitoringService", "Task removed")
    }

    @RequiresPermission(Manifest.permission.ACTIVITY_RECOGNITION)
    override fun onDestroy() {
        super.onDestroy()
        Log.i("BackgroundMonitoringService", "Service destroyed")
        // Unregister receivers to avoid memory leaks
        try {
            intentEvtReceiver?.let {
                unregisterReceiver(it)
                intentEvtReceiver = null
            }
        } catch (e: IllegalArgumentException) {
            Log.w("BackgroundMonitoringService", "Receiver already unregistered", e)
        }

        // Remove activity recognition updates
        val client = ActivityRecognition.getClient(this)
        val activityRecognitionIntent = Intent(this, ActivityRecognitionReceiver::class.java)
        val activityRecognitionPendingIntent = PendingIntent.getBroadcast(
            this, 0, activityRecognitionIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )
        client.removeActivityUpdates(activityRecognitionPendingIntent)

        // Remove activity transition updates
        val activityTransitionPendingIntent = PendingIntent.getBroadcast(
            this, 1, activityRecognitionIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )
        client.removeActivityTransitionUpdates(activityTransitionPendingIntent)

        // Remove Notification

        // Stop all detectors
        stopAllDetectors()

        if (AuthManager.isUserAuthenticated()) restartService()
    }

    private fun stopAllDetectors() {
        detectorsManager.stopMonitoringDropDetection()
        detectorsManager.stopMonitoringLowLightDetection()
        detectorsManager.stopMonitoringSleepDetection()
        detectorsManager.stopMonitoringCallDetection()
        detectorsManager.stopMonitoringFusionLocationDetector()
        detectorsManager.stopMonitoringProximityDetector()
        detectorsManager.stopMonitoringNotificationDetector() // This will disable the also disable the permission for notifications, so the user after log in again will have to enable it again, the app request it again
    }

    /*
    * Make sure the app restarts after the termination of it (AlarmManager) */
//    private fun restartService() {
//        val restartIntent = Intent(applicationContext, BackgroundMonitoringService::class.java).also {
//            it.setPackage(packageName)
//        }
//
//        val restartPendingIntent = PendingIntent.getService(
//            this, 1, restartIntent, PendingIntent.FLAG_IMMUTABLE
//        )
//
//        try {
//            val alarmManager = getSystemService(Context.ALARM_SERVICE) as AlarmManager
//            if (alarmManager.canScheduleExactAlarms()) {
//                alarmManager.setExact(
//                    AlarmManager.ELAPSED_REALTIME_WAKEUP,
//                    SystemClock.elapsedRealtime() + 5000,  // 5 seconds later
//                    restartPendingIntent
//                )
//            } else {
//                Log.e("BackgroundMonitoringService", "Cannot schedule exact alarms. Permission not granted.")
//            }
//        } catch (e: SecurityException) {
//            Log.e("BackgroundMonitoringService", "Failed to schedule exact alarm due to SecurityException", e)
//        }
//    }

    /* Make sure the app restarts after the termination of it (WorkManager) */
    private fun restartService() {
        if (!isServiceRunning(this, BackgroundMonitoringService::class.java)) {
            val workRequest = OneTimeWorkRequestBuilder<RestartServiceWorker>()
                .setInitialDelay(5, TimeUnit.SECONDS) // Delay of 5 seconds
                .build()

            WorkManager.getInstance(this).enqueue(workRequest)
        } else {
            Log.i("BackgroundMonitoringService", "Service is already running. No need to restart.")
        }
    }

    private fun isServiceRunning(context: Context, serviceClass: Class<*>): Boolean {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        for (service in activityManager.getRunningServices(Int.MAX_VALUE)) {
            if (serviceClass.name == service.service.className) {
                return true
            }
        }
        return false
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            "MonitoringServiceChannel",
            "Monitoring Service Channel",
            NotificationManager.IMPORTANCE_LOW
        )
        val manager = getSystemService(NotificationManager::class.java)
        manager?.createNotificationChannel(channel)
    }

    private fun registerAllReceivers() {
        // Register screen state receivers
        val intentFilter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_USER_PRESENT)
            addAction(Intent.ACTION_POWER_CONNECTED)
            addAction(Intent.ACTION_POWER_DISCONNECTED)
        }
        intentEvtReceiver = IntentEvtReceiver()
        registerReceiver(intentEvtReceiver, intentFilter)

        // Register activity recognition
        registerActivityUpdates()
        registerActivityTransitions()
    }

    private fun registerActivityUpdates() {
        val client = ActivityRecognition.getClient(this)
        val intent = Intent(this, ActivityRecognitionReceiver::class.java)
        val pendingIntent = PendingIntent.getBroadcast(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )

        if (checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION) == PackageManager.PERMISSION_GRANTED) {
            client.requestActivityUpdates(10_000L, pendingIntent)
                .addOnSuccessListener {
                    Log.d("ActivityRecognition", "Regular updates registered")
                }
                .addOnFailureListener {
                    Log.e("ActivityRecognition", "Failed to register regular updates", it)
                }
        }
    }

    private fun registerActivityTransitions() {
        val client = ActivityRecognition.getClient(this)
        val intent = Intent(this, ActivityRecognitionReceiver::class.java)
        val pendingIntent = PendingIntent.getBroadcast(
            this, 1, intent, // different requestCode
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )

        val transitions = listOf(
            DetectedActivity.IN_VEHICLE,
            DetectedActivity.ON_BICYCLE,
            DetectedActivity.WALKING,
            DetectedActivity.RUNNING,
            DetectedActivity.STILL,
        ).flatMap { activityType ->
            listOf(
                ActivityTransition.Builder()
                    .setActivityType(activityType)
                    .setActivityTransition(ActivityTransition.ACTIVITY_TRANSITION_ENTER)
                    .build(),
                ActivityTransition.Builder()
                    .setActivityType(activityType)
                    .setActivityTransition(ActivityTransition.ACTIVITY_TRANSITION_EXIT)
                    .build()
            )
        }

        val request = ActivityTransitionRequest(transitions)

        if (checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION) == PackageManager.PERMISSION_GRANTED) {
            client.requestActivityTransitionUpdates(request, pendingIntent)
                .addOnSuccessListener {
                    Log.d("ActivityRecognition", "Transition updates registered")
                }
                .addOnFailureListener {
                    Log.e("ActivityRecognition", "Failed to register transitions", it)
                }
        } else {
            Log.e("BackgroundMonitoringService", "Permission not granted for activity recognition")
        }
    }
}
