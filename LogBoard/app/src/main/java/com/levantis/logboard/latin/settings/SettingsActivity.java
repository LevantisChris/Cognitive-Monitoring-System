/*
 * Copyright (C) 2012 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.levantis.logboard.latin.settings;

import android.app.ActionBar;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.preference.PreferenceActivity;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.inputmethod.InputMethodInfo;
import android.view.inputmethod.InputMethodManager;


import com.levanits.logBoard.R;
import com.levantis.logboard.auth.AuthActivity;
import com.levantis.logboard.auth.AuthManager;
import com.levantis.logboard.latin.utils.FragmentUtils;

public class SettingsActivity extends PreferenceActivity {
    private static final String DEFAULT_FRAGMENT = SettingsFragment.class.getName();
    private static final String TAG = SettingsActivity.class.getSimpleName();
    private AlertDialog mAlertDialog;

    @Override
    protected void onStart() {
        super.onStart();

        // Check if the user is Authenticated
        boolean isAuthed = false;
        try {
            isAuthed = checkAuthUser();
        } catch (Exception e) {
            Log.e("SettingsActivity", "Exception in check if user is authenticated", e);
        }

        boolean enabled = false;
        try {
            enabled = isInputMethodOfThisImeEnabled();
        } catch (Exception e) {
            Log.e(TAG, "Exception in check if input method is enabled", e);
        }

        if (isAuthed && enabled) {
            Log.i(TAG, "User is authenticated and IME is enabled. Proceeding with SettingsActivity.");
        } else if (!isAuthed) {
            Log.i(TAG, "User is not authenticated. Redirecting to AuthActivity.");
            Intent intent = new Intent(this, AuthActivity.class);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            startActivity(intent);
            finish();
        } else {
            final Context context = this;
            AlertDialog.Builder builder = new AlertDialog.Builder(this);
            builder.setMessage(R.string.setup_message);
            builder.setPositiveButton(android.R.string.ok, new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int id) {
                    Intent intent = new Intent(android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS);
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    context.startActivity(intent);
                    dialog.dismiss();
                }
            });
            builder.setNegativeButton(android.R.string.cancel, new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int id) {
                    finish();
                }
            });
            builder.setCancelable(false);

            builder.create().show();
        }
    }

    private boolean checkAuthUser() {
        // Check if the user is authenticated
        if (!AuthManager.getInstance().isUserAuthenticated()) {
            Log.i("SettingsActivity", "User is not authenticated. Redirecting to AuthActivity.");
            return false;
        }
        Log.i("SettingsActivity", "User is authenticated. Proceeding with SettingsActivity.");
       return true;
    }

    /**
     * Check if this IME is enabled in the system.
     * @return whether this IME is enabled in the system.
     */
    private boolean isInputMethodOfThisImeEnabled() {
        final InputMethodManager imm =
                (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        final String imePackageName = getPackageName();
        for (final InputMethodInfo imi : imm.getEnabledInputMethodList()) {
            if (imi.getPackageName().equals(imePackageName)) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected void onCreate(final Bundle savedState) {
        super.onCreate(savedState);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            final View container = (View) getListView().getParent().getParent();
            // com.android.internal.R.id.prefs_container in
            // https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/res/res/layout/preference_list_content.xml
            container.setOnApplyWindowInsetsListener((view, windowInsets) -> {
                android.graphics.Insets insets = windowInsets.getInsets(WindowInsets.Type.systemBars());
                ViewGroup.MarginLayoutParams mlp = (ViewGroup.MarginLayoutParams) view.getLayoutParams();
                mlp.topMargin = insets.top;
                mlp.leftMargin = insets.left;
                mlp.bottomMargin = insets.bottom;
                mlp.rightMargin = insets.right;
                view.setLayoutParams(mlp);
                return WindowInsets.CONSUMED;
            });
        }

        final ActionBar actionBar = getActionBar();
        if (actionBar != null) {
            actionBar.setDisplayHomeAsUpEnabled(true);
            actionBar.setHomeButtonEnabled(true);
        }
    }

    @Override
    public boolean onOptionsItemSelected(final MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            super.onBackPressed();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    @Override
    public Intent getIntent() {
        final Intent intent = super.getIntent();
        final String fragment = intent.getStringExtra(EXTRA_SHOW_FRAGMENT);
        if (fragment == null) {
            intent.putExtra(EXTRA_SHOW_FRAGMENT, DEFAULT_FRAGMENT);
        }
        intent.putExtra(EXTRA_NO_HEADERS, true);
        return intent;
    }

    @Override
    public boolean isValidFragment(final String fragmentName) {
        return FragmentUtils.isValidFragment(fragmentName);
    }
}
