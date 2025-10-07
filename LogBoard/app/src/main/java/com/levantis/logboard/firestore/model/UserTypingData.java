package com.levantis.logboard.firestore.model;

import java.time.LocalTime;
import java.util.Date;

/**
 * Typing data for a user in a typing session
 * */

public class UserTypingData {

    private Date dateCreated;
    private int totalPressureByTimesCounter;
    private LocalTime startTime;
    private LocalTime endTime;
    private int wordsTyped;
    private int charactersTyped;
    private long duration;
    private double totalWPS;
    private double totalCPS;
    private double avgPauseWtWDuration;
    private double maxPauseWtWDuration;
    private int pauseWtWListSize;
    private double avgPauseCtCDuration;
    private double maxPauseCtCDuration;
    private int pauseCtCListSize;
    private double meanIKI;
    private double stdDevIKI;
    private int ikiListSize;
    private int totalBackspaces;
    private int totalWordOrSentenceDeletions;
    private int totalBackspaceBurstCount;
    private int maxBackspaceBurstCount;
    private int totalCharactersDeleted;

    public UserTypingData() {}

    public UserTypingData(
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
        this.dateCreated = dateCreated;
        this.totalPressureByTimesCounter = totalPressureByTimesCounter;
        this.startTime = startTime;
        this.endTime = endTime;
        this.wordsTyped = wordsTyped;
        this.charactersTyped = charactersTyped;
        this.duration = duration;
        this.totalWPS = totalWPS;
        this.totalCPS = totalCPS;
        this.avgPauseWtWDuration = avgPauseWtWDuration;
        this.maxPauseWtWDuration = maxPauseWtWDuration;
        this.pauseWtWListSize = pauseWtWListSize;
        this.avgPauseCtCDuration = avgPauseCtCDuration;
        this.maxPauseCtCDuration = maxPauseCtCDuration;
        this.pauseCtCListSize = pauseCtCListSize;
        this.meanIKI = meanIKI;
        this.stdDevIKI = stdDevIKI;
        this.ikiListSize = ikiListSize;
        this.totalBackspaces = totalBackspaces;
        this.totalWordOrSentenceDeletions = totalWordOrSentenceDeletions;
        this.totalBackspaceBurstCount = totalBackspaceBurstCount;
        this.maxBackspaceBurstCount = maxBackspaceBurstCount;
        this.totalCharactersDeleted = totalCharactersDeleted;
    }

    public Date getDateCreated() {
        return dateCreated;
    }

    public void setDateCreated(Date dateCreated) {
        this.dateCreated = dateCreated;
    }

    public int getTotalPressureByTimesCounter() {
        return totalPressureByTimesCounter;
    }

    public void setTotalPressureByTimesCounter(int totalPressureByTimesCounter) {
        this.totalPressureByTimesCounter = totalPressureByTimesCounter;
    }

    public LocalTime getStartTime() {
        return startTime;
    }

    public void setStartTime(LocalTime startTime) {
        this.startTime = startTime;
    }

    public LocalTime getEndTime() {
        return endTime;
    }

    public void setEndTime(LocalTime endTime) {
        this.endTime = endTime;
    }

    public int getWordsTyped() {
        return wordsTyped;
    }

    public void setWordsTyped(int wordsTyped) {
        this.wordsTyped = wordsTyped;
    }

    public int getCharactersTyped() {
        return charactersTyped;
    }

    public void setCharactersTyped(int charactersTyped) {
        this.charactersTyped = charactersTyped;
    }

    public long getDuration() {
        return duration;
    }

    public void setDuration(long duration) {
        this.duration = duration;
    }

    public double getTotalWPS() {
        return totalWPS;
    }

    public void setTotalWPS(double totalWPS) {
        this.totalWPS = totalWPS;
    }

    public double getTotalCPS() {
        return totalCPS;
    }

    public void setTotalCPS(double totalCPS) {
        this.totalCPS = totalCPS;
    }

    public double getAvgPauseWtWDuration() {
        return avgPauseWtWDuration;
    }

    public void setAvgPauseWtWDuration(double avgPauseWtWDuration) {
        this.avgPauseWtWDuration = avgPauseWtWDuration;
    }

    public double getMaxPauseWtWDuration() {
        return maxPauseWtWDuration;
    }

    public void setMaxPauseWtWDuration(double maxPauseWtWDuration) {
        this.maxPauseWtWDuration = maxPauseWtWDuration;
    }

    public int getPauseWtWListSize() {
        return pauseWtWListSize;
    }

    public void setPauseWtWListSize(int pauseWtWListSize) {
        this.pauseWtWListSize = pauseWtWListSize;
    }

    public double getAvgPauseCtCDuration() {
        return avgPauseCtCDuration;
    }

    public void setAvgPauseCtCDuration(double avgPauseCtCDuration) {
        this.avgPauseCtCDuration = avgPauseCtCDuration;
    }

    public double getMaxPauseCtCDuration() {
        return maxPauseCtCDuration;
    }

    public void setMaxPauseCtCDuration(double maxPauseCtCDuration) {
        this.maxPauseCtCDuration = maxPauseCtCDuration;
    }

    public int getPauseCtCListSize() {
        return pauseCtCListSize;
    }

    public void setPauseCtCListSize(int pauseCtCListSize) {
        this.pauseCtCListSize = pauseCtCListSize;
    }

    public double getMeanIKI() {
        return meanIKI;
    }

    public void setMeanIKI(double meanIKI) {
        this.meanIKI = meanIKI;
    }

    public double getStdDevIKI() {
        return stdDevIKI;
    }

    public void setStdDevIKI(double stdDevIKI) {
        this.stdDevIKI = stdDevIKI;
    }

    public int getIkiListSize() {
        return ikiListSize;
    }

    public void setIkiListSize(int ikiListSize) {
        this.ikiListSize = ikiListSize;
    }

    public int getTotalBackspaces() {
        return totalBackspaces;
    }

    public void setTotalBackspaces(int totalBackspaces) {
        this.totalBackspaces = totalBackspaces;
    }

    public int getTotalWordOrSentenceDeletions() {
        return totalWordOrSentenceDeletions;
    }

    public void setTotalWordOrSentenceDeletions(int totalWordOrSentenceDeletions) {
        this.totalWordOrSentenceDeletions = totalWordOrSentenceDeletions;
    }

    public int getTotalBackspaceBurstCount() {
        return totalBackspaceBurstCount;
    }

    public void setTotalBackspaceBurstCount(int totalBackspaceBurstCount) {
        this.totalBackspaceBurstCount = totalBackspaceBurstCount;
    }

    public int getMaxBackspaceBurstCount() {
        return maxBackspaceBurstCount;
    }

    public void setMaxBackspaceBurstCount(int maxBackspaceBurstCount) {
        this.maxBackspaceBurstCount = maxBackspaceBurstCount;
    }

    public int getTotalCharactersDeleted() {
        return totalCharactersDeleted;
    }

    public void setTotalCharactersDeleted(int totalCharactersDeleted) {
        this.totalCharactersDeleted = totalCharactersDeleted;
    }

}
