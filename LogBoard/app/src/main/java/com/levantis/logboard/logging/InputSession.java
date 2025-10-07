package com.levantis.logboard.logging;

import java.util.ArrayList;

/**
 * This class represents a input session.
 *  This represents a session from the start of the lifecycle of the keyboard until the end.
 *  An input session can contain multiple typing sessions that start and end when the keyboard is opened and closed.
 * */
public class InputSession {

    private long startTime; // in milliseconds
    private long endTime; // in milliseconds
    public TypingSession activeTypingSession;

    public InputSession() {
        startTime = System.currentTimeMillis(); // returns the current time in milliseconds
    }

}
