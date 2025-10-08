package com.levantis.logmyself.ui.profile

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.levantis.logmyself.auth.AuthActivity
import com.levantis.logmyself.auth.AuthManager
import com.levantis.logmyself.background.BackgroundMonitoringService
import com.levantis.logmyself.databinding.FragmentProfileBinding

class ProfileFragment : Fragment() {

    private var _binding: FragmentProfileBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        val profileViewModel =
            ViewModelProvider(this).get(ProfileViewModel::class.java)

        _binding = FragmentProfileBinding.inflate(inflater, container, false)
        val root: View = binding.root

        // Set the username in the TextView
        profileViewModel.textUserName.observe(viewLifecycleOwner) {
            binding.userName.text = it
        }

        return root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Listen for changes in the ViewModel
        binding.logOutButton.setOnClickListener {
            handleLogOut()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun handleLogOut() {
        AuthManager.signOut()
        stopBackgroundService()
        // Redirect to the Auth Activity
        val intent = Intent(requireContext(), AuthActivity::class.java)
        startActivity(intent)
    }

    private fun stopBackgroundService() {
        val intent = Intent(requireContext(), BackgroundMonitoringService::class.java)
        requireContext().stopService(intent)
    }
}