package com.levantis.logboard.auth;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.lifecycle.ViewModelProvider;

import com.google.android.gms.auth.api.identity.BeginSignInRequest;
import com.google.android.gms.auth.api.identity.Identity;
import com.google.android.gms.auth.api.identity.SignInClient;
import com.google.android.gms.auth.api.identity.SignInCredential;
import com.google.android.gms.common.api.ApiException;
import com.google.firebase.auth.AuthCredential;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GoogleAuthProvider;
import com.levanits.logBoard.R;
import com.levantis.logboard.latin.settings.SettingsActivity;
import com.levantis.logboard.firestore.model.User;
import com.levantis.logboard.firestore.viewmodel.UserViewModel;

public class AuthActivity extends AppCompatActivity {

    private static final String TAG = "AuthActivity";
    private static final int REQ_ONE_TAP = 9001; // Request code for sign-in

    private FirebaseAuth firebaseAuth;
    private SignInClient oneTapClient;
    private BeginSignInRequest signInRequest;
    private UserViewModel userViewModel;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_auth);

        firebaseAuth = FirebaseAuth.getInstance();

        userViewModel = new ViewModelProvider(this).get(UserViewModel.class);

        // Check if user is already authenticated
        if (firebaseAuth.getCurrentUser() != null) {
            Log.i("AuthActivity", "User is already authenticated");
            // User is already signed in, redirect to SettingsActivity
            Intent intent = new Intent(this, SettingsActivity.class);
            startActivity(intent);
            finish();
        }

        // Initialize Google Sign-In client
        oneTapClient = Identity.getSignInClient(this);
        setupGoogleSignIn();

        Button authButton = findViewById(R.id.btnGoogleAuth);
        authButton.setOnClickListener(v -> googleAuthIntent());
    }

    private void setupGoogleSignIn() {
        signInRequest = new BeginSignInRequest.Builder()
                .setGoogleIdTokenRequestOptions(
                        BeginSignInRequest.GoogleIdTokenRequestOptions.builder()
                                .setSupported(true)
                                .setServerClientId(getString(R.string.default_web_client_id))
                                .setFilterByAuthorizedAccounts(false)
                                .build())
                .setAutoSelectEnabled(true)
                .build();
    }

    private void googleAuthIntent() {
        oneTapClient.beginSignIn(signInRequest)
                .addOnSuccessListener(this, result -> {
                    try {
                        startIntentSenderForResult(
                                result.getPendingIntent().getIntentSender(),
                                REQ_ONE_TAP,
                                null, 0, 0, 0, null);
                    } catch (Exception e) {
                        Log.e(TAG, "Google Sign-In Failed: " + e.getMessage());
                    }
                })
                .addOnFailureListener(this, e -> {
                    Log.e(TAG, "One Tap Sign-In Failed", e);
                    Toast.makeText(this, "Google Sign-In failed. Try again.", Toast.LENGTH_SHORT).show();
                });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_ONE_TAP) {
            try {
                SignInCredential credential = oneTapClient.getSignInCredentialFromIntent(data);
                String idToken = credential.getGoogleIdToken();
                if (idToken != null) {
                    firebaseAuthWithGoogle(idToken);
                }
            } catch (ApiException e) {
                Log.e(TAG, "Google Sign-In Failed", e);
            }
        }
    }

    private void firebaseAuthWithGoogle(String idToken) {
        AuthCredential credential = GoogleAuthProvider.getCredential(idToken, null);
        firebaseAuth.signInWithCredential(credential)
                .addOnCompleteListener(this, task -> {
                    if (task.isSuccessful()) {
                        FirebaseUser user = firebaseAuth.getCurrentUser();
                        Toast.makeText(AuthActivity.this, "Sign-In Successful!", Toast.LENGTH_SHORT).show();
                        updateUI(user);
                        userViewModel.addUser(new User(user.getUid(), user.getEmail())); // Add user to Firestore
                    } else {
                        Log.e(TAG, "Firebase Authentication Failed", task.getException());
                        Toast.makeText(AuthActivity.this, "Authentication Failed!", Toast.LENGTH_SHORT).show();
                    }
                });
    }

    private void updateUI(FirebaseUser user) {
        if (user != null) {
            Log.d(TAG, "Sign-In Successful: " + user.getEmail() + " - name: " + user.getDisplayName());
            saveUserInfo(user); // save user info to SharedPreferences
            // Redirect to SettingsActivity
            Intent intent = new Intent(this, SettingsActivity.class);
            startActivity(intent);
            finish();
        }
    }
}
