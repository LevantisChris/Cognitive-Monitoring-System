package com.levantis.logmyself.ui.map

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.TextView
import androidx.fragment.app.DialogFragment
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.MapsInitializer
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.LatLngBounds
import com.google.android.gms.maps.model.Marker
import com.google.android.gms.maps.model.MarkerOptions
import com.levantis.logmyself.R
import com.levantis.logmyself.analysis_database.data_classes.KeyLocationInfo

class MapDialogFragment : DialogFragment(), OnMapReadyCallback {

    private lateinit var mapView: MapView
    private lateinit var locationCountTextView: TextView
    private lateinit var mapInfoTextView: TextView
    private lateinit var btnCloseMap: ImageButton
    
    private var googleMap: GoogleMap? = null
    private var keyLocations: List<KeyLocationInfo> = emptyList()

    companion object {
        private const val ARG_KEY_LOCATIONS = "key_locations"
        
        fun newInstance(keyLocations: List<KeyLocationInfo>): MapDialogFragment {
            val fragment = MapDialogFragment()
            val args = Bundle()
            args.putSerializable(ARG_KEY_LOCATIONS, keyLocations.toTypedArray())
            fragment.arguments = args
            return fragment
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setStyle(STYLE_NORMAL, R.style.FloatingMapDialogStyle)
        
        arguments?.let {
            val locationsArray = it.getSerializable(ARG_KEY_LOCATIONS) as? Array<KeyLocationInfo>
            keyLocations = locationsArray?.toList() ?: emptyList()
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.dialog_map_view, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Initialize views
        mapView = view.findViewById(R.id.mapView)
        locationCountTextView = view.findViewById(R.id.locationCountTextView)
        mapInfoTextView = view.findViewById(R.id.mapInfoTextView)
        btnCloseMap = view.findViewById(R.id.btnCloseMap)
        
        // Set up close button
        btnCloseMap.setOnClickListener {
            dismiss()
        }
        
        // Initialize map
        mapView.onCreate(savedInstanceState)
        mapView.getMapAsync(this)
        
        // Update location count
        updateLocationCount()
    }

    override fun onStart() {
        super.onStart()
        
        // Set dialog size to be more compact
        dialog?.window?.setLayout(
            (resources.displayMetrics.widthPixels * 0.9).toInt(),
            (resources.displayMetrics.heightPixels * 0.7).toInt()
        )
    }

    override fun onMapReady(map: GoogleMap) {
        googleMap = map
        
        // Configure map settings
        map.uiSettings.isZoomControlsEnabled = true
        map.uiSettings.isMyLocationButtonEnabled = false
        map.uiSettings.isCompassEnabled = true
        map.uiSettings.isMapToolbarEnabled = false
        
        // Set map type
        map.mapType = GoogleMap.MAP_TYPE_NORMAL
        
        // Add markers for key locations
        addLocationMarkers()
        
        // Set up marker click listener
        map.setOnMarkerClickListener { marker ->
            showMarkerInfo(marker)
            true
        }
    }

    private fun addLocationMarkers() {
        if (keyLocations.isEmpty()) {
            mapInfoTextView.text = "No location data available"
            return
        }

        val boundsBuilder = LatLngBounds.builder()
        val markers = mutableListOf<Marker>()

        keyLocations.forEachIndexed { index, location ->
            try {
                val position = LatLng(location.latitude, location.longitude)
                
                // Check if this is a HOME location
                val isHome = location.key_loc_type.lowercase().contains("home")
                
                val markerOptions = MarkerOptions()
                    .position(position)
                    .title(if (isHome) "🏠 HOME" else "Location ${index + 1}")
                    .snippet("Type: ${location.key_loc_type}")
                
                // Set different marker color for HOME
                if (isHome) {
                    markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_GREEN))
                } else {
                    markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_RED))
                }
                
                val marker = googleMap?.addMarker(markerOptions)
                
                marker?.let { markers.add(it) }
                boundsBuilder.include(position)
            } catch (e: Exception) {
                println("Error adding marker for location $index: ${e.message}")
            }
        }

        // Move camera to show all markers
        if (markers.isNotEmpty()) {
            try {
                val bounds = boundsBuilder.build()
                val padding = 100 // padding in pixels
                googleMap?.animateCamera(
                    CameraUpdateFactory.newLatLngBounds(bounds, padding)
                )
            } catch (e: Exception) {
                println("Error setting camera bounds: ${e.message}")
                // Fallback: zoom to first location
                keyLocations.firstOrNull()?.let { firstLocation ->
                    val position = LatLng(firstLocation.latitude, firstLocation.longitude)
                    googleMap?.animateCamera(
                        CameraUpdateFactory.newLatLngZoom(position, 12f)
                    )
                }
            }
        }
    }

    private fun showMarkerInfo(marker: Marker) {
        val title = marker.title ?: "Unknown Location"
        val snippet = marker.snippet ?: "No details available"
        
        // You can show a custom info window or toast here
        // For now, we'll just show the info in the text view
        mapInfoTextView.text = "$title - $snippet"
    }

    private fun updateLocationCount() {
        val count = keyLocations.size
        val homeCount = keyLocations.count { it.key_loc_type.lowercase().contains("home") }
        val otherCount = count - homeCount
        
        locationCountTextView.text = when {
            count == 0 -> "No locations found"
            count == 1 -> if (homeCount == 1) "1 HOME location" else "1 key location"
            else -> {
                val homeText = if (homeCount > 0) "$homeCount HOME" else ""
                val otherText = if (otherCount > 0) "$otherCount other" else ""
                val separator = if (homeText.isNotEmpty() && otherText.isNotEmpty()) " + " else ""
                "$homeText$separator$otherText locations"
            }
        }
    }

    override fun onResume() {
        super.onResume()
        mapView.onResume()
    }

    override fun onPause() {
        super.onPause()
        mapView.onPause()
    }

    override fun onDestroy() {
        super.onDestroy()
        mapView.onDestroy()
    }

    override fun onLowMemory() {
        super.onLowMemory()
        mapView.onLowMemory()
    }
}
