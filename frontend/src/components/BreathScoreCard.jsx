/**
 * BreathScoreCard Component
 *
 * Display breath quality score with:
 * - Large circular progress indicator (0-100)
 * - Color-coded by score
 * - Mask recommendation
 * - Age-specific guidance
 * - Risk factors
 * - Outdoor activity recommendations
 */

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import CountUp from 'react-countup'
import {
  Activity,
  AlertTriangle,
  Shield,
  Users,
  Baby,
  Heart,
  Wind,
  Sun,
  Moon,
  ChevronDown,
  CheckCircle,
  XCircle
} from 'lucide-react'

const BreathScoreCard = ({ breathData, loading }) => {
  const [selectedAge, setSelectedAge] = useState('adults')

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-3xl p-8 border border-blue-100 shadow-xl">
        <div className="animate-pulse">
          <div className="h-8 bg-blue-200 rounded w-1/3 mb-6" />
          <div className="h-48 bg-blue-200 rounded-full w-48 mx-auto mb-6" />
          <div className="h-6 bg-blue-200 rounded w-2/3 mx-auto" />
        </div>
      </div>
    )
  }

  if (!breathData) return null

  // Map backend field names to frontend variables
  const score = breathData.breath_score || 0
  const category = breathData.rating || 'Unknown'
  const mask_recommendation = breathData.mask || {}
  const age_guidance = breathData.age_guidance || {}
  const risk_factors = breathData.risk_factors || []
  const outdoor_activities = breathData.outdoor_activity || {}

  // Color scheme based on score
  const getScoreColor = (score) => {
    if (score >= 80) return { bg: 'from-green-400 to-emerald-500', text: 'text-green-600', ring: 'stroke-green-500' }
    if (score >= 60) return { bg: 'from-yellow-400 to-amber-500', text: 'text-yellow-600', ring: 'stroke-yellow-500' }
    if (score >= 40) return { bg: 'from-orange-400 to-red-500', text: 'text-orange-600', ring: 'stroke-orange-500' }
    return { bg: 'from-red-500 to-purple-600', text: 'text-red-600', ring: 'stroke-red-500' }
  }

  const colors = getScoreColor(score)
  const circumference = 2 * Math.PI * 85
  const offset = circumference - (score / 100) * circumference

  const ageGroups = [
    { id: 'adults', label: 'General Public', icon: Users },
    { id: 'children', label: 'Children', icon: Baby },
    { id: 'seniors', label: 'Elderly', icon: Heart },
    { id: 'sensitive', label: 'Sensitive Groups', icon: AlertTriangle }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="bg-gradient-to-br from-white via-blue-50 to-purple-50 rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8 border border-blue-100 shadow-2xl"
    >
      {/* Header - Mobile responsive */}
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <div>
          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-2 sm:gap-3">
            <Activity className="text-blue-600" size={24} />
            <span className="hidden sm:inline">Breath Quality Score</span>
            <span className="sm:hidden">Breath Score</span>
          </h2>
          <p className="text-gray-600 mt-1 text-xs sm:text-sm md:text-base">Personalized 0-100 health metric</p>
          <p className="text-gray-500 text-[10px] sm:text-xs mt-1">
            Based on AQI, weather, wildfires, and health impact factors
          </p>
        </div>
      </div>

      {/* Score Scale Reference - Mobile responsive */}
      <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-white rounded-xl sm:rounded-2xl shadow-md border border-gray-100">
        <h3 className="text-xs sm:text-sm font-bold text-gray-700 mb-2 sm:mb-3 flex items-center gap-2">
          <Activity size={14} className="text-gray-600 sm:w-4 sm:h-4" />
          What does my score mean?
        </h3>
        <div className="space-y-1 sm:space-y-1.5">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-12 h-5 sm:w-16 sm:h-6 bg-gradient-to-r from-green-400 to-emerald-500 rounded flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] sm:text-xs font-bold text-white">81-100</span>
            </div>
            <span className="text-[10px] sm:text-xs md:text-sm text-gray-700 font-medium">Excellent - Perfect for outdoor activities</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-12 h-5 sm:w-16 sm:h-6 bg-gradient-to-r from-yellow-400 to-amber-500 rounded flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] sm:text-xs font-bold text-white">61-80</span>
            </div>
            <span className="text-[10px] sm:text-xs md:text-sm text-gray-700 font-medium">Good - Safe for most people</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-12 h-5 sm:w-16 sm:h-6 bg-gradient-to-r from-orange-400 to-red-500 rounded flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] sm:text-xs font-bold text-white">41-60</span>
            </div>
            <span className="text-[10px] sm:text-xs md:text-sm text-gray-700 font-medium">Moderate - Sensitive groups should limit exposure</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-12 h-5 sm:w-16 sm:h-6 bg-gradient-to-r from-red-500 to-purple-600 rounded flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] sm:text-xs font-bold text-white">0-40</span>
            </div>
            <span className="text-[10px] sm:text-xs md:text-sm text-gray-700 font-medium">Unhealthy - Everyone should reduce outdoor activity</span>
          </div>
        </div>
      </div>

      {/* Score Circle - Mobile responsive */}
      <div className="flex flex-col items-center mb-6 sm:mb-8">
        <div className="relative">
          {/* Background circle - smaller on mobile */}
          <svg className="w-48 h-48 sm:w-56 sm:h-56 md:w-64 md:h-64 transform -rotate-90">
            <circle
              cx="96"
              cy="96"
              r="70"
              stroke="#e5e7eb"
              strokeWidth="12"
              fill="transparent"
              className="sm:cx-112 sm:cy-112 sm:r-75 md:cx-128 md:cy-128 md:r-85 sm:stroke-[14] md:stroke-[16]"
            />
            {/* Progress circle */}
            <motion.circle
              cx="96"
              cy="96"
              r="70"
              className={`${colors.ring} sm:cx-112 sm:cy-112 sm:r-75 md:cx-128 md:cy-128 md:r-85 sm:stroke-[14] md:stroke-[16]`}
              strokeWidth="12"
              fill="transparent"
              strokeLinecap="round"
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: offset }}
              transition={{ duration: 1.5, ease: 'easeOut' }}
              style={{
                strokeDasharray: circumference,
              }}
            />
          </svg>

          {/* Score number - responsive sizing */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className={`text-4xl sm:text-5xl md:text-6xl font-black ${colors.text}`}>
              <CountUp end={score} duration={1.5} />
            </div>
            <div className="text-gray-600 font-semibold mt-1 sm:mt-2 text-xs sm:text-sm md:text-base">out of 100</div>
          </div>
        </div>

        {/* Category - responsive sizing */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.8, type: 'spring' }}
          className={`mt-4 sm:mt-6 px-6 py-2 sm:px-8 sm:py-3 bg-gradient-to-r ${colors.bg} text-white rounded-full text-base sm:text-lg md:text-xl font-bold shadow-lg`}
        >
          {category}
        </motion.div>

        {/* Score Explanation - responsive text */}
        <div className="mt-3 sm:mt-4 text-center max-w-md px-2">
          <p className="text-xs sm:text-sm text-gray-600">
            This score combines air quality (AQI), weather conditions, and health factors to give you a simple 0-100 rating.
            <span className="font-semibold"> Higher is better!</span>
          </p>
        </div>
      </div>

      {/* Mask Recommendation */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-6 p-6 bg-white rounded-2xl shadow-md border border-gray-100"
      >
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-full ${mask_recommendation?.required ? 'bg-orange-100' : 'bg-green-100'}`}>
            <Shield className={mask_recommendation?.required ? 'text-orange-600' : 'text-green-600'} size={28} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-800 mb-2">Mask Recommendation</h3>
            <p className="text-gray-700 mb-2">{mask_recommendation?.message || 'No mask needed - air quality is good!'}</p>
            {mask_recommendation?.type && (
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg">
                <CheckCircle size={16} className="text-blue-600" />
                <span className="text-sm font-semibold text-blue-800">Recommended: {mask_recommendation.type}</span>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Age-Specific Guidance Tabs - Mobile responsive */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.4 }}
        className="mb-4 sm:mb-6"
      >
        <h3 className="text-base sm:text-lg font-bold text-gray-800 mb-3 sm:mb-4">Health Guidance by Group</h3>

        {/* Age group selector - better mobile grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3 sm:mb-4">
          {ageGroups.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setSelectedAge(id)}
              className={`flex items-center justify-center gap-1.5 sm:gap-2 px-2 py-2 sm:px-4 sm:py-3 rounded-lg sm:rounded-xl font-semibold transition-all text-xs sm:text-sm ${
                selectedAge === id
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 active:bg-gray-300'
              }`}
            >
              <Icon size={16} className="sm:w-[18px] sm:h-[18px] flex-shrink-0" />
              <span className="truncate">{label}</span>
            </button>
          ))}
        </div>

        {/* Age-specific content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedAge}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-100"
          >
            <p className="text-gray-800 leading-relaxed">
              {age_guidance?.[selectedAge] || `Guidance for ${selectedAge} group not available.`}
            </p>
          </motion.div>
        </AnimatePresence>
      </motion.div>

      {/* Risk Factors */}
      {risk_factors && risk_factors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="mb-6 p-6 bg-red-50 rounded-2xl border border-red-100"
        >
          <h3 className="text-lg font-bold text-red-800 mb-3 flex items-center gap-2">
            <AlertTriangle className="text-red-600" size={20} />
            Risk Factors
          </h3>
          <ul className="space-y-2">
            {risk_factors.map((factor, index) => (
              <li key={index} className="flex items-start gap-2 text-gray-700">
                <XCircle size={16} className="text-red-500 mt-1 flex-shrink-0" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      {/* Outdoor Activities */}
      {outdoor_activities && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="p-6 bg-green-50 rounded-2xl border border-green-100"
        >
          <h3 className="text-lg font-bold text-green-800 mb-3 flex items-center gap-2">
            <Sun className="text-green-600" size={20} />
            Outdoor Activity Recommendations
          </h3>
          <div className="space-y-3">
            {outdoor_activities.morning && (
              <div className="flex items-start gap-3">
                <Sun size={18} className="text-yellow-500 mt-1 flex-shrink-0" />
                <div>
                  <div className="font-semibold text-gray-800">Morning</div>
                  <div className="text-sm text-gray-700">{outdoor_activities.morning}</div>
                </div>
              </div>
            )}
            {outdoor_activities.afternoon && (
              <div className="flex items-start gap-3">
                <Sun size={18} className="text-orange-500 mt-1 flex-shrink-0" />
                <div>
                  <div className="font-semibold text-gray-800">Afternoon</div>
                  <div className="text-sm text-gray-700">{outdoor_activities.afternoon}</div>
                </div>
              </div>
            )}
            {outdoor_activities.evening && (
              <div className="flex items-start gap-3">
                <Moon size={18} className="text-indigo-500 mt-1 flex-shrink-0" />
                <div>
                  <div className="font-semibold text-gray-800">Evening</div>
                  <div className="text-sm text-gray-700">{outdoor_activities.evening}</div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default BreathScoreCard
