package com.levantis.logmyself.utils

import java.time.LocalTime

/**
 * Basic user information that is used in the app.
 * These information will be defined by the user in
 * the initial start of app.
 * */

object BasicUserInfo {

    var USER_SLEEP_TIME: LocalTime = LocalTime.of(23, 0) // 11:00 PM
    var USER_WAKEUP_TIME: LocalTime = LocalTime.of(7, 0) // 7:00 AM

}