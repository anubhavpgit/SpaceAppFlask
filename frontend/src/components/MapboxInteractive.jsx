/**
 * Mapbox Interactive Map - Click Anywhere for Weather & Air Quality
 *
 * Features:
 * - Click anywhere on Earth to see real-time data
 * - Current weather conditions & temperature
 * - Air quality index (AQI) from multiple sources
 * - 7-day temperature and AQI forecast
 * - Wildfire detection markers
 * - NASA TEMPO NO2 satellite data visualization
 * - Beautiful satellite imagery from Mapbox
 */

import React, { useRef, useState, useEffect } from 'react'
import mapboxgl from 'mapbox-gl'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MapPin, X, Loader2, Search,
  Maximize2, Minimize2, ChevronLeft
} from 'lucide-react'
import { apiService } from '../services/api'
import { useLocation } from '../context/LocationContext'
import WeatherCard from './WeatherCard'
import 'mapbox-gl/dist/mapbox-gl.css'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN
mapboxgl.accessToken = MAPBOX_TOKEN

const MapboxInteractive = () => {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef([])
  const isFirstMount = useRef(true)

  // Global location context - syncs with entire app
  const { location: globalLocation, setLocation: setGlobalLocation } = useLocation()

  // Debug logging
  useEffect(() => {
    console.log('🗺️ Mapbox Token:', MAPBOX_TOKEN ? 'Loaded' : 'MISSING!')
    console.log('🗺️ Map Container:', mapContainerRef.current)
  }, [])

  const [selectedLocation, setSelectedLocation] = useState(null)
  const [locationData, setLocationData] = useState(null)
  const [weatherData, setWeatherData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [wildfires, setWildfires] = useState([])
  const [showForecast, setShowForecast] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const containerRef = useRef(null)
  const [selectedDate, setSelectedDate] = useState(new Date())

  // Handle fullscreen toggle with browser API
  const toggleFullscreen = async () => {
    if (!containerRef.current) return

    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen()
        setIsFullscreen(true)
      } else {
        await document.exitFullscreen()
        setIsFullscreen(false)
      }

      // Force map resize after fullscreen change
      setTimeout(() => {
        if (mapRef.current) mapRef.current.resize()
      }, 100)
    } catch (err) {
      console.error('Fullscreen error:', err)
    }
  }

  // Listen for fullscreen changes (e.g., ESC key)
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
      if (mapRef.current) {
        setTimeout(() => mapRef.current.resize(), 100)
      }
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  // Initialize map with 3D features
  useEffect(() => {
    if (mapRef.current) return // initialize map only once

    console.log('🗺️ Initializing Mapbox map...')

    try {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/satellite-streets-v12',
        center: [globalLocation.lon, globalLocation.lat],
        zoom: 10,
        pitch: 60, // 3D tilt angle (0-85)
        bearing: 0, // Rotation
        antialias: true // Smooth 3D rendering
      })

      mapRef.current.on('load', () => {
        console.log('✅ Mapbox map loaded successfully!')

        // Enable 3D terrain
        mapRef.current.setTerrain({
          source: 'mapbox-dem',
          exaggeration: 1.5
        })

        // Add 3D terrain source
        mapRef.current.addSource('mapbox-dem', {
          type: 'raster-dem',
          url: 'mapbox://mapbox.mapbox-terrain-dem-v1',
          tileSize: 512,
          maxzoom: 14
        })

        // Add 3D buildings layer
        const layers = mapRef.current.getStyle().layers
        const labelLayerId = layers.find(
          (layer) => layer.type === 'symbol' && layer.layout['text-field']
        )?.id

        mapRef.current.addLayer(
          {
            id: '3d-buildings',
            source: 'composite',
            'source-layer': 'building',
            filter: ['==', 'extrude', 'true'],
            type: 'fill-extrusion',
            minzoom: 15,
            paint: {
              'fill-extrusion-color': '#aaa',
              'fill-extrusion-height': [
                'interpolate',
                ['linear'],
                ['zoom'],
                15,
                0,
                15.05,
                ['get', 'height']
              ],
              'fill-extrusion-base': [
                'interpolate',
                ['linear'],
                ['zoom'],
                15,
                0,
                15.05,
                ['get', 'min_height']
              ],
              'fill-extrusion-opacity': 0.6
            }
          },
          labelLayerId
        )
      })

      mapRef.current.on('error', (e) => {
        console.error('❌ Mapbox error:', e.error)
      })

      // Add navigation controls
      mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right')

      // Add geolocate control with event handler
      const geolocateControl = new mapboxgl.GeolocateControl({
        positionOptions: {
          enableHighAccuracy: true
        },
        trackUserLocation: true,
        showUserHeading: true
      })

      mapRef.current.addControl(geolocateControl, 'top-right')

      // Handle geolocate events
      geolocateControl.on('geolocate', (e) => {
        console.log('📍 Geolocated to:', e.coords.latitude, e.coords.longitude)
        handleMapClick(e.coords.latitude, e.coords.longitude)
      })

      // Handle map clicks
      mapRef.current.on('click', (e) => {
        const { lng, lat } = e.lngLat
        handleMapClick(lat, lng)
      })
    } catch (error) {
      console.error('❌ Failed to initialize Mapbox:', error)
    }
  }, [])

  // Watch for global location changes from navbar
  useEffect(() => {
    if (!mapRef.current || !globalLocation) return

    // Skip on first mount to avoid infinite loop
    if (isFirstMount.current) {
      isFirstMount.current = false
      return
    }

    console.log('🌍 Global location changed from navbar, flying map to:', globalLocation)

    // Fly to new location
    mapRef.current.flyTo({
      center: [globalLocation.lon, globalLocation.lat],
      zoom: 12,
      pitch: 60,
      duration: 2500,
      essential: true
    })

    // Fetch data for the new location
    handleMapClick(globalLocation.lat, globalLocation.lon)
  }, [globalLocation.lat, globalLocation.lon])

  // Search for location
  const handleSearch = async (query) => {
    if (!query || query.length < 3) {
      setSearchResults([])
      return
    }

    setIsSearching(true)
    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&limit=5`
      )
      const data = await response.json()
      setSearchResults(data.features || [])
    } catch (error) {
      console.error('Search error:', error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  // Handle search result selection
  const handleSelectLocation = (result) => {
    const [lon, lat] = result.center

    // Fly to location
    if (mapRef.current) {
      mapRef.current.flyTo({
        center: [lon, lat],
        zoom: 12,
        duration: 2000
      })
    }

    // Fetch data for this location
    handleMapClick(lat, lon)

    // Clear search
    setSearchQuery('')
    setSearchResults([])
  }

  // Refetch weather data when date changes (without refetching location/wildfires)
  const handleDateChange = async (newDate) => {
    if (!selectedLocation) return

    setSelectedDate(newDate)

    // Format date as YYYY-MM-DD
    const dateStr = newDate.toISOString().split('T')[0]

    try {
      const weather = await apiService.getWeather(
        selectedLocation.lat,
        selectedLocation.lon,
        dateStr
      )
      setWeatherData(weather)
      console.log(`📅 Weather updated for date: ${dateStr}`)
    } catch (error) {
      console.error('Error updating weather for date:', error)
    }
  }

  // Handle map click - updates entire app
  const handleMapClick = async (lat, lon) => {
    console.log(`🗺️ Map clicked at: ${lat.toFixed(4)}, ${lon.toFixed(4)}`);

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    setSelectedLocation({ lat, lon })
    setIsLoading(true)
    setLocationData(null)

    // Reset to today when clicking new location
    setSelectedDate(new Date())
    const dateStr = new Date().toISOString().split('T')[0]

    try {
      // Fetch all data in parallel
      const [conditions, forecast, locationInfo, wildfireData, weather] = await Promise.all([
        apiService.getCurrentConditions(lat, lon),
        apiService.getForecast(lat, lon),
        apiService.reverseGeocode(lat, lon),
        apiService.getWildfires(lat, lon, 200).catch(() => ({ fires: [] })),
        apiService.getWeather(lat, lon, dateStr).catch(() => null)
      ])

      const cityName = locationInfo?.location?.city || `${lat.toFixed(2)}, ${lon.toFixed(2)}`

      console.log('📊 Fetched data:', {
        conditions,
        forecast,
        cityName,
        wildfires: wildfireData?.fires?.length || 0
      })

      // UPDATE GLOBAL LOCATION - This syncs with entire app!
      setGlobalLocation(lat, lon, cityName)

      // Set weather data for WeatherCard
      setWeatherData(weather)

      // Set basic location data for AQI and map marker
      setLocationData({
        lat,
        lon,
        city: cityName,
        aqi: conditions?.air_quality_index,
        primary_pollutant: conditions?.dominant_pollutant
      })

      // Update wildfires
      if (wildfireData?.fires && wildfireData.fires.length > 0) {
        setWildfires(wildfireData.fires.map(fire => ({
          id: `fire-${fire.latitude}-${fire.longitude}`,
          latitude: fire.latitude,
          longitude: fire.longitude,
          confidence: fire.confidence,
          brightness: fire.brightness,
          severity: fire.severity
        })))
      } else {
        setWildfires([])
      }

    } catch (error) {
      console.error('❌ Error fetching location data:', error)
      setLocationData({
        lat,
        lon,
        city: `${lat.toFixed(2)}, ${lon.toFixed(2)}`,
        error: true
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Add markers when location or wildfires change
  useEffect(() => {
    if (!mapRef.current) return

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []

    // Add selected location marker
    if (selectedLocation) {
      const markerEl = document.createElement('div')
      markerEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="${locationData?.aqi ? getAQIColor(locationData.aqi) : '#3b82f6'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`
      markerEl.style.cursor = 'pointer'

      const marker = new mapboxgl.Marker({ element: markerEl })
        .setLngLat([selectedLocation.lon, selectedLocation.lat])
        .addTo(mapRef.current)

      markersRef.current.push(marker)
    }

    // Add wildfire markers
    wildfires.forEach(fire => {
      const markerEl = document.createElement('div')
      markerEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#ef4444" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flame"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>`
      markerEl.style.cursor = 'pointer'
      markerEl.classList.add('animate-pulse')

      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="padding: 8px;">
          <div style="font-weight: bold; color: #dc2626;">Active Wildfire</div>
          <div style="font-size: 12px;">Confidence: ${fire.confidence}%</div>
          <div style="font-size: 12px;">Severity: ${fire.severity}</div>
        </div>
      `)

      const marker = new mapboxgl.Marker({ element: markerEl })
        .setLngLat([fire.longitude, fire.latitude])
        .setPopup(popup)
        .addTo(mapRef.current)

      markersRef.current.push(marker)
    })
  }, [selectedLocation, locationData, wildfires])

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full"
    >
      {/* Map Container */}
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Fullscreen Toggle Button - Positioned below zoom controls, hidden on mobile */}
      <button
        onClick={toggleFullscreen}
        className="hidden md:block absolute top-40 right-4 z-30 p-3 bg-white/95 backdrop-blur-lg rounded-xl shadow-2xl hover:bg-white transition-all hover:scale-110"
        title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
      >
        {isFullscreen ? (
          <Minimize2 className="w-5 h-5 text-slate-700" />
        ) : (
          <Maximize2 className="w-5 h-5 text-slate-700" />
        )}
      </button>

      {/* Search Box - Mobile responsive, positioned to avoid zoom controls */}
      <div
        className={`absolute top-4 z-30 transition-all duration-300
          w-[calc(100%-5rem)] max-w-xs left-4
          md:w-96 md:max-w-md md:mx-0
          ${locationData ? 'md:left-[520px]' : 'md:left-1/2 md:-translate-x-1/2'}`}
      >
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              handleSearch(e.target.value)
            }}
            placeholder="Search for a city or location..."
            className="w-full px-4 py-2.5 pl-10 pr-4 md:px-4 md:py-3 md:pl-12 bg-white/95 backdrop-blur-lg rounded-xl shadow-2xl border border-white/20 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm md:text-base"
          />
          <Search className="absolute left-3 md:left-4 top-1/2 -translate-y-1/2 w-4 h-4 md:w-5 md:h-5 text-slate-400" />
          {isSearching && (
            <Loader2 className="absolute right-3 md:right-4 top-1/2 -translate-y-1/2 w-4 h-4 md:w-5 md:h-5 text-blue-500 animate-spin" />
          )}
        </div>

        {/* Search Results Dropdown */}
        {searchResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 bg-white/95 backdrop-blur-lg rounded-xl shadow-2xl border border-white/20 overflow-hidden"
          >
            {searchResults.map((result, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectLocation(result)}
                className="w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors border-b border-slate-100 last:border-b-0"
              >
                <div className="flex items-center gap-3">
                  <MapPin className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-slate-800">{result.text}</div>
                    <div className="text-xs text-slate-500">{result.place_name}</div>
                  </div>
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </div>

      {/* Instructions Overlay - Mobile responsive, positioned at bottom on mobile */}
      {!selectedLocation && !searchQuery && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="absolute bottom-20 md:top-24 md:bottom-auto left-1/2 -translate-x-1/2 z-10 px-4 max-w-xs md:max-w-none"
        >
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-2 md:px-6 md:py-3 rounded-full shadow-2xl">
            <p className="text-xs md:text-sm font-semibold flex items-center gap-2 text-center">
              <MapPin className="w-4 h-4 md:w-5 md:h-5 animate-bounce flex-shrink-0" />
              <span>Tap or search to explore</span>
            </p>
          </div>
        </motion.div>
      )}

      {/* Weather Intelligence Sidebar - Responsive: Bottom sheet on mobile, left sidebar on desktop */}
      <AnimatePresence>
        {locationData && !isLoading && (
          <>
            {/* Mobile: Bottom sheet */}
            <motion.div
              initial={{ y: '100%', opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: '100%', opacity: 0 }}
              className="md:hidden absolute left-0 right-0 bottom-0 top-20 z-20 flex flex-col bg-white rounded-t-3xl shadow-2xl"
            >
              {/* Mobile Close Button */}
              <button
                onClick={() => {
                  setSelectedLocation(null)
                  setLocationData(null)
                  setWildfires([])
                }}
                className="absolute right-4 top-4 p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-all z-30"
                title="Close weather panel"
              >
                <X className="w-5 h-5 text-slate-700" />
              </button>

              {/* WeatherCard Container with scrolling */}
              <div className="overflow-y-auto h-full px-4 pt-12 pb-4">
                <WeatherCard
                  weatherData={weatherData}
                  aqi={locationData.aqi}
                  loading={isLoading}
                  selectedDate={selectedDate}
                  onDateChange={handleDateChange}
                />
              </div>
            </motion.div>

            {/* Desktop: Left Sidebar */}
            <motion.div
              initial={{ x: -400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -400, opacity: 0 }}
              className="hidden md:flex absolute left-4 top-4 bottom-4 w-[450px] lg:w-[500px] z-20 flex-col"
            >
              {/* Desktop Close Button */}
              <button
                onClick={() => {
                  setSelectedLocation(null)
                  setLocationData(null)
                  setWildfires([])
                }}
                className="absolute -right-12 top-0 p-3 bg-white/95 backdrop-blur-lg rounded-lg shadow-2xl hover:bg-white transition-all hover:scale-110 z-30"
                title="Close weather panel"
              >
                <X className="w-5 h-5 text-slate-700" />
              </button>

              {/* WeatherCard Container with scrolling */}
              <div className="overflow-y-auto h-full pr-2">
                <WeatherCard
                  weatherData={weatherData}
                  aqi={locationData.aqi}
                  loading={isLoading}
                  selectedDate={selectedDate}
                  onDateChange={handleDateChange}
                />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Attribution - Mobile responsive */}
      <div className="absolute bottom-2 right-2 md:bottom-4 md:right-4 bg-white/90 backdrop-blur px-2 py-1 md:px-4 md:py-2 rounded-lg text-[10px] md:text-xs text-slate-600 z-10">
        <span className="hidden md:inline">Powered by Mapbox · NASA FIRMS · WAQI · OpenAQ</span>
        <span className="md:hidden">Mapbox · NASA · WAQI</span>
      </div>
    </div>
  )
}

// Helper function for AQI color coding (used for markers)
const getAQIColor = (aqi) => {
  if (aqi <= 50) return '#10b981'
  if (aqi <= 100) return '#f59e0b'
  if (aqi <= 150) return '#f97316'
  if (aqi <= 200) return '#ef4444'
  if (aqi <= 300) return '#a855f7'
  return '#7c2d12'
}

export default MapboxInteractive
