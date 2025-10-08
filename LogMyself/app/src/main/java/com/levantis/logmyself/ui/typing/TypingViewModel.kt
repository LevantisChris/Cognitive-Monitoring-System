package com.levantis.logmyself.ui.typing

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

class TypingViewModel : ViewModel() {

    private val _text = MutableLiveData<String>().apply {
        value = "This is a typing Fragment"
    }
    val text: LiveData<String> = _text

}