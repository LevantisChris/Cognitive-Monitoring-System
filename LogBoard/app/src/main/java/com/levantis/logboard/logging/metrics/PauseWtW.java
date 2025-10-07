package com.levantis.logboard.logging.metrics;

import android.util.Log;

import com.levantis.logboard.logging.Metric;
import com.levantis.logboard.logging.TypingSession;

import java.time.Duration;
import java.time.LocalTime;

/**
 * This class represents the metric of the pause  (hesitation, deep thinking etc.) between two words.
 *  The time between the end of one word and the beginning of the next - how much
 *  time it takes to write a new word - how much time the user thinks what he/she going
 *  to write. Must be enabled when the user has already write something (one or two words).
 *
 *  The difference between the pause from word to word (PauseWtW) and the pause from character to character (PauseCtC)
 *  is that the first one tells the delay when the user has already (potentially) complete a thought, a sentence or something else and
 *  is trying to figure out the next "step".
 *  The second one tells the delay when the user is still thinking what to write, what to type or how to type it. It is more precise than the
 *  first one and very valuable.
 */

public class PauseWtW extends Metric {

    private TypingSession typingSession; // the session this metric instance is associated with - where it belongs
    private LocalTime pauseDuration_start; // the metric (pause) will start when a word is typed
    private LocalTime pauseDuration_end; // the metric (pause) will end when the next word is typed

    public PauseWtW(TypingSession session) {
        super("PAUSE_DURATION_WtW",
                "Keystroke Dynamics",
                "The duration of the pause between two words - hesitation - time to think - deep thinking.",
                3);
        Log.i("PauseWtW log", "PauseWtW metric created");
        reset();
        this.typingSession = session;
    }

    public void startPauseDuration() {
        Log.i("PauseWtW log", "PauseWtW timer started");
        pauseDuration_start = LocalTime.now();
    }

    public void endPauseDuration() {
        Log.i("PauseWtW log", "PauseWtW timer ended");
        pauseDuration_end = LocalTime.now();
        Log.d("PauseWtW log", "LOCAL - PauseWtW duration: " + calcDuration());
    }

    public double calcDuration() {
        try {
            if(pauseDuration_start == null || pauseDuration_end == null) {
                throw new RuntimeException("Cannot calculate duration, start or end time is null");
            }
            Duration duration = Duration.between(pauseDuration_start, pauseDuration_end);
            return duration.getSeconds() + (double) duration.getNano() / 1_000_000_000; // take precise seconds
        } catch (Exception e) {
            Log.e("PauseWtW log", "Error calculating duration: " + e.getMessage());
            return 0; // return 0 if there is an exception, no weight
        }
    }
    @Override
    public void reset() {}
}

