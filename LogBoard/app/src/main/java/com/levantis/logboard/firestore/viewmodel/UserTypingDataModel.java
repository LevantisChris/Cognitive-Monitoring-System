package com.levantis.logboard.firestore.viewmodel;

import androidx.lifecycle.AndroidViewModel;
import androidx.lifecycle.MutableLiveData;

import com.google.firebase.auth.FirebaseUser;
import com.levantis.logboard.firestore.model.User;
import com.levantis.logboard.firestore.model.UserTypingData;
import com.levantis.logboard.firestore.repository.UserTypingDataRepository;

public class UserTypingDataModel extends AndroidViewModel {

    private final UserTypingDataRepository userTypingDataRepository = new UserTypingDataRepository();
    private final MutableLiveData<User> userLiveData = new MutableLiveData<>();

    public UserTypingDataModel(@androidx.annotation.NonNull android.app.Application application) {
        super(application);
    }

    public void addUserTypingData(FirebaseUser user, UserTypingData userTypingData) {
        userTypingDataRepository.addUserTypingData(user, userTypingData);
    }
}
