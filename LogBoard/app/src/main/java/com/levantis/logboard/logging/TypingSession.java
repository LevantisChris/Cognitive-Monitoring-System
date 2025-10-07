package com.levantis.logboard.logging;

import android.annotation.SuppressLint;
import android.os.Build;
import android.util.Log;

import com.levantis.logboard.auth.AuthManager;
import com.levantis.logboard.logging.metrics.IKI;
import com.levantis.logboard.logging.metrics.PauseCtC;
import com.levantis.logboard.logging.metrics.PauseWtW;
import com.levantis.logboard.firestore.model.UserTypingData;
import com.levantis.logboard.firestore.viewmodel.UserTypingDataModel;

import java.time.Duration;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;

public class TypingSession {
    public int wordsTyped; // is a feature describing a session
    public int charactersTyped; // is a feature describing a session
    private LocalTime startTime; // format: 15:09:39.278474
    private LocalTime endTime; // format: 15:09:39.278474
    private final Date dateCreated;

    /* PauseWtW  metrics */
    // a typing session will have at each time ONLY  one active
    // pause, not multiple. We need to track it because we also
    // need to end it when the user types a new word.
    public PauseWtW activePauseWtW = null;
    private double maxPauseWtWDuration; // the maximum - longest pause duration in a typing session - Highlights the most significant break in typing
    private final List<PauseWtW> pauseWtWList; // a typing session has multiple pauses durations in it
    public List<PauseCtC> activePauseCtCList = new ArrayList<>(Arrays.asList(null, null));// List because we might have two active pauses at the same time
    private double maxPauseCtCDuration; // the maximum - longest pause duration in a typing session - Highlights the most significant break in typing
    private final List<PauseCtC> pauseCtCList; // a typing session has multiple pauses durations in it

    /* Pressure metric */
    private int totalPressureByTimesCounter; // the total pressure applied to the keyboard keys in the current typing session, by counter

    /* IKI metric  */
    public IKI activeIKI = null;
    private final List<IKI> ikiList; // all the IKI's created in the typing session

    /* Error metric/s */
    private int totalBackspaces; // total times the user presses the DELETE (backspace button), indifferent of the purpose
    private int totalWordOrSentenceDeletions; // total times the user deletes (complete) text, a whole word or a sentence
    private int totalBackspaceBurstCount; // total times the user presses the DELETE (backspace button) in a burst, the burst must include at least 2 backspace presses
    private int maxBackspaceBurstCount; // the maximum number of backspace presses in a burst
    private int totalCharactersDeleted; // total characters deleted in a typing session, user deletes a character also
    // NOTE: that if the user selects text that is not complete (a word or a sentence) then this deletion counts as a character deletion (ex. Hello user selects ll and deletes it)

    public TypingSession() {
        Log.d("TypingSession log", "Typing Session created");
        dateCreated = new Date();
        pauseWtWList = new ArrayList<>();
        pauseCtCList = new ArrayList<>();
        ikiList = new ArrayList<>();
    }

    public void startTypingSession(InputSession inputSession, TypingSession typingSession) {
        Log.i("TypingSession log", "Session started");
        inputSession.activeTypingSession = typingSession;
        startTime = LocalTime.now(); // format: 15:09:39.278474
        endTime = null;
    }
    public void endTypingSession(InputSession inputSession, UserTypingDataModel userTypingDataModel) {
        Log.i("TypingSession log", "Session ended");
        endTime = LocalTime.now(); // format: 15:09:39.278474
        inputSession.activeTypingSession = null;
        typingSessionInfo(inputSession);
        //
        if (userTypingDataModel != null && checkDataUsability()) {
            generateTypingDataModel(
                    userTypingDataModel,
                    dateCreated,
                    totalPressureByTimesCounter,
                    startTime,
                    endTime,
                    wordsTyped,
                    charactersTyped,
                    calcDuration(),
                    totalWPS(),
                    totalCPS(),
                    calcAvgPauseWtWDuration(),
                    maxPauseWtWDuration,
                    pauseWtWList.size(),
                    calcAvgPauseCtCDuration(),
                    maxPauseCtCDuration,
                    pauseCtCList.size(),
                    calcMeanIKI(),
                    calcStdDevIKI(),
                    ikiList.size(),
                    totalBackspaces,
                    totalWordOrSentenceDeletions,
                    totalBackspaceBurstCount,
                    maxBackspaceBurstCount,
                    totalCharactersDeleted
            );
        } else {
            Log.e("TypingSession log", "UserTypingDataModel is null, cannot generate typing data model");
        }
    }

    // User wrote a word in the current session
    public void wordTyped() {
        wordsTyped++;
    }
    // User pressed a character in the current session (English or Greek)
    public void characterTyped() {
        Log.i("TypingSession log", "Character typed");
        charactersTyped++;
    }
    // Calculate the duration of the typing session
    public long calcDuration() {
        return java.time.temporal.ChronoUnit.SECONDS.between(startTime, endTime);
    }


    /** Typing speed calculations for a typing session
     * */
    public double totalWPS() {
        long elapsedTimeInSeconds = calcDuration();
        if (elapsedTimeInSeconds <= 0) return 0;
        return wordsTyped / (double) elapsedTimeInSeconds;
    }

    public double totalCPS() {
        long elapsedTimeInSeconds = calcDuration();
        if (elapsedTimeInSeconds <= 0) return 0;
        return charactersTyped / (double) elapsedTimeInSeconds;
    }
    /**------------------------------------------------------------------------------------------*/

    /** PauseWtW timer calculations for a typing session
    *  NOTE: A typing session has multiple pauses timers
    *  */
    // Add a pause timer in the typing session
    public void addPauseWtW(PauseWtW pauseWtWDuration) {
        pauseWtWList.add(pauseWtWDuration);
    }
    // Take all the pauses for a given typing session and calculate the average pause time
    private double calcAvgPauseWtWDuration() {
        if(pauseWtWList.isEmpty()) return -1;
        maxPauseWtWDuration = 0; // set it to 0
        double totalPauseDurationOnSession = 0;
        for(int i = 0; i < pauseWtWList.size(); i++) {
            double duration = pauseWtWList.get(i).calcDuration();
            if(duration > maxPauseWtWDuration) maxPauseWtWDuration = duration;
            totalPauseDurationOnSession += duration;
        }
        return totalPauseDurationOnSession / pauseWtWList.size();
    }
    /**------------------------------------------------------------------------------------------*/

    /** PauseCtC timer calculations for a typing session
     *  NOTE: A typing session has multiple pauses timers
     *  */
    public void addPauseCtC(PauseCtC pauseCtCDuration) {
        pauseCtCList.add(pauseCtCDuration);
    }
    private double calcAvgPauseCtCDuration() {
        int nullDurationsCrC = 0; // counter to check how many null durations we have, those will be removed from the size
        if(pauseCtCList.isEmpty()) return -1;
        maxPauseCtCDuration = 0; // set it to 0
        double totalPauseDurationOnSession = 0;
        for(int i = 0; i < pauseCtCList.size(); i++) {
            double duration = pauseCtCList.get(i).calcDuration();
            if(duration == -1) {nullDurationsCrC++; break;}; // -1 duration means null start or end time
            if (duration > maxPauseCtCDuration) maxPauseCtCDuration = duration;
            totalPauseDurationOnSession += duration;
        }
        return totalPauseDurationOnSession / (pauseCtCList.size() - nullDurationsCrC);
    }
    /**------------------------------------------------------------------------------------------*/

    /** Pressure calculations for a typing session
     *  NOTE: This is characteristic of the user's typing behavior
     *  in a typing session
     *  */
    public void addPressureCounter(int pressureCount) {
        totalPressureByTimesCounter += pressureCount;
    }

    public void removePressureCounter(int pressureCount) {
        totalPressureByTimesCounter -= pressureCount;
    }
    /**------------------------------------------------------------------------------------------*/

    /**
     * IKI's calculations for a typing session
     * We take the average and the standard deviation of all the IKI's.
     */
    public void addIki(IKI ikiMetric) {
        ikiList.add(ikiMetric);
    }
    private double calcMeanIKI() {
        if (ikiList.isEmpty()) {
            System.err.println("IKI log: IKI list is empty, cannot calculate mean.");
            return 0;
        }

        double sum = 0;
        int validIKIs = 0;
        for (IKI iki : ikiList) {
            double duration = iki.calcDuration();
            if (duration >= 0) { // Only add valid durations
                sum += duration;
                validIKIs++;
            }
        }
        return validIKIs > 0 ? sum / validIKIs : -1;
    }
    public double calcStdDevIKI() {
        double mean = calcMeanIKI();
        if (mean == -1) return -1;

        double sum = 0;
        int validIKIs = 0;
        for (IKI iki : ikiList) {
            double duration = iki.calcDuration();
            if (duration >= 0) {
                sum += Math.pow(duration - mean, 2);
                validIKIs++;
            }
        }
        return validIKIs > 0 ? Math.sqrt(sum / validIKIs) : -1;
    }
    /**------------------------------------------------------------------------------------------*/

    /** Errors related calculations */
    public void backspacePressed() {totalBackspaces++;}
    public void wordOrSentenceDeleted() {totalWordOrSentenceDeletions++;}
    public void backspaceBurst() {totalBackspaceBurstCount++;}
    public void setMaxBackspaceBurstCount(int newMaxBackspaceBurstCount) {
        characterDeleted(); // every backspace burst counts as a characters deletion
        if(newMaxBackspaceBurstCount > maxBackspaceBurstCount) this.maxBackspaceBurstCount = newMaxBackspaceBurstCount;
    }
    public void characterDeleted() {totalCharactersDeleted++;}

    private void typingSessionInfo(InputSession parentInputSession) {
        @SuppressLint("DefaultLocale") String logMessage = String.format(
                "Typing Session Info:\n" +
                        "═══════════════════\n" +
                        "Date created: %s\n" +
                        "Total pressure counter:  %d\n" +
                        "Start Time: %s\n" +
                        "End Time: %s\n" +
                        "Words Typed: %d\n" +
                        "Characters Typed: %d\n" +
                        "Duration: %d seconds\n" +
                        "Parent Input Session: %s\n" +
                        "Typing Speed:\n" +
                        " - Words/sec: %.2f\n" +
                        " - Chars/sec: %.2f\n" +
                        "Average PauseWtW Duration (by word to word): %.3f seconds\n" +
                        "Max PauseWtW Duration: %.3f seconds\n" +
                        "Total num of WtW pauses: %d\n" +
                        "Average PauseCtC Duration (by character to character): %.3f seconds\n" +
                        "Max PauseCtC Duration: %.3f seconds\n" +
                        "Total num of CtC pauses (with errors): %d\n" +
                        "Average (Mean) IKI: %.2f\n" +
                        "Std for IKI: %.4f\n" +
                        "Total IKI's (with errors): %d\n" +
                        "Total backspace pressed: %d\n" +
                        "Total (complete) word or sentence deletions: %d\n" +
                        "Total backspace bursts (>= 2): %d\n" +
                        "Max backspace burst press count: %d\n" +
                        "Characters deleted: %d",
                dateCreated,
                totalPressureByTimesCounter,
                startTime,
                endTime,
                wordsTyped,
                charactersTyped,
                calcDuration(), // Typing session duration
                parentInputSession,
                totalWPS(), totalCPS(), // Typing speed
                //
                calcAvgPauseWtWDuration(),
                maxPauseWtWDuration,
                pauseWtWList.size(),
                calcAvgPauseCtCDuration(),
                maxPauseCtCDuration,
                pauseCtCList.size(),
                calcMeanIKI(),
                calcStdDevIKI(),
                ikiList.size(),
                totalBackspaces,
                totalWordOrSentenceDeletions,
                totalBackspaceBurstCount,
                maxBackspaceBurstCount,
                totalCharactersDeleted
        );
        Log.i("TypingSession", logMessage);
    }

    private boolean checkDataUsability() {
        // Check if the typing session has enough data to be usable
        if (wordsTyped < 4 || charactersTyped < 20 || calcDuration() < 1.5) {
            Log.e("TypingSession", "Not enough data to generate typing data model");
            return false;
        }
        return true;
    }

    private void generateTypingDataModel(
            UserTypingDataModel userTypingDataModel,
            Date dateCreated,
            int totalPressureByTimesCounter,
            LocalTime startTime,
            LocalTime endTime,
            int wordsTyped,
            int charactersTyped,
            long duration,
            double totalWPS,
            double totalCPS,
            double avgPauseWtWDuration,
            double maxPauseWtWDuration,
            int pauseWtWListSize,
            double avgPauseCtCDuration,
            double maxPauseCtCDuration,
            int pauseCtCListSize,
            double meanIKI,
            double stdDevIKI,
            int ikiListSize,
            int totalBackspaces,
            int totalWordOrSentenceDeletions,
            int totalBackspaceBurstCount,
            int maxBackspaceBurstCount,
            int totalCharactersDeleted
    ) {
        UserTypingData userTypingData = new UserTypingData(
                dateCreated,
                totalPressureByTimesCounter,
                startTime,
                endTime,
                wordsTyped,
                charactersTyped,
                duration,
                totalWPS,
                totalCPS,
                avgPauseWtWDuration,
                maxPauseWtWDuration,
                pauseWtWListSize,
                avgPauseCtCDuration,
                maxPauseCtCDuration,
                pauseCtCListSize,
                meanIKI,
                stdDevIKI,
                ikiListSize,
                totalBackspaces,
                totalWordOrSentenceDeletions,
                totalBackspaceBurstCount,
                maxBackspaceBurstCount,
                totalCharactersDeleted
        );

        userTypingDataModel.addUserTypingData(
                AuthManager.getInstance().getCurrentUser(),
                userTypingData
        );

    }
}
