package com.levantis.logboard.logging;

/**
 * This class represents a metric that can be measured.
 *  Abstract because:
 *  - It serves as a base template for all specific metric types
 *  - It defines a common structure that all metrics must follow
 *  - It enforces implementation of essential methods (reset() and getResults()) in child classes
 *  - It cannot be instantiated directly since different metrics will have different implementations
 * */

public abstract class Metric  {
    private String name;
    private String category;
    private String description;
    private int importance;

    public Metric(String name, String category, String description, int importance) {
        this.name = name;
        this.category = category;
        this.description = description;
        this.importance = importance;
    }

    public abstract void reset();
}
