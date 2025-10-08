package com.levantis.logmyself.cloudb

import android.util.Log
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.levantis.logmyself.cloudb.model.User

object FirestoreManager {

    fun getCurrentUserId(): String? {
        val auth = FirebaseAuth.getInstance()
        return auth.currentUser?.uid
    }

    private fun getUserCollectionPath(collectionName: String): String? {
        val userId = getCurrentUserId()
        return if (userId != null) "users/$userId/$collectionName" else null
    }

    /**
     * Save an events and its attributes.
     * @param collectionName The name of the collection (e.g., "sleep_events")
     * @param data The data to save (e.g., a SleepEvent object)
     * @param onSuccess Success callback
     * @param onFailure Failure callback
     * */
    fun saveEvent(
        collectionName: String,
        data: Any,
        onSuccess: () -> Unit,
        onFailure: (Exception) -> Unit
    ) {
        val firestore = FirebaseFirestore.getInstance()
        val collectionPath = getUserCollectionPath(collectionName)
        if (collectionPath != null) {
            firestore.collection(collectionPath)
                .add(data)
                .addOnSuccessListener {
                    Log.i("FirestoreManager", "Event saved")
                    onSuccess()
                }
                .addOnFailureListener {
                    Log.e("FirestoreManager", "Failed to save event", it)
                    onFailure(it)
                }
        } else {
            onFailure(Exception("User ID is null, cannot save event"))
        }
    }

    fun addUser(user: User, onResult: (Boolean) -> Unit) {
        val firestore = FirebaseFirestore.getInstance()
        val userId = getCurrentUserId()
        if (userId != null) {
            firestore.collection("users").document(userId).get()
                .addOnSuccessListener { document ->
                    if (!document.exists()) {
                        firestore.collection("users").document(userId).set(user)
                            .addOnSuccessListener {
                                Log.i("FirestoreManager", "User added successfully")
                                onResult(true)
                            }
                            .addOnFailureListener {
                                Log.e("FirestoreManager", "Error adding user", it)
                                onResult(false)
                            }
                    } else {
                        // User already exists
                        onResult(true)
                    }
                }
                .addOnFailureListener { exception ->
                    Log.e("FirestoreManager", "Error checking user existence", exception)
                    onResult(false)
                }
        } else {
            onResult(false)
        }
    }

}