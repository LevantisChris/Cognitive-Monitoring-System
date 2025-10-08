package com.levantis.logmyself.ui.profile

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.levantis.logmyself.auth.AuthManager
import com.levantis.logmyself.cloudb.FirestoreManager

class ProfileViewModel : ViewModel() {

    private val _textUserName = MutableLiveData<String>().apply {
        value = if (AuthManager.isUserAuthenticated()) AuthManager.getCurrentUser()?.displayName else "NaA"
    }
    val textUserName: LiveData<String> = _textUserName

}