package com.levantis.logboard.latin.settings;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.Preference;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.TextView;

import com.levanits.logBoard.R;
import com.levantis.logboard.auth.AuthActivity;
import com.levantis.logboard.auth.AuthManager;

public class UserProfileSettingsFragment extends SubScreenFragment {
    @Override
    public void onCreate(final Bundle icicle) {
        super.onCreate(icicle);

        /* If the user is authed load the User profile settings screen */
        if(AuthManager.getInstance().isUserAuthenticated()) {
            addPreferencesFromResource(R.xml.prefs_screen_user_profile);
            updateInfo();
        }

        try {
            findPreference("logout_button").setOnPreferenceClickListener(preference -> {
                AuthManager.getInstance().signOut();

                Intent intent = new Intent(getActivity(), AuthActivity.class);
                startActivity(intent);
                getActivity().finish();

                return true;
            });
        } catch (Exception e) {
            Log.e("UserProfileSettingsFragment Log", "Cannot load logout button");
        }
    }

    private void updateInfo() {
        try {
            final Preference userProfilePreference1 = findPreference("user_display_name");
            userProfilePreference1.setSummary("Logged in as " + getUserDisplayName());
            //
            final Preference userProfilePreference2 = findPreference("user_email");
            userProfilePreference2.setSummary("Email in use " + getUserEmail());
        } catch (Exception e) {
            Log.e("UserProfileSettingsFragment Log", "Cannot load user information");
        }
    }

    private String getUserEmail() throws Exception {
        SharedPreferences sharedPreferences = getActivity().getSharedPreferences("user_info", Context.MODE_PRIVATE);
        return sharedPreferences.getString("user_email", "Unknown name");
    }

    private String getUserDisplayName() throws Exception {
        SharedPreferences sharedPreferences = getActivity().getSharedPreferences("user_info", Context.MODE_PRIVATE);
        return sharedPreferences.getString("user_display_name", "Unknown name");
    }
}
