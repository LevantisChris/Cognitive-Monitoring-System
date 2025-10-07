package com.levantis.logboard.firestore.repository;

import android.util.Log;

import com.google.firebase.firestore.CollectionReference;
import com.google.firebase.firestore.FirebaseFirestore;
import com.levantis.logboard.firestore.model.User;

public class UserRepository {
    private final FirebaseFirestore db = FirebaseFirestore.getInstance();
    private final CollectionReference usersRef = db.collection("users");

    public void addUser(User user) {
        usersRef.document(user.getUID()).get()
                .addOnSuccessListener(documentSnapshot -> {
                    if (documentSnapshot.exists()) {
                        Log.i("UserRepository", "User already exists");
                    } else {
                        usersRef.document(user.getUID()).set(user)
                                .addOnSuccessListener(aVoid -> {
                                    Log.i("UserRepository", "User added successfully");
                                })
                                .addOnFailureListener(e -> {
                                    Log.e("UserRepository", "Error adding user", e);
                                });
                    }
                })
                .addOnFailureListener(e -> {
                    Log.e("UserRepository", "Error checking user existence", e);
                });
    }

    public void getUser(String userId) {
        usersRef.document(userId).get()
                .addOnSuccessListener(documentSnapshot -> {
                    if (documentSnapshot.exists()) {
                        User user = documentSnapshot.toObject(User.class);
                        //
                    } else {
                        // Handle the case where the user does not exist
                        Log.i("UserRepository", "User does not exist");
                    }
                })
                .addOnFailureListener(e -> {
                    Log.e("UserRepository", "Error getting user", e);
                });
    }
}
