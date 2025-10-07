package com.levantis.logboard.logging.metrics;

import android.util.Log;

import com.levantis.logboard.logging.Metric;
import com.levantis.logboard.logging.TypingSession;

import java.time.Duration;
import java.time.LocalTime;


/**
 * PauseCtC is about capturing the time between the release of one key and the press of the next key.
 * More specifically, it is the timer from an UP event to next DOWN event of the next character pressed,
 * this metric includes the pressure the user adds when pressing a character and the time to press the next
 * key (IKI).
 * */
public class PauseCtC extends Metric {
    private TypingSession typingSession; // the session this metric instance is associated with - where it belongs
    private LocalTime pauseDuration_start; // the metric (pause) will start when a character is typed
    private LocalTime pauseDuration_end; // the metric (pause) will end when the next character is typed

    public PauseCtC(TypingSession session) {
        super("PAUSE_DURATION_CtC",
                "Keystroke Dynamics",
                "The duration of the pause between two characters - hesitation - time to think - deep thinking.",
                3);
        Log.i("PauseCtC log", "PauseCtC metric created");
        reset();
        this.typingSession = session;
    }

    public void startPauseTimer() {
        Log.i("PauseCtC log", "PauseCtC timer started");
        pauseDuration_start = LocalTime.now();
    }

    public void endPauseTimer() {
        Log.i("PauseWtW log", "PauseWtW timer ended");
        pauseDuration_end = LocalTime.now();
        //Log.d("PauseWtW log", "LOCAL - PauseWtW duration: " + calcDuration());
    }

    public double calcDuration() {
        //
        try {
            if(pauseDuration_start == null || pauseDuration_end == null) {
                Log.i("PauseCtC log", "Cannot calculate duration, start or end time is null");
                throw new RuntimeException("Cannot calculate duration, start or end time is null");
            }
            Duration duration = Duration.between(pauseDuration_start, pauseDuration_end);
            return duration.getSeconds() + (double) duration.getNano() / 1_000_000_000;             // take precise seconds
        } catch (RuntimeException e) {
            Log.e("PauseCtC log", "Error calculating duration: " + e.getMessage());
            return -1; // if for any reason the duration cannot be calculated, return -1, no weight
        }
    }

    @Override
    public void reset() {}
}
