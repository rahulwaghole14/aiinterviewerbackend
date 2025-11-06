// HorizontalDatePicker.jsx
import React, { useState } from 'react';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import "./HorizontalDatePicker.css"; // The CSS import is now active.

const HorizontalDatePicker = ({ selectedDate, onSelectDate, isDateFullyBooked }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  
  // Generates a week of dates starting from `currentDate`
  const generateDates = () => {
    const dates = [];
    const startOfWeek = new Date(currentDate);
    // Set the start of the week to the current date's day
    startOfWeek.setDate(currentDate.getDate());
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      dates.push(date);
    }
    return dates;
  };
  
  const dates = generateDates();
  
  // Handles navigating to the previous week
  const handlePrevWeek = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() - 7);
    setCurrentDate(newDate);
  };
  
  // Handles navigating to the next week
  const handleNextWeek = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + 7);
    setCurrentDate(newDate);
  };
  
  // Checks if a date is the currently selected one
  const isDateSelected = (date) => {
    return selectedDate && date.toDateString() === selectedDate.toDateString();
  };
  
  // Formats the month and year for the header
  const formatMonthYear = (date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };
  
  return (
    <div className="horizontal-datepicker-container">
      <div className="horizontal-datepicker-header">
        <button className="nav-button" onClick={handlePrevWeek}>
          <FiChevronLeft size={20} />
        </button>
        <span className="month-year-display">{formatMonthYear(currentDate)}</span>
        <button className="nav-button" onClick={handleNextWeek}>
          <FiChevronRight size={20} />
        </button>
      </div>
      <div className="horizontal-days-container">
        {dates.map((date, index) => {
          const isFullyBooked = isDateFullyBooked && isDateFullyBooked(date);
          return (
            <div 
              key={index}
              className={`day-card ${isDateSelected(date) ? 'selected' : ''} ${isFullyBooked ? 'booked' : ''}`}
              onClick={() => !isFullyBooked && onSelectDate(date)}
            >
              <span className="day-name">{date.toLocaleDateString('en-US', { weekday: 'short' })}</span>
              <span className="day-number">{date.getDate()}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default HorizontalDatePicker;
