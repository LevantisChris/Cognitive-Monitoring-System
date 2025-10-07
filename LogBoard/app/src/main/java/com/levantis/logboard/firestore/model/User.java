package com.levantis.logboard.firestore.model;

import java.time.LocalDate;
import java.time.LocalDateTime;

public class User {

    private String UID;
    private LocalDateTime dateCreated;
    private String email;

    public User() {}

    public User(String UID, String email) {
        this.UID = UID;
        this.email = email;
        this.dateCreated = LocalDateTime.now();
    }

    public String getUID() {return UID;}

    public void setUID(String UID) {this.UID = UID;}

    public LocalDateTime getDateCreated() {
        return dateCreated;
    }

    public void setDateCreated(LocalDateTime dateCreated) {
        this.dateCreated = dateCreated;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}
