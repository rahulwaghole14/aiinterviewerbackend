import React, { useState, useEffect } from 'react';
import './TimePicker12.css';

const TimePicker12 = ({ value, onChange, placeholder = "Select time" }) => {
  const [hour, setHour] = useState(9);
  const [minute, setMinute] = useState(0);
  const [ampm, setAmpm] = useState('AM');

  // Parse the initial value when component mounts or value changes
  useEffect(() => {
    if (value) {
      try {
        let parsedHour, parsedMinute, parsedAmpm;
        
        if (value.includes('M')) {
          // 12-hour format like "5:45 PM"
          const timeParts = value.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
          if (timeParts) {
            parsedHour = parseInt(timeParts[1]);
            parsedMinute = parseInt(timeParts[2]);
            parsedAmpm = timeParts[3].toUpperCase();
          }
        } else {
          // 24-hour format like "17:45:00" - convert to 12-hour
          const [hours, minutes] = value.split(':');
          const hour24 = parseInt(hours);
          parsedMinute = parseInt(minutes);
          
          if (hour24 === 0) {
            parsedHour = 12;
            parsedAmpm = 'AM';
          } else if (hour24 < 12) {
            parsedHour = hour24;
            parsedAmpm = 'AM';
          } else if (hour24 === 12) {
            parsedHour = 12;
            parsedAmpm = 'PM';
          } else {
            parsedHour = hour24 - 12;
            parsedAmpm = 'PM';
          }
        }
        
        if (parsedHour && parsedMinute !== undefined && parsedAmpm) {
          setHour(parsedHour);
          setMinute(parsedMinute);
          setAmpm(parsedAmpm);
        }
      } catch (error) {
        console.error('Error parsing time value:', error);
      }
    }
  }, [value]);

  const handleChange = (newHour, newMinute, newAmpm) => {
    const timeString = `${newHour}:${newMinute.toString().padStart(2, '0')} ${newAmpm}`;
    onChange(timeString);
  };

  const handleHourChange = (e) => {
    const newHour = parseInt(e.target.value);
    setHour(newHour);
    handleChange(newHour, minute, ampm);
  };

  const handleMinuteChange = (e) => {
    const newMinute = parseInt(e.target.value);
    setMinute(newMinute);
    handleChange(hour, newMinute, ampm);
  };

  const handleAmpmChange = (e) => {
    const newAmpm = e.target.value;
    setAmpm(newAmpm);
    handleChange(hour, minute, newAmpm);
  };

  return (
    <div className="time-picker-inline edit-input">
      <select 
        value={hour} 
        onChange={handleHourChange}
        className="time-select hour-select"
      >
        {Array.from({ length: 12 }, (_, i) => i + 1).map(h => (
          <option key={h} value={h}>{h}</option>
        ))}
      </select>
      
      <span className="time-separator">:</span>
      
      <select 
        value={minute} 
        onChange={handleMinuteChange}
        className="time-select minute-select"
      >
        {[0, 15, 30, 45].map(m => (
          <option key={m} value={m}>
            {m.toString().padStart(2, '0')}
          </option>
        ))}
      </select>
      
      <select 
        value={ampm} 
        onChange={handleAmpmChange}
        className="time-select ampm-select"
      >
        <option value="AM">AM</option>
        <option value="PM">PM</option>
      </select>
    </div>
  );
};

export default TimePicker12;
