package com.levantis.logmyself.auth

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.gms.auth.api.identity.BeginSignInRequest
import com.google.android.gms.auth.api.identity.BeginSignInResult
import com.google.android.gms.auth.api.identity.Identity
import com.google.android.gms.auth.api.identity.SignInClient
import com.google.android.gms.common.api.ApiException
import com.google.android.gms.tasks.OnFailureListener
import com.google.android.gms.tasks.OnSuccessListener
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.GoogleAuthProvider
import com.levantis.logmyself.MainActivity
import com.levantis.logmyself.R
import com.levantis.logmyself.background.BackgroundMonitoringService
import com.levantis.logmyself.cloudb.FirestoreManager


class AuthActivity : AppCompatActivity() {

    private lateinit var firebaseAuth: FirebaseAuth
    private lateinit var oneTapClient: SignInClient
    private lateinit var signInRequest: BeginSignInRequest

    // For the animation
    val messages = listOf(
        "Monitor and improve your mind, effortlessly",
        "Detect changes in typing behavior",
        "Understand your sleep and movement patterns",
        "Support your mental well-being with insights"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_auth)

        loadDescriptionAnimation(messages)

        // Initialize FirebaseAuth
        firebaseAuth = FirebaseAuth.getInstance()

        // Check if user is already signed in
        if(firebaseAuth.currentUser != null) {
            Log.i("AuthActivity", "User already signed in: " + firebaseAuth.currentUser?.email)
            /* Redirect to the Main Activity */
            intent = Intent(this, MainActivity::class.java)
            startActivity(intent)
            finish()
        }

        // Initialize Google Sign-In client
        oneTapClient = Identity.getSignInClient(this);

        // Configure Google Sign-In
        signInRequest = BeginSignInRequest.Builder()
            .setGoogleIdTokenRequestOptions(BeginSignInRequest.GoogleIdTokenRequestOptions.builder()
                    .setSupported(true)
                    .setServerClientId(getString(R.string.default_web_client_id))
                    .setFilterByAuthorizedAccounts(false)
                    .build()
            )
            .setAutoSelectEnabled(true)
            .build()

        // Trigger Google Sign-In
        findViewById<View>(R.id.btnGoogleAuth).setOnClickListener {
            handleGoogleBtnClick()
        }
    }

    private fun handleGoogleBtnClick() {
        oneTapClient.beginSignIn(signInRequest)
            .addOnSuccessListener(this, OnSuccessListener { result: BeginSignInResult? ->
                try {
                    startIntentSenderForResult(
                        result!!.pendingIntent.intentSender, 9001, null, 0, 0, 0, null
                    )
                } catch (e: Exception) {
                    Log.e("AuthActivity", "Google Sign-In Failed: " + e.message)
                }
            }).addOnFailureListener(this, OnFailureListener { e: Exception? ->
                Log.e("AuthActivity", "One Tap Sign-In Failed", e)
            })
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 9001) {
            try {
                val credential = oneTapClient.getSignInCredentialFromIntent(data)
                val idToken = credential.googleIdToken
                if(idToken == null) return
                val firebaseAuthCredential = GoogleAuthProvider.getCredential(idToken, null)
                // Authenticate with Firebase
                firebaseAuth.signInWithCredential(firebaseAuthCredential)
                    .addOnCompleteListener(this) { task ->
                        if (task.isSuccessful) {
                            // Success
                            val user = firebaseAuth.currentUser
                            // Add the user in the database
                            addUserInDatabase(user) { success ->
                                if (success) {
                                    // Redirect user
                                    Toast.makeText(this, "Sign-in successful", Toast.LENGTH_SHORT).show()
                                    updateUI()
                                } else {
                                    Toast.makeText(this, "Sign-in failed", Toast.LENGTH_SHORT).show()
                                }
                            }
                        } else {
                            // Failed
                            Log.e("AuthActivity", "Sign-In Failed: " + task.exception?.message)
                            Toast.makeText(this, "Sign-in failed", Toast.LENGTH_SHORT).show()
                        }
                    }
            } catch (e: ApiException) {
                Log.e("AuthActivity", "Sign-In Failed: " + e.message)
            }
        }
    }

    private fun addUserInDatabase(firestoreUser: FirebaseUser?, callback: (Boolean) -> Unit) {
        val newUser = com.levantis.logmyself.cloudb.model.User(
            firestoreUser?.uid ?: run {
                callback(false)
                return
            },
            firestoreUser.displayName,
            firestoreUser.email,
        )
        FirestoreManager.addUser(newUser) { success ->
            if (success) {
                // User added or already exists
                Log.i("AuthActivity", "User added successfully")
                callback(true)
            } else {
                // Handle failure
                Log.e("AuthActivity", "Error adding user")
                callback(false)
            }
        }
    }

    private fun updateUI() {
        intent = Intent(this, MainActivity::class.java)
        startActivity(intent)
        // Start the background service
        startBackgroundService()
        finish()
    }

    private fun loadDescriptionAnimation(strings: List<String>) {
        var textView = findViewById<TextView>(R.id.textCarousel)
        var index = 0

        val handler = Handler(Looper.getMainLooper())
        val delayMillis: Long = 3000 // Time between messages (3 seconds)

        val runnable = object : Runnable {
            override fun run() {
                // Fade out animation
                textView.animate().alpha(0f).setDuration(500).withEndAction {
                    textView.text = messages[index]
                    textView.animate().alpha(1f).setDuration(500).start()
                    index = (index + 1) % messages.size
                }.start()

                handler.postDelayed(this, delayMillis)
            }
        }
        handler.post(runnable)
    }

    private fun startBackgroundService() {
        val intent = Intent(this, BackgroundMonitoringService::class.java)
        startService(intent)
    }
}