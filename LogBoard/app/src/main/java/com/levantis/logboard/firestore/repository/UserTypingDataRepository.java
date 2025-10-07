package com.levantis.logboard.firestore.repository;

import android.util.Log;

import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.CollectionReference;
import com.google.firebase.firestore.FirebaseFirestore;
import com.levantis.logboard.firestore.model.UserTypingData;

public class UserTypingDataRepository {
    private final FirebaseFirestore db = FirebaseFirestore.getInstance();
    private final CollectionReference usersRef = db.collection("users");

    public void addUserTypingData(FirebaseUser user, UserTypingData userTypingData) {
        usersRef.document(user.getUid()).collection("typing_session_data").add(userTypingData)
                .addOnSuccessListener(aVoid -> {
                    Log.i("UserRepository", "User typing data added successfully for user: " + user.getUid());
                })
                .addOnFailureListener(e -> {
                    Log.e("UserRepository", "Error adding user typing data for user " + user.getUid(), e);
                });
    }
}
