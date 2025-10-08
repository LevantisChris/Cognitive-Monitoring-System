package com.levantis.logmyself.utils

import android.app.Activity
import android.app.AppOpsManager
import android.content.Context
import android.content.Context.APP_OPS_SERVICE
import android.content.Intent
import android.content.pm.PackageManager
import android.provider.Settings
import android.util.Log
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.net.toUri

object PermissionsManager {

    fun isPermissionGranted(context: Context, permission: String): Boolean {
        return ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
    }

    fun isUsageAccessGranted(
        context: Context,
        packageName: String
    ): Boolean {
        val appOpsManager = context.getSystemService(APP_OPS_SERVICE) as AppOpsManager
        val mode = appOpsManager.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    fun isScheduleExactAlarmsGranted(context: Context): Boolean {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as android.app.AlarmManager
        return alarmManager.canScheduleExactAlarms()
    }

    fun isActionNotificationListenerSettingsGranted(context: Context): Boolean {
        val enabledListeners = Settings.Secure.getString(context.contentResolver, "enabled_notification_listeners")
        val packageName = context.packageName
        return enabledListeners != null && enabledListeners.contains(packageName)
    }

    /* Request permissions, normal and special */
    fun requestPermission(
        context: Context,
        permission: String,
        requestCode: Int,
        activity: Activity? = null,
        packageName: String? = null,
        isSpecial: Boolean = false
    ) {
        if (isSpecial) {
            val intent = Intent(permission)
            if (permission != Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS) {
                packageName?.let {
                    intent.data = "package:$it".toUri()
                }
            }
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
        } else {
            activity?.let {
                if (!isPermissionGranted(context, permission)) {
                    ActivityCompat.requestPermissions(it, arrayOf(permission), requestCode)
                }
            }
        }
    }

    /* This function will check at the state of the permission,
    *  it will be called when needed to see of the user allow or
    *  disallow any of the required permissions */
    fun checkStateOfPermissions() {

    }

    private fun addDeniedPermission() {
        // Add denied permission in the Room database
    }
    private fun removeDeniedPermission() {
        // Remove denied permission from the Room database
    }

    private fun addGrantedPermission() {
        // Add granted permission in the Room database
    }
    private fun removeGrantedPermission() {
        // Remove granted permission from the Room database
    }

}