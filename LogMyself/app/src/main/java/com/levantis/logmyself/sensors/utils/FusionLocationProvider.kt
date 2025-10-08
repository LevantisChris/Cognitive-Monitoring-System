package com.levantis.logmyself.sensors.utils

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.os.Looper
import android.util.Log
import androidx.annotation.RequiresPermission
import androidx.core.app.ActivityCompat
import com.google.android.gms.location.ActivityRecognition
import com.google.android.gms.location.ActivityRecognitionClient
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.levantis.logmyself.sensors.SensorsDataManager
import com.levantis.logmyself.utils.PermissionsManager
import java.time.LocalDateTime

/*
*  Provide location updates every x minutes.
*  Get data such as latitude, longitude, accuracy and speed.
*/

class FusionLocationProvider (
    private val context: Context
) {

    private val fusedLocationClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)
    private val activityRecognitionClient: ActivityRecognitionClient =
        ActivityRecognition.getClient(context)
    private lateinit var locationCallback: LocationCallback

    @RequiresPermission(allOf = [Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION])
    fun startLocationUpdates() {
        if (!PermissionsManager.isPermissionGranted(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            )
            && !PermissionsManager.isPermissionGranted(
                context,
                Manifest.permission.ACCESS_COARSE_LOCATION
            )
        ) {
            Log.i("FusionLocationProvider", "Location permissions are not granted (at least one) - cannot start location updates")
            return
        }
        val locationRequest = LocationRequest.Builder(
            Priority.PRIORITY_HIGH_ACCURACY, 30_000L // 30 seconds
        ).setMinUpdateIntervalMillis(30_000L)
            .setMinUpdateDistanceMeters(0f)
            .build()

        locationCallback = object : LocationCallback() {
            override fun onLocationResult(locationResult: LocationResult) {
                for (location in locationResult.locations) {
                    logLocationData(location)
                }
            }
        }
        /* Start monitoring, but first check whether at least one location permission is already granted */
        fusedLocationClient.requestLocationUpdates(
            locationRequest,
            locationCallback,
            Looper.getMainLooper()
        )
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.ACTIVITY_RECOGNITION
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            return
        }
    }

    private fun logLocationData(location: Location) {
        val latitude = location.latitude
        val longitude = location.longitude
        val accuracy = location.accuracy
        val speed = location.speed
        val altitude = location.altitude
        val bearing = location.bearing
        val speedAccuracyMetersPerSecond =  location.speedAccuracyMetersPerSecond
        val timestampNow = LocalDateTime.now()
        SensorsDataManager.reportPositionGPSEvent(
            latitude = latitude,
            longitude = longitude,
            accuracy = accuracy,
            altitude = altitude,
            speed = speed,
            bearing = bearing,
            speedAccuracyMetersPerSecond = speedAccuracyMetersPerSecond,
            timestampNow = timestampNow
        )
    }

    fun stopLocationUpdates() {
        fusedLocationClient.removeLocationUpdates(locationCallback)
    }
}