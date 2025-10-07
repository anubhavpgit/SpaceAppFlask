/**
 * WeatherCard Component
 *
 * Comprehensive weather intelligence featuring:
 * - Current weather with large temperature display
 * - Temperature scale toggle (Celsius, Fahrenheit, Kelvin)
 * - Extended weather metrics (UV, visibility, pressure, dew point, etc.)
 * - 24h rain forecast visualization
 * - Umbrella recommendation
 * - Clothing recommendations as visual cards
 * - Moon phase display
 * - Sunrise/sunset times
 */

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Cloud,
  CloudRain,
  Umbrella,
  Sun,
  Moon,
  Sunrise,
  Sunset,
  Wind,
  Droplets,
  Thermometer,
  Shirt,
  CloudSnow,
  CloudDrizzle,
  Eye,
  Gauge,
  CloudDrizzle as Dew,
  CloudCog,
  Zap,
  Snowflake,
  Calendar,
  ChevronLeft,
  ChevronRight,
  X
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'

const WeatherCard = ({ weatherData, aqi, loading, selectedDate: propSelectedDate, onDateChange }) => {
  // Temperature scale state (C, F, K) - persisted in localStorage
  const [tempScale, setTempScale] = useState(() => {
    return localStorage.getItem('tempScale') || 'C'
  })

  // Use prop if provided, otherwise internal state
  const [internalDate, setInternalDate] = useState(new Date())
  const selectedDate = propSelectedDate || internalDate
  const setSelectedDate = (newDate) => {
    if (onDateChange) {
      onDateChange(newDate)
    } else {
      setInternalDate(newDate)
    }
  }

  const [showDatePicker, setShowDatePicker] = useState(false)
  const [calendarMonth, setCalendarMonth] = useState(new Date())

  // Generate next 16 days for date selection (Open-Meteo forecast limit)
  const getNext16Days = () => {
    const days = []
    for (let i = 0; i < 16; i++) {
      const date = new Date()
      date.setDate(date.getDate() + i)
      days.push(date)
    }
    return days
  }

  // Month navigation
  const nextMonth = () => {
    const newMonth = new Date(calendarMonth)
    newMonth.setMonth(newMonth.getMonth() + 1)
    setCalendarMonth(newMonth)
  }

  const prevMonth = () => {
    const newMonth = new Date(calendarMonth)
    newMonth.setMonth(newMonth.getMonth() - 1)
    // Don't go before current month
    if (newMonth >= new Date(new Date().getFullYear(), new Date().getMonth(), 1)) {
      setCalendarMonth(newMonth)
    }
  }

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const formatFullDate = (date) => {
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
  }

  const isToday = (date) => {
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  // Update localStorage when scale changes
  useEffect(() => {
    localStorage.setItem('tempScale', tempScale)
  }, [tempScale])

  // Temperature conversion functions
  const convertTemp = (celsius) => {
    if (!celsius && celsius !== 0) return '--'
    const c = parseFloat(celsius)
    if (tempScale === 'F') {
      return Math.round((c * 9/5) + 32)
    } else if (tempScale === 'K') {
      return Math.round(c + 273.15)
    }
    return Math.round(c)
  }

  const getTempUnit = () => {
    return tempScale === 'C' ? '°C' : tempScale === 'F' ? '°F' : 'K'
  }

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-3xl p-8 border border-blue-100 shadow-xl">
        <div className="animate-pulse">
          <div className="h-8 bg-blue-200 rounded w-1/3 mb-6" />
          <div className="h-32 bg-blue-200 rounded mb-4" />
          <div className="h-48 bg-blue-200 rounded" />
        </div>
      </div>
    )
  }

  if (!weatherData) return null

  const current = weatherData.current || {}
  const forecast = weatherData.forecast || {}
  const astronomy = weatherData.astronomy || {}
  const recommendations = weatherData.recommendations || {}

  const rain_forecast = forecast.rain
  const umbrella_needed = recommendations.umbrella?.needed ? recommendations.umbrella : null
  const clothing_recommendations = [
    ...(recommendations.clothing?.layers || []),
    ...(recommendations.clothing?.accessories || [])
  ]
  const moon_phase = astronomy.moon_phase

  // Format time from ISO to display format
  const formatTime = (isoTime) => {
    if (!isoTime) return '--:--'
    try {
      const date = new Date(isoTime)
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
    } catch {
      return '--:--'
    }
  }

  const sunrise = formatTime(astronomy.sunrise)
  const sunset = formatTime(astronomy.sunset)
  const location = weatherData.location || 'Current Location'

  // Get weather icon based on conditions
  const getWeatherIcon = (condition) => {
    const lower = condition?.toLowerCase() || ''
    if (lower.includes('rain')) return <CloudRain className="text-blue-500" size={80} />
    if (lower.includes('cloud')) return <Cloud className="text-gray-400" size={80} />
    if (lower.includes('clear') || lower.includes('sun')) return <Sun className="text-yellow-500" size={80} />
    if (lower.includes('snow')) return <CloudSnow className="text-blue-300" size={80} />
    if (lower.includes('drizzle')) return <CloudDrizzle className="text-blue-400" size={80} />
    return <Cloud className="text-gray-400" size={80} />
  }

  // Moon phase emoji
  const getMoonEmoji = (phase) => {
    const phases = {
      'new': '🌑',
      'waxing_crescent': '🌒',
      'first_quarter': '🌓',
      'waxing_gibbous': '🌔',
      'full': '🌕',
      'waning_gibbous': '🌖',
      'last_quarter': '🌗',
      'waning_crescent': '🌘'
    }
    return phases[phase] || '🌙'
  }

  // Clothing icon mapping
  const getClothingIcon = (item) => {
    const lower = item.toLowerCase()
    if (lower.includes('jacket') || lower.includes('coat')) return '🧥'
    if (lower.includes('umbrella')) return '☂️'
    if (lower.includes('sunglasses')) return '🕶️'
    if (lower.includes('hat')) return '🧢'
    if (lower.includes('scarf')) return '🧣'
    if (lower.includes('gloves')) return '🧤'
    return '👕'
  }

  // UV Index color coding
  const getUVColor = (uvIndex) => {
    if (!uvIndex && uvIndex !== 0) return 'text-gray-400'
    const uv = parseFloat(uvIndex)
    if (uv <= 2) return 'text-green-600'
    if (uv <= 5) return 'text-yellow-600'
    if (uv <= 7) return 'text-orange-600'
    if (uv <= 10) return 'text-red-600'
    return 'text-purple-600'
  }

  const getUVBgColor = (uvIndex) => {
    if (!uvIndex && uvIndex !== 0) return 'from-gray-50 to-gray-100'
    const uv = parseFloat(uvIndex)
    if (uv <= 2) return 'from-green-50 to-green-100'
    if (uv <= 5) return 'from-yellow-50 to-yellow-100'
    if (uv <= 7) return 'from-orange-50 to-orange-100'
    if (uv <= 10) return 'from-red-50 to-red-100'
    return 'from-purple-50 to-purple-100'
  }

  const getUVBorderColor = (uvIndex) => {
    if (!uvIndex && uvIndex !== 0) return 'border-gray-200'
    const uv = parseFloat(uvIndex)
    if (uv <= 2) return 'border-green-200'
    if (uv <= 5) return 'border-yellow-200'
    if (uv <= 7) return 'border-orange-200'
    if (uv <= 10) return 'border-red-200'
    return 'border-purple-200'
  }

  const getUVRating = (uvIndex) => {
    if (!uvIndex && uvIndex !== 0) return 'Unknown'
    const uv = parseFloat(uvIndex)
    if (uv <= 2) return 'Low'
    if (uv <= 5) return 'Moderate'
    if (uv <= 7) return 'High'
    if (uv <= 10) return 'Very High'
    return 'Extreme'
  }

  // Wind speed color coding
  const getWindColor = (speed) => {
    const windSpeed = parseFloat(speed) || 0
    if (windSpeed < 10) return 'text-green-600'
    if (windSpeed < 20) return 'text-yellow-600'
    if (windSpeed < 30) return 'text-orange-600'
    return 'text-red-600'
  }

  // Format rain forecast data for chart
  const rainChartData = rain_forecast?.hourly?.map((item, index) => ({
    hour: item.time || `${index}h`,
    probability: item.probability || 0,
    intensity: item.intensity || 0
  })) || []

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="bg-gradient-to-br from-white via-cyan-50 to-blue-100 rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8 border border-blue-100 shadow-2xl"
    >
      {/* Header with Temperature Toggle - Mobile responsive */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 gap-3">
        <div className="min-w-0">
          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-2 sm:gap-3">
            <Cloud className="text-blue-600 flex-shrink-0" size={24} />
            <span className="truncate">Weather Intelligence</span>
          </h2>
          <p className="text-gray-600 mt-1 text-xs sm:text-sm md:text-base truncate">{location || 'Current Location'}</p>
        </div>

        {/* Temperature Scale Toggle - Mobile responsive */}
        <div className="flex items-center gap-1 sm:gap-2 bg-white/90 backdrop-blur-sm rounded-full p-1 sm:p-1.5 shadow-lg border border-blue-100 flex-shrink-0">
          <button
            onClick={() => setTempScale('C')}
            className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-full font-semibold transition-all text-xs sm:text-sm ${
              tempScale === 'C'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-blue-50 active:bg-blue-100'
            }`}
          >
            °C
          </button>
          <button
            onClick={() => setTempScale('F')}
            className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-full font-semibold transition-all text-xs sm:text-sm ${
              tempScale === 'F'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-blue-50 active:bg-blue-100'
            }`}
          >
            °F
          </button>
          <button
            onClick={() => setTempScale('K')}
            className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-full font-semibold transition-all text-xs sm:text-sm ${
              tempScale === 'K'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-blue-50 active:bg-blue-100'
            }`}
          >
            K
          </button>
        </div>
      </div>

      {/* Date Selector with Horizontal Scroll & Calendar - Mobile responsive */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-4 sm:mb-6 p-3 sm:p-4 bg-white/80 backdrop-blur-sm rounded-xl sm:rounded-2xl shadow-lg"
      >
        <div className="flex items-center justify-between mb-2 sm:mb-3 gap-2">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
            <Calendar className="text-blue-600 flex-shrink-0" size={16} />
            <div className="min-w-0 flex-1">
              <h3 className="text-sm sm:text-base md:text-lg font-bold text-gray-800 hidden sm:block">Select Forecast Date</h3>
              <h3 className="text-sm font-bold text-gray-800 sm:hidden">Date</h3>
              <span className="text-[10px] sm:text-xs md:text-sm text-gray-500 block truncate">({formatFullDate(selectedDate)})</span>
            </div>
          </div>

          {/* Calendar Toggle Button - responsive */}
          <button
            onClick={() => setShowDatePicker(!showDatePicker)}
            className="p-1.5 sm:p-2 rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white transition-all hover:scale-110 flex-shrink-0"
            title="Open calendar"
          >
            <Calendar size={16} className="sm:w-5 sm:h-5" />
          </button>
        </div>

        {/* Calendar Popup */}
        <AnimatePresence>
          {showDatePicker && (
            <motion.div
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              className="mb-4 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl border border-blue-200 shadow-lg"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={prevMonth}
                    className="p-1 hover:bg-blue-100 rounded-lg transition-colors"
                    title="Previous month"
                  >
                    <ChevronLeft size={20} className="text-gray-600" />
                  </button>
                  <h4 className="font-bold text-gray-800 min-w-[140px] text-center">
                    {calendarMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </h4>
                  <button
                    onClick={nextMonth}
                    className="p-1 hover:bg-blue-100 rounded-lg transition-colors"
                    title="Next month"
                  >
                    <ChevronRight size={20} className="text-gray-600" />
                  </button>
                </div>
                <button
                  onClick={() => setShowDatePicker(false)}
                  className="p-1 hover:bg-blue-100 rounded-lg transition-colors"
                >
                  <X size={16} className="text-gray-600" />
                </button>
              </div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-2">
                {/* Day headers */}
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="text-center text-xs font-semibold text-gray-500 pb-1">
                    {day}
                  </div>
                ))}

                {/* Calendar dates */}
                {(() => {
                  const today = new Date()
                  today.setHours(0, 0, 0, 0)

                  const firstDay = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1)
                  const lastDay = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 0)
                  const startPadding = firstDay.getDay()
                  const dates = []

                  // Add padding for first week
                  for (let i = 0; i < startPadding; i++) {
                    dates.push(<div key={`pad-${i}`} className="aspect-square" />)
                  }

                  // Add all dates
                  const totalDays = lastDay.getDate()
                  for (let day = 1; day <= totalDays; day++) {
                    const date = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), day)
                    date.setHours(0, 0, 0, 0)
                    const isPast = date < today
                    const maxDate = new Date()
                    maxDate.setDate(maxDate.getDate() + 16)
                    const isTooFar = date > maxDate // 16 days limit (Open-Meteo)
                    const isSelected = date.toDateString() === selectedDate.toDateString()
                    const isTodayDate = date.toDateString() === new Date().toDateString()
                    const isDisabled = isPast || isTooFar

                    dates.push(
                      <button
                        key={day}
                        onClick={() => {
                          if (!isDisabled) {
                            setSelectedDate(date)
                            setShowDatePicker(false)
                          }
                        }}
                        disabled={isDisabled}
                        className={`aspect-square rounded-lg text-sm font-semibold transition-all ${
                          isSelected
                            ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg scale-110'
                            : isTodayDate
                            ? 'bg-blue-100 text-blue-700 border-2 border-blue-500 hover:scale-105'
                            : isDisabled
                            ? 'text-gray-300 cursor-not-allowed'
                            : 'bg-white hover:bg-blue-50 text-gray-700 border border-gray-200 hover:scale-105'
                        }`}
                      >
                        {day}
                      </button>
                    )
                  }

                  return dates
                })()}
              </div>

              <div className="mt-3 text-xs text-gray-600 text-center">
                Select any date within the next 16 days for accurate forecasts
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Horizontal Scrolling Date Picker - Mobile optimized */}
        <div className="relative">
          <div className="overflow-x-auto scrollbar-thin scrollbar-thumb-blue-400 scrollbar-track-blue-100 pb-2 -mx-3 sm:mx-0 px-3 sm:px-0">
            <div className="flex gap-2 sm:gap-3 min-w-max">
              {getNext16Days().map((date, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedDate(date)}
                  className={`flex-shrink-0 px-4 py-2 sm:px-6 sm:py-3 rounded-lg sm:rounded-xl font-semibold transition-all active:scale-95 ${
                    date.toDateString() === selectedDate.toDateString()
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg scale-105'
                      : 'bg-white hover:bg-blue-50 active:bg-blue-100 text-gray-700 border border-blue-100 hover:scale-105'
                  }`}
                >
                  <div className="text-[10px] sm:text-xs opacity-75">
                    {isToday(date) ? 'Today' : date.toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div className="text-sm sm:text-base md:text-lg font-bold">{formatDate(date)}</div>
                </button>
              ))}
            </div>
          </div>
          {/* Scroll hint arrows */}
          <div className="absolute right-0 top-0 bottom-0 w-8 sm:w-12 bg-gradient-to-l from-white/80 to-transparent pointer-events-none rounded-r-xl" />
        </div>

        {!isToday(selectedDate) && weatherData?.is_forecast && (
          <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-300">
            <p className="text-sm text-green-900">
              <strong>📅 Forecast Mode:</strong> Showing predicted weather for {formatFullDate(selectedDate)}.
            </p>
            <p className="text-xs text-green-700 mt-2">
              {weatherData?.data_source || 'Weather forecast powered by Open-Meteo'} •
              Forecasts up to 16 days available with decreasing accuracy over time.
            </p>
          </div>
        )}
        {!isToday(selectedDate) && !weatherData?.is_forecast && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-800">
              <strong>ℹ️ Current Conditions:</strong> Selected date is today. Showing real-time weather data.
            </p>
          </div>
        )}
      </motion.div>

      {/* Current Weather - Mobile responsive */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="mb-4 sm:mb-6 p-4 sm:p-6 bg-white/80 backdrop-blur-sm rounded-xl sm:rounded-2xl shadow-lg"
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex-1 min-w-0">
            {weatherData?.is_forecast && (
              <div className="text-[10px] sm:text-xs font-semibold text-blue-600 mb-1 uppercase tracking-wider truncate">
                📅 {formatFullDate(selectedDate)} Forecast
              </div>
            )}
            {!weatherData?.is_forecast && isToday(selectedDate) && (
              <div className="text-[10px] sm:text-xs font-semibold text-green-600 mb-1 uppercase tracking-wider">
                ⚡ Real-time Current Conditions
              </div>
            )}
            <div className="text-5xl sm:text-6xl md:text-7xl font-black text-gray-800 mb-1 sm:mb-2">
              {convertTemp(current?.temperature)}{getTempUnit()}
            </div>
            <div className="text-base sm:text-lg md:text-xl text-gray-700 font-semibold mb-1 sm:mb-2 truncate">
              {current?.condition || 'Loading...'}
            </div>
            {aqi && (
              <div className="mb-1 sm:mb-2">
                <span className="text-xs sm:text-sm font-semibold text-gray-600">Air Quality: </span>
                <span className={`text-xs sm:text-sm font-bold ${
                  aqi <= 50 ? 'text-green-600' :
                  aqi <= 100 ? 'text-yellow-600' :
                  aqi <= 150 ? 'text-orange-600' :
                  aqi <= 200 ? 'text-red-600' :
                  'text-purple-600'
                }`}>AQI {Math.round(aqi)}</span>
              </div>
            )}
            <div className="flex items-center gap-3 sm:gap-4 text-gray-600 flex-wrap">
              <div className="flex items-center gap-1.5 sm:gap-2">
                <Wind size={14} className="sm:w-4 sm:h-4 flex-shrink-0" />
                <span className="text-xs sm:text-sm">{current?.wind_speed || '--'} km/h</span>
              </div>
              <div className="flex items-center gap-1.5 sm:gap-2">
                <Droplets size={14} className="sm:w-4 sm:h-4 flex-shrink-0" />
                <span className="text-xs sm:text-sm">{current?.humidity || '--'}% humidity</span>
              </div>
            </div>
          </div>
          <div className="flex-shrink-0">
            <div className="w-16 h-16 sm:w-20 sm:h-20 flex items-center justify-center">
              {getWeatherIcon(current?.condition)}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Extended Weather Metrics Grid - Horizontal Scroll */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="mb-6"
      >
        <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Thermometer className="text-blue-600" size={20} />
          Detailed Conditions
          <span className="text-xs text-gray-500 font-normal ml-2">(Scroll horizontally →)</span>
        </h3>

        {/* Horizontal scrolling container */}
        <div className="relative">
          <div className="overflow-x-auto scrollbar-thin scrollbar-thumb-blue-400 scrollbar-track-blue-100 pb-4">
            <div className="flex gap-4 min-w-max">

          {/* Feels Like Temperature */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="flex-shrink-0 w-48 p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-xl border border-orange-100 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <Thermometer className="text-orange-600" size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">Feels Like</div>
            </div>
            <div className="text-2xl font-black text-gray-800">
              {convertTemp(current?.feels_like)}{getTempUnit()}
            </div>
            <div className="text-xs text-gray-500 mt-1">Apparent temp</div>
          </motion.div>

          {/* UV Index */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.35 }}
            className={`flex-shrink-0 w-48 p-4 bg-gradient-to-br ${getUVBgColor(current?.uv_index)} rounded-xl border ${getUVBorderColor(current?.uv_index)} hover:shadow-lg transition-shadow`}
          >
            <div className="flex items-center gap-3 mb-2">
              <Sun className={getUVColor(current?.uv_index)} size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">UV Index</div>
            </div>
            <div className={`text-2xl font-black ${getUVColor(current?.uv_index)}`}>
              {current?.uv_index ?? '--'}
            </div>
            <div className="text-xs text-gray-600 mt-1 font-semibold">
              {getUVRating(current?.uv_index)}
            </div>
          </motion.div>

          {/* Visibility */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="flex-shrink-0 w-48 p-4 bg-gradient-to-br from-cyan-50 to-blue-50 rounded-xl border border-cyan-100 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <Eye className="text-cyan-600" size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">Visibility</div>
            </div>
            <div className="text-2xl font-black text-gray-800">
              {current?.visibility ?? '--'}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {current?.visibility ? 'km' : ''}
            </div>
          </motion.div>

          {/* Pressure */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.45 }}
            className="flex-shrink-0 w-48 p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-indigo-100 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <Gauge className="text-indigo-600" size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">Pressure</div>
            </div>
            <div className="text-2xl font-black text-gray-800">
              {current?.pressure ?? '--'}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {current?.pressure ? 'hPa' : ''}
            </div>
          </motion.div>

          {/* Dew Point */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="flex-shrink-0 w-48 p-4 bg-gradient-to-br from-teal-50 to-green-50 rounded-xl border border-teal-100 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <Droplets className="text-teal-600" size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">Dew Point</div>
            </div>
            <div className="text-2xl font-black text-gray-800">
              {convertTemp(current?.dew_point)}{getTempUnit()}
            </div>
            <div className="text-xs text-gray-500 mt-1">Condensation temp</div>
          </motion.div>

          {/* Cloud Cover */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.55 }}
            className="flex-shrink-0 w-48 p-4 bg-gradient-to-br from-gray-50 to-slate-100 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <CloudCog className="text-gray-600" size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">Cloud Cover</div>
            </div>
            <div className="text-2xl font-black text-gray-800">
              {current?.cloud_cover ?? '--'}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Sky coverage</div>
          </motion.div>

          {/* Wind Gust */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 }}
            className="flex-shrink-0 w-48 p-4 bg-gradient-to-br from-emerald-50 to-lime-50 rounded-xl border border-emerald-100 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <Wind className={getWindColor(current?.wind_gusts)} size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">Wind Gust</div>
            </div>
            <div className={`text-2xl font-black ${getWindColor(current?.wind_gusts)}`}>
              {current?.wind_gusts ?? '--'}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {current?.wind_gusts ? 'km/h peak' : ''}
            </div>
          </motion.div>

          {/* Precipitation */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.65 }}
            className="flex-shrink-0 w-48 p-4 bg-gradient-to-br from-blue-50 to-sky-50 rounded-xl border border-blue-100 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <CloudRain className="text-blue-600" size={24} />
              <div className="text-xs text-gray-600 font-semibold uppercase">Precipitation</div>
            </div>
            <div className="text-2xl font-black text-gray-800">
              {current?.precipitation ?? '0'}
            </div>
            <div className="text-xs text-gray-500 mt-1">mm</div>
          </motion.div>

            </div>
          </div>
          {/* Scroll hint gradient on right */}
          <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-white/90 via-white/50 to-transparent pointer-events-none rounded-r-2xl" />
        </div>
      </motion.div>

      {/* Umbrella Alert */}
      {umbrella_needed && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-6 p-5 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl shadow-lg"
        >
          <div className="flex items-center gap-4 text-white">
            <div className="p-3 bg-white/20 rounded-full">
              <Umbrella size={32} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold mb-1">Umbrella Recommended</h3>
              <p className="text-blue-50">
                {umbrella_needed.message || 'Rain expected today - bring an umbrella!'}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Rain Forecast Chart */}
      {rainChartData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-6 p-6 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg"
        >
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <CloudRain className="text-blue-600" size={20} />
            24-Hour Rain Forecast
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rainChartData}>
                <defs>
                  <linearGradient id="rainGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="hour"
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                  label={{ value: 'Probability %', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: 'none',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="probability"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#rainGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      )}

      {/* Clothing Recommendations */}
      {clothing_recommendations && clothing_recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mb-6"
        >
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Shirt className="text-purple-600" size={20} />
            What to Wear
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {clothing_recommendations.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border border-purple-100 text-center hover:shadow-lg transition-shadow"
              >
                <div className="text-4xl mb-2">{getClothingIcon(item)}</div>
                <div className="text-sm font-semibold text-gray-700">{item}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Sun & Moon Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Sunrise */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="p-4 bg-gradient-to-br from-orange-50 to-yellow-50 rounded-xl border border-orange-100"
        >
          <div className="flex items-center gap-3">
            <Sunrise className="text-orange-500" size={24} />
            <div>
              <div className="text-xs text-gray-600 font-medium">Sunrise</div>
              <div className="text-lg font-bold text-gray-800">{sunrise || '--:--'}</div>
            </div>
          </div>
        </motion.div>

        {/* Sunset */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65 }}
          className="p-4 bg-gradient-to-br from-pink-50 to-purple-50 rounded-xl border border-pink-100"
        >
          <div className="flex items-center gap-3">
            <Sunset className="text-pink-500" size={24} />
            <div>
              <div className="text-xs text-gray-600 font-medium">Sunset</div>
              <div className="text-lg font-bold text-gray-800">{sunset || '--:--'}</div>
            </div>
          </div>
        </motion.div>

        {/* Moon Phase */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="p-4 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl border border-indigo-100"
        >
          <div className="flex items-center gap-3">
            <div className="text-3xl">{moon_phase?.emoji || '🌙'}</div>
            <div>
              <div className="text-xs text-gray-600 font-medium">Moon Phase</div>
              <div className="text-sm font-bold text-gray-800 capitalize">
                {moon_phase?.name || 'Unknown'}
              </div>
              <div className="text-xs text-gray-500">
                {moon_phase?.illumination ? `${moon_phase.illumination}% lit` : ''}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default WeatherCard
