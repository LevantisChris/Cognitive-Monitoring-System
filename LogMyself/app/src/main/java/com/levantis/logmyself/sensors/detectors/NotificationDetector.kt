package com.levantis.logmyself.sensors.detectors

import android.app.Notification
import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.levantis.logmyself.sensors.SensorsDataManager
import java.time.LocalDateTime

/* An attempt to detect when the user receives a phone call from third party apps
*  like Messenger, WhatsUp, Viber etc. This is done by checking the notification
*  data and try to detect the name of the packages and some extra info.
*  This NOT the best way to do it, also it is very hard to gather metadata for the call, like
*  duration, start time and end time.
*  --
*  onNotificationRemoved, cannot capture the exact time of the call end, but
*  onNotificationPosted can detect with success the potential start of a VoIP call,
*  at least for the apps that are listed in the checkForVoipCall function and for the
*  current time.
*  --
*  This is not a very ethical way because we want the permission "BIND_NOTIFICATION_LISTENER_SERVICE"
* */

class NotificationDetector : NotificationListenerService() {

    fun startMonitoring(context: Context) {
        toggleNotificationListenerService(context, true)
    }

    fun stopMonitoring(context: Context) {
        toggleNotificationListenerService(context, false)
    }

    private fun toggleNotificationListenerService(context: Context, enable: Boolean) {
        val componentName = ComponentName(context, NotificationDetector::class.java)
        val packageManager = context.packageManager

        if (enable) {
            // Force rebind: disable and enable quickly
            packageManager.setComponentEnabledSetting(
                componentName,
                PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP
            )
            packageManager.setComponentEnabledSetting(
                componentName,
                PackageManager.COMPONENT_ENABLED_STATE_ENABLED,
                PackageManager.DONT_KILL_APP
            )
        } else {
            // Just disable
            packageManager.setComponentEnabledSetting(
                componentName,
                PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP
            )
        }
    }


    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val pkg = sbn.packageName
        val extras = sbn.notification.extras
        val title = extras.getString(Notification.EXTRA_TITLE)?.lowercase() ?: ""
        val text = extras.getString(Notification.EXTRA_TEXT)?.lowercase() ?: ""
        val category = sbn.notification.category
        val isOngoing = (sbn.notification.flags and Notification.FLAG_ONGOING_EVENT) != 0

        if (checkForVoipCall(
                pkg,
                title,
                text,
                category ?: "",
                isOngoing
        )) {
            Log.i("NotificationDetector", "VoIP Call Detected (onPost) from $pkg")
            // Report data in the database
            SensorsDataManager.reportCallEvent(
                null,
                "VoIP_CALL_THIRD_PARTY_APP",
                null,
                LocalDateTime.now()
            )
        } else {
            Log.i("NotificationDetector", "Notification Detected (onPost) from $pkg")
        }
    }

//    override fun onNotificationRemoved(sbn: StatusBarNotification) {
//        val pkg = sbn.packageName
//        val extras = sbn.notification.extras
//        val title = extras.getString(Notification.EXTRA_TITLE)?.lowercase() ?: ""
//        val text = extras.getString(Notification.EXTRA_TEXT)?.lowercase() ?: ""
//        val category = sbn.notification.category
//        val isOngoing = (sbn.notification.flags and Notification.FLAG_ONGOING_EVENT) != 0
//
//        if (checkForVoipCall(
//                pkg,
//                title,
//                text,
//                category ?: "",
//                isOngoing
//            )) {
//            Log.i("NotificationDetector", "VoIP Call Detected (onRemoved) from $pkg")
//        } else {
//            Log.i("NotificationDetector", "Notification Detected (onRemoved) from $pkg")
//        }
//    }

    /* Try to identify if the user is receiving or doing a phone call through a third party app (ex. Messenger, Viber etc.) */
    private fun checkForVoipCall(
        pkg: String,
        title: String,
        text: String,
        category: String,
        isOngoing: Boolean
    ): Boolean {
        val isVoipApp =
            pkg.contains("viber") || pkg.contains("messenger") || pkg.contains("whatsapp") || pkg.contains(
                "telegram"
            ) || pkg.contains("facebook") || pkg.contains("skype") || pkg.contains("zoom") || pkg.contains(
                "google"
            ) || pkg.contains("signal") || pkg.contains("discord") || pkg.contains("teams") || pkg.contains("instagram")
        val likelyCall =
            title.contains("call") || text.contains("calling") || text.contains("video") || text.contains(
                "audio"
            ) || category == Notification.CATEGORY_CALL
        return isVoipApp && likelyCall && isOngoing
    }
}