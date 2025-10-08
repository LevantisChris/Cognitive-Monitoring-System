package com.levantis.logmyself.ui.behavior

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.levantis.logmyself.R
import com.levantis.logmyself.databinding.FragmentBehaviorBinding

class BehaviorFragment : Fragment() {

    private var _binding: FragmentBehaviorBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        val behaviorViewModel =
                ViewModelProvider(this).get(BehaviorViewModel::class.java)

        _binding = FragmentBehaviorBinding.inflate(inflater, container, false)
        val root: View = binding.root

        return root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}