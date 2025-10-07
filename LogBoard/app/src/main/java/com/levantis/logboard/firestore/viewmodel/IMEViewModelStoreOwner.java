package com.levantis.logboard.firestore.viewmodel;

import androidx.lifecycle.ViewModelStore;
import androidx.lifecycle.ViewModelStoreOwner;

/**
 * Singleton class that implements ViewModelStoreOwner for managing ViewModel instances.
 * This is used to provide a ViewModelStore for the IME (Input Method Editor) to manage its ViewModels
 * and send user data typing info.
 */

public class IMEViewModelStoreOwner implements ViewModelStoreOwner {
    private static final IMEViewModelStoreOwner instance = new IMEViewModelStoreOwner();
    private final ViewModelStore viewModelStore = new ViewModelStore();

    private IMEViewModelStoreOwner() {}

    public static IMEViewModelStoreOwner getInstance() {
        return instance;
    }

    @Override
    public ViewModelStore getViewModelStore() {
        return viewModelStore;
    }
}

