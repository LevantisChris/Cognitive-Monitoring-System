package com.levantis.logmyself.auth

import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.firestore.auth.User


object AuthManager {

    private val firebaseAuth: FirebaseAuth = FirebaseAuth.getInstance()

    fun isUserAuthenticated(): Boolean {
        return firebaseAuth.currentUser != null
    }

    fun getCurrentUser(): FirebaseUser? {
        return firebaseAuth.currentUser
    }

    fun signOut() {
        firebaseAuth.signOut()
    }
}