/**
 * Lighthouse v3 - Dashboard (PRODUCTION ENHANCED)
 * Real-time air quality awareness powered by NASA TEMPO
 *
 * New v3 Features:
 * - Live data indicators with countdown timer
 * - Auto-refresh every 60 seconds
 * - Data export (PDF/JSON) and sharing
 * - Mini sparklines for trend visualization
 * - Quick Facts and health tips
 * - Professional loading skeletons
 */

import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cloud, Wind, Droplets, AlertCircle, Activity, Radio, TrendingUp, TrendingDown, Zap, Sun, Moon, Umbrella } from 'lucide-react'
import CountUp from 'react-countup'
import { DashboardSkeleton } from '../components/Skeleton'
import WildfireAlert from '../components/WildfireAlert'
import DataExport from '../components/DataExport'
import { MetricTooltip } from '../components/Tooltip'
import BreathScoreCard from '../components/BreathScoreCard'
import WeatherCard from '../components/WeatherCard'
import LiveDataFeed from '../components/LiveDataFeed'
import MapboxInteractive from '../components/MapboxInteractive'
import MapboxTest from '../components/MapboxTest'
import TempoDataIndicator from '../components/TempoDataIndicator'
import { apiService } from '../services/api'
import { getAQIColor, getAQIGradient, getAQILabel, getHealthRecommendation, getAQITrend } from '../utils/aqi'
import { useLocation } from '../context/LocationContext'
import { formatDistanceToNow } from 'date-fns'

const Dashboard = () => {
  const [data, setData] = useState(null)
  const [wildfireData, setWildfireData] = useState(null)
  const [groundData, setGroundData] = useState(null)
  const [breathData, setBreathData] = useState(null)
  const [weatherData, setWeatherData] = useState(null)
  const [locationDetails, setLocationDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [countdown, setCountdown] = useState(60)
  const [selectedDate, setSelectedDate] = useState(new Date())
  const { location } = useLocation()

  const { lat, lon, city } = location

  // Fetch weather data for a specific date
  const fetchWeatherForDate = useCallback(async (date) => {
    try {
      const dateStr = date.toISOString().split('T')[0]
      const weather = await apiService.getWeather(lat, lon, dateStr)
      setWeatherData(weather)
      console.log(`📅 Weather updated for date: ${dateStr}`)
    } catch (err) {
      console.error('Error fetching weather for date:', err)
    }
  }, [lat, lon])

  // Handle date change
  const handleDateChange = useCallback(async (newDate) => {
    setSelectedDate(newDate)
    await fetchWeatherForDate(newDate)
  }, [fetchWeatherForDate])

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)

      // Format current date for weather API
      const dateStr = new Date().toISOString().split('T')[0]

      // Fetch all data in parallel
      const [forecast, wildfires, ground, breath, weather, locDetails] = await Promise.all([
        apiService.getForecast(lat, lon, city),
        apiService.getWildfires(lat, lon, 100),
        apiService.getGroundSensors(lat, lon),
        apiService.getBreathScore(lat, lon).catch(() => null),
        apiService.getWeather(lat, lon, dateStr).catch(() => null),
        apiService.reverseGeocode(lat, lon).catch(() => null)
      ])

      setData(forecast)
      setWildfireData(wildfires)
      setGroundData(ground?.data || {})
      setBreathData(breath)
      setWeatherData(weather)
      setLocationDetails(locDetails)
      setError(null)
      setLastUpdate(new Date())
      setCountdown(60)
    } catch (err) {
      console.error('Error fetching data:', err)
      console.error('Error details:', err.response?.data || err.message)
      setError(`Failed to load air quality data: ${err.response?.data?.message || err.message || 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }, [lat, lon, city])

  useEffect(() => {
    // Reset to today when location changes
    setSelectedDate(new Date())
    fetchData()
    // Refresh every 60 seconds
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [fetchData])

  // Countdown timer for next refresh
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => (prev > 0 ? prev - 1 : 60))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  if (loading && !data) return <DashboardSkeleton />

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Unable to Load Data</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    </div>
  )

  if (!data || !data.prediction) return null

  const { prediction, location: apiLocation, health_guidance, data_sources } = data
  const aqi = prediction.aqi
  const gradient = getAQIGradient(aqi)
  const category = prediction.category || getAQILabel(aqi)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black">
      {/* Interactive Mapbox Map - FIRST THING ON PAGE - Mobile optimized */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="relative"
      >
        <div className="bg-gradient-to-br from-slate-900 via-gray-900 to-black">
          <div className="max-w-7xl mx-auto px-2 sm:px-4 md:px-6 lg:px-8 pt-4 sm:pt-6 md:pt-8 pb-6 sm:pb-8 md:pb-12">
            <div className="text-center mb-3 sm:mb-4 md:mb-6">
              <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl font-bold text-white mb-1 sm:mb-2 md:mb-3 bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent px-2">
                🗺️ Interactive Air Quality Map
              </h2>
              <p className="text-white/80 text-xs sm:text-sm md:text-base lg:text-lg xl:text-xl font-medium px-2">
                Click anywhere on the map to see weather & air quality data
              </p>
              <p className="text-white/60 text-[10px] sm:text-xs md:text-sm mt-1 sm:mt-2 px-2">
                Powered by Mapbox satellite imagery & NASA TEMPO data
              </p>
            </div>

            <div className="w-full rounded-lg sm:rounded-xl md:rounded-2xl overflow-hidden shadow-2xl" style={{ height: '300px', maxHeight: '40vh' }}>
              <MapboxInteractive />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Hero AQI Display */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
        className="relative overflow-hidden"
        style={{ background: gradient }}
      >
        {/* Real-Time Indicator & Export - Mobile responsive */}
        <div className="absolute top-2 right-2 sm:top-4 sm:right-4 flex items-center gap-2 sm:gap-3 z-20 flex-wrap justify-end">
          <DataExport data={data} location={location} />

          {/* Live Indicator */}
          <div className="flex items-center gap-1.5 sm:gap-2 px-2 py-1.5 sm:px-4 sm:py-2 bg-white/10 backdrop-blur-lg rounded-lg border border-white/20">
            <div className="relative">
              <Radio className="text-green-400 animate-pulse-glow" size={12} />
              <div className="absolute inset-0 bg-green-400 blur-md opacity-50 animate-pulse" />
            </div>
            <div className="text-white text-xs sm:text-sm font-semibold">
              LIVE
            </div>
          </div>
        </div>

        {/* Auto-refresh Timer - Mobile responsive */}
        <div className="absolute top-2 left-2 sm:top-4 sm:left-4 z-20">
          <div className="flex items-center gap-1.5 sm:gap-2 px-2 py-1.5 sm:px-3 sm:py-2 bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 text-white text-[10px] sm:text-xs">
            <Activity size={12} className="text-blue-400" />
            <span className="hidden sm:inline">Next update: {countdown}s</span>
            <span className="sm:hidden">{countdown}s</span>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-8 sm:py-12 md:py-16 lg:py-20 text-center">
          <h1 className="text-white text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-light mb-2 sm:mb-3 md:mb-4 px-2">
            {locationDetails?.city || apiLocation.city || `${apiLocation.lat}, ${apiLocation.lon}`}
          </h1>
          {locationDetails?.precision && (
            <p className="text-white/60 text-[10px] sm:text-xs md:text-sm mb-2 px-2 leading-relaxed">
              Precise location: {locationDetails.neighborhood || locationDetails.city}
              {locationDetails.state && `, ${locationDetails.state}`}
              {locationDetails.country && `, ${locationDetails.country}`}
              {' '}(±{locationDetails.precision}m accuracy)
            </p>
          )}

          {/* AQI Label */}
          <div className="text-white/80 text-xs sm:text-sm md:text-base lg:text-lg xl:text-xl font-medium mb-1 sm:mb-2 tracking-wider px-2">
            AIR QUALITY INDEX (AQI)
          </div>

          {/* Giant AQI Number with CountUp - Mobile optimized */}
          <div className="text-white text-6xl sm:text-7xl md:text-8xl lg:text-9xl xl:text-[12rem] font-black leading-none mb-2 sm:mb-3 md:mb-4">
            <CountUp end={aqi} duration={1.5} />
          </div>

          <div className="text-white text-xl sm:text-2xl md:text-3xl lg:text-4xl font-semibold mb-2 px-2">
            {category}
          </div>

          <div className="text-white/60 text-[10px] sm:text-xs md:text-sm mb-2 sm:mb-3 md:mb-4">
            EPA Standard Scale (0-500)
          </div>

          {/* Health Recommendation */}
          <p className="text-white/90 text-xs sm:text-sm md:text-base lg:text-lg xl:text-xl max-w-2xl mx-auto px-4 leading-relaxed">
            {health_guidance.general_public || getHealthRecommendation(aqi)}
          </p>

          {/* Last Updated */}
          <p className="text-white/50 text-[10px] sm:text-xs md:text-sm mt-3 sm:mt-4 md:mt-6">
            Updated {formatDistanceToNow(lastUpdate, { addSuffix: true })}
          </p>
        </div>

        {/* Decorative gradient overlay */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-900 to-transparent" />
      </motion.div>

      {/* Details Section - Mobile responsive padding */}
      <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-6 sm:py-8 md:py-12">
        {/* Umbrella Alert Banner - Mobile optimized */}
        {weatherData?.umbrella_needed && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 sm:mb-6 md:mb-8 p-4 sm:p-5 md:p-6 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-xl sm:rounded-2xl shadow-2xl"
          >
            <div className="flex items-center gap-3 sm:gap-4 text-white">
              <div className="p-2 sm:p-3 md:p-4 bg-white/20 rounded-full flex-shrink-0">
                <Umbrella size={24} className="sm:w-7 sm:h-7 md:w-8 md:h-8" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg sm:text-xl md:text-2xl font-bold mb-1">Umbrella Alert</h3>
                <p className="text-blue-50 text-sm sm:text-base md:text-lg">
                  {weatherData.umbrella_needed.message || 'Rain expected today - bring an umbrella!'}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Wildfire Alert - Mobile optimized */}
        {wildfireData && wildfireData.wildfire_detected && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 sm:mb-6 md:mb-8"
          >
            <WildfireAlert wildfireData={wildfireData} />
            {wildfireData.closest_fire && locationDetails && (
              <div className="mt-3 sm:mt-4 p-4 sm:p-5 md:p-6 bg-orange-50 border border-orange-200 rounded-xl sm:rounded-2xl">
                <h4 className="text-base sm:text-lg font-bold text-orange-800 mb-2 sm:mb-3">Wildfire Location Details</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 md:gap-4 text-xs sm:text-sm">
                  <div>
                    <span className="font-semibold text-gray-700">Coordinates: </span>
                    <span className="text-gray-600 break-all">
                      {wildfireData.closest_fire.latitude.toFixed(4)}, {wildfireData.closest_fire.longitude.toFixed(4)}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-700">Distance: </span>
                    <span className="text-gray-600">{wildfireData.closest_fire.distance_km.toFixed(1)} km away</span>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-700">Brightness: </span>
                    <span className="text-gray-600">{wildfireData.closest_fire.brightness}K</span>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-700">Confidence: </span>
                    <span className="text-gray-600">{wildfireData.closest_fire.confidence}%</span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Featured Cards: Breath Score & Weather - Mobile optimized spacing */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 md:gap-8 mb-4 sm:mb-6 md:mb-8">
          <BreathScoreCard breathData={breathData} aqi={aqi} loading={loading && !breathData} />
          <WeatherCard
            weatherData={weatherData}
            aqi={aqi}
            loading={loading && !weatherData}
            selectedDate={selectedDate}
            onDateChange={handleDateChange}
          />
        </div>

        {/* NASA TEMPO Satellite Data Indicator */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-8"
        >
          <TempoDataIndicator forecastData={data} />
        </motion.div>

        {/* Live Data Feed */}
        <div className="mb-8">
          <LiveDataFeed />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
          {/* Weather Info */}
          {data_sources.weather?.available && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="bg-white/5 backdrop-blur-lg rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-white/10"
            >
              <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <Cloud className="w-6 h-6 sm:w-8 sm:h-8 text-blue-400" />
                <h3 className="text-lg sm:text-xl font-semibold text-white">Weather</h3>
              </div>
              <p className="text-white/70 text-base sm:text-lg mb-2">
                {data_sources.weather.conditions}
              </p>
              <p className="text-white/90 text-xl sm:text-2xl font-bold">
                {data_sources.weather.temperature}
              </p>
            </motion.div>
          )}

          {/* Data Sources */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
          >
            <div className="flex items-center gap-3 mb-4">
              <Wind className="w-8 h-8 text-green-400" />
              <h3 className="text-xl font-semibold text-white">Data Sources</h3>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-white/70">Satellite (TEMPO)</span>
                <span className={`text-sm px-2 py-1 rounded ${
                  data_sources.satellite?.available ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {data_sources.satellite?.available ? 'Active' : 'Unavailable'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/70">Ground Sensors</span>
                <span className={`text-sm px-2 py-1 rounded ${
                  data_sources.ground_sensors?.available ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {data_sources.ground_sensors?.available ? 'Active' : 'Unavailable'}
                </span>
              </div>
            </div>
          </motion.div>

          {/* Prediction Confidence */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
          >
            <div className="flex items-center gap-3 mb-4">
              <Droplets className="w-8 h-8 text-purple-400" />
              <h3 className="text-xl font-semibold text-white">Prediction</h3>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-white/70">Confidence</span>
                <span className="text-white font-semibold capitalize">{prediction.confidence}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/70">Risk Level</span>
                <span className={`text-sm px-2 py-1 rounded capitalize ${
                  prediction.risk_level === 'high' || prediction.risk_level === 'severe'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {prediction.risk_level}
                </span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Health Guidance Cards */}
        {health_guidance && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-8 bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10"
          >
            <h3 className="text-2xl font-bold text-white mb-6">Health Guidance</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-semibold text-white/90 mb-2">General Public</h4>
                <p className="text-white/70">{health_guidance.general_public}</p>
              </div>
              <div>
                <h4 className="text-lg font-semibold text-white/90 mb-2">Sensitive Groups</h4>
                <p className="text-white/70">{health_guidance.sensitive_groups}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Environmental Metrics - ALWAYS SHOW with NASA/Demo Data */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-8 bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10"
        >
          <div className="flex items-center gap-3 mb-6">
            <Activity className="w-6 h-6 text-blue-400" />
            <h3 className="text-2xl font-bold text-white">Environmental Metrics</h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4">
            {['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3'].map((pollutant) => {
              // Use ground data if available, otherwise use NASA TEMPO derived estimates
              let pollutantData = groundData?.[pollutant]

              // If no ground data for this pollutant, estimate from NASA TEMPO NO2
              if (!pollutantData && prediction?.no2_molecules_cm2) {
                // Convert: API returns value in 10^15 molecules/cm² units
                // 1e15 molecules/cm² ≈ 20 ppb NO2
                const no2_in_1e15_units = prediction.no2_molecules_cm2
                const no2_ppb = no2_in_1e15_units * 20

                if (pollutant === 'NO2') {
                  pollutantData = {
                    value: no2_ppb.toFixed(1),
                    unit: 'ppb',
                    quality: no2_ppb < 53 ? 'good' : no2_ppb < 100 ? 'moderate' : 'unhealthy',
                    source: 'NASA TEMPO'
                  }
                } else if (pollutant === 'PM2.5') {
                  // Estimate PM2.5 from NO2 correlation
                  const pm25 = (no2_ppb * 0.3).toFixed(1)
                  pollutantData = {
                    value: pm25,
                    unit: 'µg/m³',
                    quality: pm25 < 12 ? 'good' : pm25 < 35.4 ? 'moderate' : 'unhealthy',
                    source: 'Estimated'
                  }
                } else if (pollutant === 'PM10') {
                  const pm10 = (no2_ppb * 0.5).toFixed(1)
                  pollutantData = {
                    value: pm10,
                    unit: 'µg/m³',
                    quality: pm10 < 54 ? 'good' : pm10 < 154 ? 'moderate' : 'unhealthy',
                    source: 'Estimated'
                  }
                } else if (pollutant === 'O3') {
                  const o3 = (no2_ppb * 1.2).toFixed(1)
                  pollutantData = {
                    value: o3,
                    unit: 'ppb',
                    quality: o3 < 54 ? 'good' : o3 < 70 ? 'moderate' : 'unhealthy',
                    source: 'Estimated'
                  }
                } else if (pollutant === 'CO') {
                  const co = (no2_ppb * 0.05).toFixed(2)
                  pollutantData = {
                    value: co,
                    unit: 'ppm',
                    quality: co < 4.4 ? 'good' : co < 9.4 ? 'moderate' : 'unhealthy',
                    source: 'Estimated'
                  }
                } else if (pollutant === 'SO2') {
                  const so2 = (no2_ppb * 0.2).toFixed(1)
                  pollutantData = {
                    value: so2,
                    unit: 'ppb',
                    quality: so2 < 35 ? 'good' : so2 < 75 ? 'moderate' : 'unhealthy',
                    source: 'Estimated'
                  }
                }
              }

                const getQualityColor = (quality) => {
                  if (!quality) return 'text-gray-400'
                  if (quality === 'good') return 'text-green-400'
                  if (quality === 'moderate') return 'text-yellow-400'
                  if (quality.includes('unhealthy')) return 'text-orange-400'
                  if (quality === 'very_unhealthy') return 'text-red-400'
                  if (quality === 'hazardous') return 'text-purple-400'
                  return 'text-gray-400'
                }

                const getQualityBg = (quality) => {
                  if (!quality) return 'bg-gray-500/10'
                  if (quality === 'good') return 'bg-green-500/10'
                  if (quality === 'moderate') return 'bg-yellow-500/10'
                  if (quality.includes('unhealthy')) return 'bg-orange-500/10'
                  if (quality === 'very_unhealthy') return 'bg-red-500/10'
                  if (quality === 'hazardous') return 'bg-purple-500/10'
                  return 'bg-gray-500/10'
                }

                return (
                  <div
                    key={pollutant}
                    className={`${getQualityBg(pollutantData?.quality)} rounded-lg p-3 sm:p-4 border border-white/10`}
                  >
                    <div className="text-white/60 text-xs sm:text-sm mb-1">{pollutant}</div>
                    {pollutantData ? (
                      <>
                        <div className={`text-xl sm:text-2xl font-bold ${getQualityColor(pollutantData.quality)} mb-1`}>
                          {pollutantData.value}
                        </div>
                        <div className="text-white/40 text-xs">{pollutantData.unit}</div>
                        <div className={`text-xs mt-1 sm:mt-2 capitalize ${getQualityColor(pollutantData.quality)}`}>
                          {pollutantData.quality?.replace('_', ' ')}
                        </div>
                      </>
                    ) : (
                      <div className="text-gray-500 text-sm">N/A</div>
                    )}
                  </div>
                )
              })}
            </div>
            <p className="text-white/30 text-xs mt-4">
              {groundData && Object.keys(groundData).length > 0
                ? 'Data from OpenAQ Ground Sensors • Color-coded by EPA Air Quality Standards'
                : 'Estimated from NASA TEMPO NO₂ satellite data • Ground sensors unavailable for this location'
              }
            </p>
          </motion.div>

        {/* Quick Facts & Health Tips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-12 bg-gradient-to-br from-blue-500/10 to-purple-500/10 backdrop-blur-lg rounded-2xl p-8 border border-white/10"
        >
          <div className="flex items-center gap-3 mb-6">
            <Zap className="w-8 h-8 text-yellow-400" />
            <h3 className="text-2xl font-bold text-white">Quick Facts</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* AQI vs Breath Score Explainer */}
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <h4 className="text-lg font-semibold text-white mb-3">Understanding the Scores</h4>
              <div className="space-y-3 text-white/70 text-sm leading-relaxed">
                <div>
                  <span className="font-bold text-white">AQI (0-500):</span> EPA standard measuring air pollution levels
                </div>
                <div>
                  <span className="font-bold text-white">Breath Score (0-100):</span> Custom health metric combining AQI, weather, wildfires & personal impact
                </div>
                <p className="text-white/50 text-xs mt-2">
                  Higher AQI = worse air. Higher Breath Score = better health conditions.
                </p>
              </div>
            </div>

            {/* Best Time for Activities */}
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <Sun className="text-yellow-400" size={20} />
                Best Time for Activities
              </h4>
              <p className="text-white/70 text-sm leading-relaxed">
                {aqi <= 50 ?
                  "Perfect conditions! Any time is great for outdoor activities." :
                  aqi <= 100 ?
                  "Early morning or evening when temperatures are cooler." :
                  aqi <= 150 ?
                  "Limit strenuous outdoor activities. Stay indoors during peak hours." :
                  "Avoid all outdoor activities. Stay indoors with air filtration."
                }
              </p>
            </div>

            {/* Protection Tips */}
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <h4 className="text-lg font-semibold text-white mb-3">Protection Tips</h4>
              <ul className="text-white/70 text-sm space-y-2">
                {aqi <= 100 ? (
                  <>
                    <li>✓ Enjoy outdoor activities</li>
                    <li>✓ Stay hydrated</li>
                    <li>✓ Monitor local forecasts</li>
                  </>
                ) : (
                  <>
                    <li>✓ Wear an N95 mask outdoors</li>
                    <li>✓ Use air purifiers indoors</li>
                    <li>✓ Keep windows closed</li>
                    <li>✓ Limit outdoor exposure</li>
                  </>
                )}
              </ul>
            </div>
          </div>

          {/* 7-Day Forecast Preview */}
          {prediction.confidence && (
            <div className="mt-6 pt-6 border-t border-white/10">
              <h4 className="text-lg font-semibold text-white mb-3">Forecast Confidence</h4>
              <div className="flex items-center gap-4">
                <div className="flex-1 bg-white/5 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      prediction.confidence === 'high' ? 'bg-green-500 w-full' :
                      prediction.confidence === 'medium' ? 'bg-yellow-500 w-2/3' :
                      'bg-orange-500 w-1/3'
                    }`}
                  />
                </div>
                <span className="text-white font-semibold capitalize">{prediction.confidence}</span>
              </div>
              <p className="text-white/50 text-xs mt-2">
                Based on {data_sources.satellite?.data_points || 'multiple'} satellite data points
                {data_sources.satellite?.r_squared && ` (R² = ${(data_sources.satellite.r_squared * 100).toFixed(1)}%)`}
              </p>
            </div>
          )}
        </motion.div>

        {/* NASA Attribution */}
        <div className="mt-12 text-center">
          <p className="text-white/50 text-sm">
            Data from NASA TEMPO Satellite • OpenAQ Ground Sensors • NOAA Weather Service
          </p>
          <p className="text-white/30 text-xs mt-2">
            Last updated: {formatDistanceToNow(lastUpdate, { addSuffix: true })}
          </p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
