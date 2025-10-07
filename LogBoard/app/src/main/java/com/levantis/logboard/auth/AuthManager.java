package com.levantis.logboard.auth;

import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GetTokenResult;



import android.util.Log;

public class AuthManager {
    private static AuthManager instance;
    private final FirebaseAuth firebaseAuth;

    private AuthManager() {
        firebaseAuth = FirebaseAuth.getInstance();
    }

    public static synchronized AuthManager getInstance() {
        if (instance == null) {
            instance = new AuthManager();
        }
        return instance;
    }

    public boolean isUserAuthenticated() {
        FirebaseUser currentUser = firebaseAuth.getCurrentUser();
        if (currentUser == null) return false;
        
        // Check if token is still valid
        return !isTokenExpired(currentUser);
    }

    private boolean isTokenExpired(FirebaseUser user) {
        try {
            Task<GetTokenResult> task = user.getIdToken(false);
            if (task.isSuccessful()) {
                GetTokenResult result = task.getResult();
                long expirationTime = result.getExpirationTimestamp();
                long currentTime = System.currentTimeMillis() / 1000;
                
                // Check if token expires within next 5 minutes
                return (expirationTime - currentTime) < 300;
            }
            return true; // Assume expired if can't get token
        } catch (Exception e) {
            Log.e("AuthManager", "Error checking token expiration", e);
            return true; // Assume expired on error
        }
    }

    public void refreshTokenIfNeeded() {
        FirebaseUser user = getCurrentUser();
        if (user != null) {
            user.getIdToken(true)
                .addOnCompleteListener(task -> {
                    if (!task.isSuccessful()) {
                        Log.w("AuthManager", "Token refresh failed", task.getException());
                        signOut();
                    } else {
                        Log.d("AuthManager", "Token refreshed successfully");
                    }
                });
        }
    }

    public FirebaseUser getCurrentUser() {
        return firebaseAuth.getCurrentUser();
    }

    public void signOut() {
        firebaseAuth.signOut();
    }
}