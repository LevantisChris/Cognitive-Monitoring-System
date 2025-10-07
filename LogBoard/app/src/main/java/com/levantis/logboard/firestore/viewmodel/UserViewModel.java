package com.levantis.logboard.firestore.viewmodel;

import android.app.Application;

import androidx.annotation.NonNull;
import androidx.lifecycle.AndroidViewModel;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;

import com.levantis.logboard.firestore.model.User;
import com.levantis.logboard.firestore.repository.UserRepository;

public class UserViewModel extends AndroidViewModel {
    private final UserRepository userRepository = new UserRepository();
    private final MutableLiveData<User> userLiveData = new MutableLiveData<>();

    public UserViewModel(@NonNull Application application) {
        super(application);
    }

    public LiveData<User> getUserLiveData() {
        return userLiveData;
    }

    public void addUser(User user) {
        userRepository.addUser(user);
    }

}
