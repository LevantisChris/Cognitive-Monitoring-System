package com.levantis.logmyself.sensors.detectors

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.telephony.TelephonyCallback
import android.telephony.TelephonyManager
import android.util.Log
import com.levantis.logmyself.sensors.SensorsDataManager
import com.levantis.logmyself.utils.PermissionsManager
import java.time.Instant
import java.time.ZoneId

class CallStateDetector(
    private val context: Context
) : TelephonyCallback(), TelephonyCallback.CallStateListener {

    private val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager

    fun startMonitoring() {
        if (PermissionsManager.isPermissionGranted(context, android.Manifest.permission.READ_CALL_LOG)) {
            Log.i("CallStateDetector", "Permission to read call logs is granted - registering")
            telephonyManager.registerTelephonyCallback(context.mainExecutor, this)
        } else {
            Log.i("CallStateDetector", "Permission to read call logs is not granted")
        }
    }

    fun stopMonitoring() {
        if (PermissionsManager.isPermissionGranted(context, android.Manifest.permission.READ_CALL_LOG)) {
            Log.i("CallStateDetector", "Permission to read call logs is granted - unregistering")
            telephonyManager.unregisterTelephonyCallback(this)
        } else {
            Log.i("CallStateDetector", "Permission to read call logs is not granted")
        }
    }

    override fun onCallStateChanged(state: Int) {
        when(state) {
            TelephonyManager.CALL_STATE_IDLE -> {
                // Call ended
                //TODO: Validate if a handler is a good approach here
                Handler(Looper.getMainLooper()).postDelayed({
                    fetchLastCallDetails()
                }, 1000)
            }
            TelephonyManager.CALL_STATE_RINGING -> {
                // Incoming call
            }
            TelephonyManager.CALL_STATE_OFFHOOK -> {
                // Call answered or outgoing call
            }
        }
    }

    private fun fetchLastCallDetails() {
        val cursor = context.contentResolver.query(
            android.provider.CallLog.Calls.CONTENT_URI,
            arrayOf(
                android.provider.CallLog.Calls.TYPE,
                android.provider.CallLog.Calls.DURATION,
                android.provider.CallLog.Calls.DATE
            ),
            null,
            null,
            "${android.provider.CallLog.Calls.DATE} DESC"
        )
        if(cursor == null) { return }
        cursor.use {
            var stateDescription = ""
            if (it.moveToFirst()) {
                val callType = it.getInt(it.getColumnIndexOrThrow(android.provider.CallLog.Calls.TYPE))
                val callDuration = it.getInt(it.getColumnIndexOrThrow(android.provider.CallLog.Calls.DURATION))
                val callDate = Instant.ofEpochMilli(it.getLong(it.getColumnIndexOrThrow(android.provider.CallLog.Calls.DATE)))
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime()
                Log.d("CallStateDetector", "Call type: $callType, Duration: $callDuration seconds, Date: $callDate")
                when (callType) {
                    android.provider.CallLog.Calls.INCOMING_TYPE -> { // 1
                        Log.i("CallStateDetector", "Incoming call ended. Duration: $callDuration seconds")
                        stateDescription = "INCOMING_TYPE"
                    }

                    android.provider.CallLog.Calls.OUTGOING_TYPE -> { // 2
                        Log.i("CallStateDetector", "Outgoing call ended. Duration: $callDuration seconds")
                        stateDescription = "OUTGOING_TYPE"
                    }

                    android.provider.CallLog.Calls.MISSED_TYPE -> { // 3 - caller might drop the call, or the receiver might not pick it up
                        Log.i("CallStateDetector", "Missed call. Duration: $callDuration seconds")
                        stateDescription = "MISSED_TYPE"
                    }

                    android.provider.CallLog.Calls.REJECTED_TYPE -> { // 5 - User manually rejected the call - INCOMING
                        Log.i("CallStateDetector", "Rejected call. Duration: $callDuration seconds")
                        stateDescription = "REJECTED_TYPE"
                    }

                    android.provider.CallLog.Calls.BLOCKED_TYPE -> { // 6 - Call was auto-blocked - INCOMING
                        Log.i("CallStateDetector", "Blocked call. Duration: $callDuration seconds")
                        stateDescription = "BLOCKED_TYPE"
                    }

                    android.provider.CallLog.Calls.ANSWERED_EXTERNALLY_TYPE -> { // 7 - Answered via headset, watch, etc. - INCOMING
                        Log.i("CallStateDetector", "Answered externally. Duration: $callDuration seconds")
                        stateDescription = "ANSWERED_EXTERNALLY_TYPE"
                    }
                }
                // Send data to the database (TYPE, DESCRIPTION, DURATION, DATETIME) - we add type because if might not be initialized by the description
                Log.i(
                    "CallStateDetector",
                    "Call info: Type: $callType, Description: $stateDescription, Duration: $callDuration seconds, Date: $callDate"
                )
                SensorsDataManager.reportCallEvent(
                    callType,
                    stateDescription,
                    callDuration,
                    callDate
                )
            }
        }
    }
}