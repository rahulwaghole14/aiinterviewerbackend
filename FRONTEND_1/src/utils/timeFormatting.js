// Shared time formatting utilities for consistent time display across all components

/**
 * Convert 24-hour time string to 12-hour format for display
 * @param {string} timeStr - Time string in format "HH:MM" or "HH:MM:SS"
 * @returns {string} - Formatted time string like "9:00 AM" or "2:30 PM"
 */
export const formatTimeTo12Hour = (timeStr) => {
  if (!timeStr || typeof timeStr !== 'string') {
    return 'N/A';
  }

  // Extract hours and minutes (handle both "HH:MM" and "HH:MM:SS" formats)
  const [hourStr, minuteStr] = timeStr.split(':');
  let hour = parseInt(hourStr, 10);
  const minutes = parseInt(minuteStr, 10);
  
  // Convert to 12-hour format
  const ampm = hour >= 12 ? "PM" : "AM";
  hour = hour % 12;
  hour = hour ? hour : 12; // Handle midnight (0) and noon (12)
  const minuteStr2 = minutes < 10 ? "0" + minutes : minutes;
  
  return `${hour}:${minuteStr2} ${ampm}`;
};

/**
 * Convert 12-hour time string to 24-hour format for API
 * @param {string} time12Str - Time string in format "9:00 AM" or "2:30 PM"
 * @returns {string} - 24-hour format like "09:00" or "14:30"
 */
export const formatTimeTo24Hour = (time12Str) => {
  if (!time12Str || typeof time12Str !== 'string') {
    return '';
  }

  try {
    // Parse 12-hour time format
    const timeParts = time12Str.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
    if (!timeParts) {
      throw new Error('Invalid time format');
    }
    
    let hours = parseInt(timeParts[1]);
    const minutes = timeParts[2];
    const ampm = timeParts[3].toUpperCase();
    
    // Convert to 24-hour format
    if (ampm === 'PM' && hours !== 12) {
      hours += 12;
    } else if (ampm === 'AM' && hours === 12) {
      hours = 0;
    }
    
    return `${hours.toString().padStart(2, '0')}:${minutes}`;
  } catch (error) {
    console.error('Error converting 12-hour to 24-hour format:', error);
    return '';
  }
};

/**
 * Format time range for display (e.g., "09:00-09:30" -> "9:00 AM - 9:30 AM")
 * @param {string} timeRange - Time range string like "09:00-09:30"
 * @returns {string} - Formatted time range like "9:00 AM - 9:30 AM"
 */
export const formatTimeRange = (timeRange) => {
  if (!timeRange || typeof timeRange !== 'string') {
    return '';
  }

  // Handle time range format (e.g., "09:00-09:30")
  if (timeRange.includes("-")) {
    const [startTime, endTime] = timeRange.split("-");
    return `${formatTimeTo12Hour(startTime)} - ${formatTimeTo12Hour(endTime)}`;
  }

  // Fallback for single time format
  return formatTimeTo12Hour(timeRange);
};

/**
 * Parse time range from string (e.g., "09:00-09:30" -> {start: "09:00", end: "09:30"})
 * @param {string} timeRange - Time range string like "09:00-09:30"
 * @returns {object} - Object with start and end times
 */
export const parseTimeRange = (timeRange) => {
  if (!timeRange || typeof timeRange !== 'string') {
    return { start: '', end: '' };
  }

  if (timeRange.includes("-")) {
    const [start, end] = timeRange.split("-");
    return { start: start.trim(), end: end.trim() };
  }

  return { start: timeRange.trim(), end: '' };
};
