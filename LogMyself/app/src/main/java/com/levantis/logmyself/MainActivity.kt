package com.levantis.logmyself

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.levantis.logmyself.auth.AuthActivity
import com.levantis.logmyself.auth.AuthManager
import com.levantis.logmyself.databinding.ActivityMainBinding
import com.levantis.logmyself.sensors.listeners.DropListener
import com.levantis.logmyself.sensors.listeners.LightListener
import com.levantis.logmyself.ui.utils.DialogUtils
import com.levantis.logmyself.utils.PermissionsManager


class MainActivity : AppCompatActivity(), LightListener, DropListener {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d("MainActivity", "onCreate() called")

        checkIfUserIsAuthenticated()

        requestAllPermissions(this, (this as Activity))

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val navHostFragment = supportFragmentManager.findFragmentById(R.id.nav_host_fragment_activity_main) as NavHostFragment
        var navController = navHostFragment.navController
        binding.navView.setupWithNavController(navController)
    }

    override fun onResume() {
        super.onResume()
        Log.d("MainActivity", "onResume() called")
        //TODO: Check for any changes in permissions
    }

    /* Function to request all necessary permissions that the app needs */
    fun requestAllPermissions(context: Context, activity: Activity) {
        val permissionMessages = mapOf(
            Manifest.permission.READ_PHONE_STATE to "Permission required to read phone state",
            Manifest.permission.READ_CALL_LOG to "Permission required to read call logs",
            Manifest.permission.ACTIVITY_RECOGNITION to "Permission required for activity recognition",
            Settings.ACTION_USAGE_ACCESS_SETTINGS to "Permission required for usage stats access",
            Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM to "Permission required for exact alarms",
            Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS to "Permission required to detect VoIP calls",
            Manifest.permission.ACCESS_FINE_LOCATION to "Permission required for fine location access",
            Manifest.permission.ACCESS_COARSE_LOCATION to "Permission required for coarse location access",
            Manifest.permission.ACCESS_BACKGROUND_LOCATION to "Permission required for background location access",
            Manifest.permission.POST_NOTIFICATIONS to "Permission required for notifications"
        )

        val baseRequestCode = 1000
        val requiredPermissions = mutableListOf(
            Manifest.permission.READ_PHONE_STATE,
            Manifest.permission.READ_CALL_LOG,
            Manifest.permission.ACTIVITY_RECOGNITION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_BACKGROUND_LOCATION,
            Settings.ACTION_USAGE_ACCESS_SETTINGS,
            Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
            Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requiredPermissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        var currentIndex = 0

        fun requestNextPermission() {
            if (currentIndex >= requiredPermissions.size) return

            val permission = requiredPermissions[currentIndex]
            val isSpecialPermission = permission.startsWith("android.settings")
            val message = permissionMessages[permission] ?: "Permission required"

            // Check if permission needs to be requested
            // Different logic for special permissions and normal
            val needsRequest = when {
                isSpecialPermission && permission == Settings.ACTION_USAGE_ACCESS_SETTINGS ->
                    !PermissionsManager.isUsageAccessGranted(context, "com.levantis.logmyself")
                isSpecialPermission && permission == Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM ->
                    !PermissionsManager.isScheduleExactAlarmsGranted(context)
                isSpecialPermission && permission == Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS ->
                    !PermissionsManager.isActionNotificationListenerSettingsGranted(activity)
                !isSpecialPermission ->
                    !PermissionsManager.isPermissionGranted(context, permission)
                else -> false
            }

            if (needsRequest) {
                DialogUtils.showInfoDialog(
                    activity,
                    "Permission Required",
                    message,
                    "Settings"
                ) { dialog, _ ->
                    dialog.dismiss()
                    PermissionsManager.requestPermission(
                        context = context,
                        permission = permission,
                        requestCode = baseRequestCode + currentIndex,
                        activity = if (!isSpecialPermission) activity else null,
                        packageName = if (isSpecialPermission) "com.levantis.logmyself" else null,
                        isSpecial = isSpecialPermission
                    )
                    currentIndex++
                    requestNextPermission()
                }
            } else {
                currentIndex++
                requestNextPermission()
            }
        }

        requestNextPermission()
    }

    private fun checkIfUserIsAuthenticated() {
        if(!AuthManager.isUserAuthenticated()) {
            intent = Intent(this, AuthActivity::class.java)
            startActivity(intent)
            finish()
        }
    }
}