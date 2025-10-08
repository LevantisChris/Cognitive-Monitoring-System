package com.levantis.logmyself.sensors.receivers

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.levantis.logmyself.sensors.SensorsDataManager

/*
* Receiver to handle all intent related events.
* **/

class IntentEvtReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action.equals(Intent.ACTION_USER_PRESENT)){
            Log.i("IntentEvtReceiver", "(ACTION_USER_PRESENT) Phone unlocked")
            SensorsDataManager.addPhoneUnlockedEvents(context) // increment the counter for phone unlocked events
        }
        if (intent.action.equals(Intent.ACTION_SCREEN_OFF)){
            Log.i("IntentEvtReceiver", "(ACTION_SCREEN_OFF) Phone screen turned off");
            SensorsDataManager.endScreenTimeTracking(context) // end tracking screen time
        }
        if(intent.action.equals(Intent.ACTION_SCREEN_ON)) {
            Log.i("IntentEvtReceiver", "(ACTION_SCREEN_ON) Phone screen turned on")
            SensorsDataManager.startScreenTimeTracking() // start tracking screen time
        }
        // Power connection events
        if(intent.action.equals(Intent.ACTION_POWER_CONNECTED)) {
            // Device plugged in
            Log.i("PowerConnectionReceiver", "Device plugged in")
            SensorsDataManager.startChargeTimeTracking()
        }
        if(intent.action.equals(Intent.ACTION_POWER_DISCONNECTED)) {
            // Device unplugged
            Log.i("PowerConnectionReceiver", "Device un-plugged")
            SensorsDataManager.stopChargeTimeTracking(context)
        }
    }
}