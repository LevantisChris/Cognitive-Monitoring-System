package com.levantis.logboard.logging.metrics;

import android.util.Log;

import com.levantis.logboard.logging.Metric;
import com.levantis.logboard.logging.TypingSession;

import java.time.Duration;
import java.time.LocalTime;

/**
 * IKI is about capturing the time between the release of one key and the press of the next key.
 * More specifically, it is the timer from an UP event to next DOWN event of the next character pressed,
 * This metric is important because it gives an idea of the timer the user takes to press the next key.
 *
 * For this metric we take (in TypingSession class):
 * 1) Mean of all IKI's of a typing session
 * 2) Standard Deviation of all IKI's of a typing session
 */

public class IKI extends Metric {

    private TypingSession typingSession; // the session this metric instance is associated with - where it belongs
    private LocalTime iki_start;
    private LocalTime iki_end;

    public IKI() {
        super(
                "IKI",
                "Keystroke Timing",
                "Inter-Key Interval (IKI) The time between the release of one key and the press of the next key.",
                3
        );
    }

    public void startIKI() {
        Log.i("IKI log", "Starting IKI");
        iki_start = LocalTime.now();
    }

    public void endIKI() {
        Log.i("IKI log", "Ending IKI");
        iki_end = LocalTime.now();
        Log.d("IKI log", "endIKI Start :" + iki_start + " End: " + iki_end);
    }

    public double calcDuration() {
        //Log.d("IKI log", "calcDuration Start :" + iki_start + " End: " + iki_end);
        try {
            if (iki_start == null || iki_end == null) {
                throw new RuntimeException("Cannot calculate duration, start or end time is null");
            }

            Duration duration = Duration.between(iki_start, iki_end);
            if (duration.isNegative()) {
                duration = Duration.between(iki_start, iki_end.plusSeconds(86400)); // Add 24 hours safely
            }

            return duration.toNanos() / 1_000_000_000.0; // Convert to seconds with decimal precision
        } catch (RuntimeException e) {
            Log.e("IKI log", "Error calculating duration: " + e.getMessage());
            return -1; // error
        }
    }


    @Override
    public void reset() {
        iki_start = null;
        iki_end = null;
    }
}
