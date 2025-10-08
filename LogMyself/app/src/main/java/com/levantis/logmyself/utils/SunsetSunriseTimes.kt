package com.levantis.logmyself.utils

import java.time.LocalDateTime
import java.time.LocalTime

/**
 * This holds the sunrise and sunset times for different countries.
 * */

object SunsetSunriseTimes {

    var GREECE_SUMMER_SUNR: Long = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0).toEpochSecond(java.time.ZoneOffset.UTC) * 1000 // start of the day
    var GREECE_SUMMER_SUNS: Long = LocalDateTime.now().withHour(23).withMinute(59).withSecond(59).toEpochSecond(java.time.ZoneOffset.UTC) * 1000 // end of the day

    /* More countries will be added here ... */

}