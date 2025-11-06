import React, { useState, useEffect, useRef, useCallback } from "react";
import PropTypes from "prop-types";
import { useSelector } from "react-redux";
import { baseURL } from "../config/constants";
import { useNotification } from "../hooks/useNotification";
import { formatTimeTo12Hour, formatTimeRange } from "../utils/timeFormatting";
import "./TimeSlotPicker.css";

const TimeSlotPicker = ({
  selectedTimes = [],
  onSelectTimes = () => {},
  selectedDate,
  isBooking = false,
  setIsBooking = () => {},
  onAvailableSlotsChange = () => {},
  onAllSlotsChange = () => {},
  aiInterviewType = "technical",
  isModal = false,
}) => {
  const notify = useNotification();
  const [localSelectedTimes, setLocalSelectedTimes] = useState(selectedTimes);
  const isCtrlPressed = useRef(false);
  const lastClickedTimeRef = useRef(null);

  const [availableSlotsInternal, setAvailableSlotsInternal] = useState([]);
  const [bookedSlots, setBookedSlots] = useState([]);
  const [allSlotsInternal, setAllSlotsInternal] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const user = useSelector((state) => state.user?.user);

  // Generate time slots for 24 hours in 10-minute intervals
  const generateTimeSlots = () => {
    const slots = [];
    for (let hour = 0; hour <= 23; hour++) {
      const maxMinute = 60;
      for (let minute = 0; minute < maxMinute; minute += 10) {
        const startTime = `${String(hour).padStart(2, "0")}:${String(
          minute
        ).padStart(2, "0")}`;
        
        // Calculate end time (10 minutes later)
        let endHour = hour;
        let endMinute = minute + 10;
        
        if (endMinute >= 60) {
          endHour += 1;
          endMinute -= 60;
        }
        
        // Wrap around to next day hour but still allow displaying the closing segment
        if (endHour >= 24) {
          break;
        }
        
        const endTime = `${String(endHour).padStart(2, "0")}:${String(
          endMinute
        ).padStart(2, "0")}`;
        const timeRange = `${startTime}-${endTime}`;
        slots.push(timeRange);
      }
    }
    return slots;
  };

  // Generate all possible time slots
  const allTimeSlots = generateTimeSlots();

  // Fetch all slots from API for specific date with role-based filtering
  const fetchAllSlots = useCallback(async () => {
    if (!selectedDate) return;

    try {
      setIsLoading(true);
      const authToken = localStorage.getItem("authToken");
      if (!authToken) return;

      const formattedDate = selectedDate.toISOString().split("T")[0];

      // Build query parameters based on user role
      const queryParams = new URLSearchParams({
        date: formattedDate,
      });

      // If user is company, add company_id filter
      if (user?.role === "company" || user?.user_type === "company") {
        const companyId = user?.company_id || user?.id;
        if (companyId) {
          queryParams.append("company_id", companyId);
        }
      }

      console.log("Fetching all slots for date:", formattedDate);

      // Build the URLs properly
      const availableURL = `${baseURL}/api/interviews/slots/?${queryParams}&status=available`;
      const bookedURL = `${baseURL}/api/interviews/slots/?${queryParams}&status=booked`;

      console.log("Available URL:", availableURL);
      console.log("Booked URL:", bookedURL);

      // Fetch available and booked slots separately with proper status filtering
      const [availableResponse, bookedResponse] = await Promise.all([
        fetch(availableURL, {
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
        }),
        fetch(bookedURL, {
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
        }),
      ]);

      const available = [];
      const booked = [];

      console.log("Available response status:", availableResponse.status);
      console.log("Booked response status:", bookedResponse.status);

      if (availableResponse.ok) {
        const availableData = await availableResponse.json();
        console.log("Available response data:", availableData);
        const availableSlots = availableData.results || availableData || [];

        console.log(
          "Available slots response:",
          availableSlots.length,
          "slots"
        );
        console.log("Looking for date:", formattedDate);

        // Use Map to store unique time ranges with their metadata
        const availableTimeRanges = new Map();

        availableSlots.forEach((slot) => {
          console.log(
            "Processing slot:",
            slot.id,
            "interview_date:",
            slot.interview_date,
            "start_time:",
            slot.start_time,
            "end_time:",
            slot.end_time,
            "status:",
            slot.status
          );
          if (slot.interview_date && slot.start_time && slot.end_time) {
            // Use interview_date directly since it's now a separate field
            const slotDate = slot.interview_date;
            console.log(
              "Slot date:",
              slotDate,
              "vs selected:",
              formattedDate,
              "match:",
              slotDate === formattedDate
            );

            if (slotDate === formattedDate) {
              // Since start_time and end_time are now TimeField (e.g., "09:00:00"), extract HH:MM
              const startTime = slot.start_time.substring(0, 5); // "09:00:00" -> "09:00"
              const endTime = slot.end_time.substring(0, 5); // "10:30:00" -> "10:30"

              if (startTime && endTime) {
                const timeRange = `${startTime}-${endTime}`;

                // If this time range already exists, combine the capacities
                if (availableTimeRanges.has(timeRange)) {
                  const existing = availableTimeRanges.get(timeRange);
                  existing.totalCapacity += slot.max_candidates || 1;
                  existing.currentBookings += slot.current_bookings || 0;
                  existing.slots.push(slot);
                } else {
                  availableTimeRanges.set(timeRange, {
                    timeRange,
                    totalCapacity: slot.max_candidates || 1,
                    currentBookings: slot.current_bookings || 0,
                    availableSpots: slot.available_spots || 1,
                    aiInterviewType: slot.ai_interview_type,
                    slots: [slot],
                  });
                }

                console.log("Adding/updating available time range:", timeRange);
              }
            }
          }
        });

        // Extract just the time ranges for the available array
        available.push(...Array.from(availableTimeRanges.keys()));

        // Store the detailed slot information for later use
        window.slotDetails = availableTimeRanges;
      } else {
        console.error(
          "Available response not ok:",
          availableResponse.status,
          await availableResponse.text()
        );
      }

      if (bookedResponse.ok) {
        const bookedData = await bookedResponse.json();
        console.log("Booked response data:", bookedData);
        const bookedSlots = bookedData.results || bookedData || [];

        console.log("Booked slots response:", bookedSlots.length, "slots");

        const bookedTimeRanges = new Set(); // Use Set to avoid duplicates

        bookedSlots.forEach((slot) => {
          console.log(
            "Processing booked slot:",
            slot.id,
            "interview_date:",
            slot.interview_date,
            "start_time:",
            slot.start_time,
            "end_time:",
            slot.end_time,
            "status:",
            slot.status
          );
          if (slot.interview_date && slot.start_time && slot.end_time) {
            // Use interview_date directly since it's now a separate field
            const slotDate = slot.interview_date;
            console.log(
              "Booked slot date:",
              slotDate,
              "vs selected:",
              formattedDate,
              "match:",
              slotDate === formattedDate
            );

            if (slotDate === formattedDate) {
              // Since start_time and end_time are now TimeField (e.g., "09:00:00"), extract HH:MM
              const startTime = slot.start_time.substring(0, 5); // "09:00:00" -> "09:00"
              const endTime = slot.end_time.substring(0, 5); // "10:30:00" -> "10:30"

              if (startTime && endTime) {
                const timeRange = `${startTime}-${endTime}`;
                console.log("Adding booked time range:", timeRange);
                bookedTimeRanges.add(timeRange);
              }
            }
          }
        });

        booked.push(...Array.from(bookedTimeRanges));
      } else {
        console.error(
          "Booked response not ok:",
          bookedResponse.status,
          await bookedResponse.text()
        );
      }

      console.log("Processed slots - Available:", available, "Booked:", booked);

      setAvailableSlotsInternal(available);
      setBookedSlots(booked);

      // Combine all slots for reference
      const allSlotsData = [...available, ...booked];
      setAllSlotsInternal(allSlotsData);

      // Notify parent components of changes
      onAvailableSlotsChange(available);
      onAllSlotsChange(allSlotsData);
    } catch (error) {
      console.error("Error fetching slots:", error);
      notify.error(error.message || "Failed to fetch available slots");
    } finally {
      setIsLoading(false);
    }
  }, [selectedDate, user, baseURL]);

  useEffect(() => {
    setLocalSelectedTimes(selectedTimes || []);
  }, [selectedTimes]);

  useEffect(() => {
    fetchAllSlots();
  }, [selectedDate, fetchAllSlots]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Control") {
        isCtrlPressed.current = true;
      }
    };

    const handleKeyUp = (event) => {
      if (event.key === "Control") {
        isCtrlPressed.current = false;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  // Book an interview slot
  const bookSlot = async (slotId, bookingData) => {
    try {
      console.log("=== TIME SLOT PICKER - SLOT BOOKING ===");
      console.log("Booking slot ID:", slotId);
      console.log("Booking data:", bookingData);
      
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        throw new Error("Authentication token not found");
      }

      // First, get the current slot data to check bookings
      console.log("Fetching current slot data...");
      const slotResponse = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/`,
        {
          method: "GET",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!slotResponse.ok) {
        throw new Error(`Failed to fetch slot data: ${slotResponse.status}`);
      }

      const slotData = await slotResponse.json();
      console.log("Current slot data:", slotData);
      
      const currentBookings = slotData.current_bookings || 0;
      const maxCandidates = slotData.max_candidates || 1;
      
      console.log("Slot booking details:", {
        current_bookings: currentBookings,
        max_candidates: maxCandidates,
        start_time: slotData.start_time,
        end_time: slotData.end_time,
        status: slotData.status
      });
      
      // Update slot booking based on current bookings
      let updateData;
      if (currentBookings >= maxCandidates - 1) {
        // If this is the last available slot, mark as booked
        updateData = {
          current_bookings: maxCandidates,
          status: "booked"
        };
        console.log("Slot will be marked as BOOKED (max candidates reached)");
      } else {
        // Otherwise, just increment current_bookings
        updateData = {
          current_bookings: currentBookings + 1
        };
        console.log("Slot booking count will be incremented");
      }

      console.log("=== SLOT UPDATE PROCESS ===");
      console.log(`Updating slot ${slotId}:`, updateData);
      console.log(`Before update - current_bookings: ${currentBookings}, max_candidates: ${maxCandidates}`);

      // Merge the update data with complete slot data
      const fullUpdateData = {
        ...slotData,
        ...updateData
      };

      console.log("Full update data (merged):", fullUpdateData);
      console.log("Update data being sent:", updateData);

      // Update the slot using PUT method
      console.log("Sending PUT request to update slot...");
      const updateResponse = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/`,
        {
          method: "PUT",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(fullUpdateData),
        }
      );

      console.log("Slot update response status:", updateResponse.status);
      console.log("Slot update response headers:", Object.fromEntries(updateResponse.headers.entries()));

      if (!updateResponse.ok) {
        const errorData = await updateResponse.json().catch(() => ({}));
        console.error("=== SLOT UPDATE FAILED ===");
        console.error("Failed to update slot:", errorData);
        console.error("Response status:", updateResponse.status);
        throw new Error(`Failed to update slot: ${updateResponse.status}`);
      } else {
        const updatedSlotData = await updateResponse.json();
        console.log("=== SLOT UPDATE SUCCESS ===");
        console.log("Slot updated successfully:", updatedSlotData);
        console.log(`After update - current_bookings: ${updatedSlotData.current_bookings}, status: ${updatedSlotData.status}`);
        console.log("Updated slot times:", {
          start_time: updatedSlotData.start_time,
          end_time: updatedSlotData.end_time
        });
      }

      // Create the schedule relationship
      console.log("=== CREATING SCHEDULE RELATIONSHIP ===");
      console.log("Sending booking data:", bookingData);
      
      const response = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/book_slot/`,
        {
          method: "POST",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(bookingData),
        }
      );

      console.log("Schedule creation response status:", response.status);
      console.log("Schedule creation response headers:", Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("=== SCHEDULE CREATION FAILED ===");
        console.error("Failed to create schedule relationship:", errorData);
        console.error("Response status:", response.status);
        throw new Error(`Failed to book slot: ${response.status}`);
      }

      const scheduleResult = await response.json();
      console.log("=== SCHEDULE CREATION SUCCESS ===");
      console.log("Schedule relationship created:", scheduleResult);
      
      return scheduleResult;
    } catch (error) {
      console.error("Error booking interview slot:", error);
      throw error;
    }
  };

  // Release an interview slot
  const releaseSlot = async (slotId) => {
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        throw new Error("Authentication token not found");
      }

      // First, get the current slot data to check bookings
      const slotResponse = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/`,
        {
          method: "GET",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!slotResponse.ok) {
        throw new Error(`Failed to fetch slot data: ${slotResponse.status}`);
      }

      const slotData = await slotResponse.json();
      const currentBookings = slotData.current_bookings || 0;
      const maxCandidates = slotData.max_candidates || 1;
      
      // Update slot booking based on current bookings
      let updateData;
      if (currentBookings <= 1) {
        // If this was the last booking, mark as available
        updateData = {
          current_bookings: 0,
          status: "available"
        };
      } else {
        // Otherwise, just decrement current_bookings
        updateData = {
          current_bookings: currentBookings - 1
        };
      }

      console.log(`Releasing slot ${slotId}:`, updateData);

      // Merge the update data with complete slot data
      const fullUpdateData = {
        ...slotData,
        ...updateData
      };

      console.log("Full release update data:", fullUpdateData);

      // Update the slot using PUT method
      const updateResponse = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/`,
        {
          method: "PUT",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(fullUpdateData),
        }
      );

      if (!updateResponse.ok) {
        throw new Error(`Failed to update slot: ${updateResponse.status}`);
      }

      // Also call the release_slot endpoint for cleanup
      const response = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/release_slot/`,
        {
          method: "POST",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to release slot: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error releasing interview slot:", error);
      throw error;
    }
  };

  // Create a new interview slot
  const createSlot = async (slotData) => {
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        throw new Error("Authentication token not found");
      }

      const response = await fetch(`${baseURL}/api/interviews/slots/`, {
        method: "POST",
        headers: {
          Authorization: `Token ${authToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(slotData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create slot: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error creating interview slot:", error);
      throw error;
    }
  };

  // Update an existing interview slot
  const updateSlot = async (slotId, slotData) => {
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        throw new Error("Authentication token not found");
      }

      const response = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/`,
        {
          method: "PUT",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(slotData),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update slot: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error updating interview slot:", error);
      throw error;
    }
  };

  // Delete an interview slot
  const deleteSlot = async (slotId) => {
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        throw new Error("Authentication token not found");
      }

      const response = await fetch(
        `${baseURL}/api/interviews/slots/${slotId}/`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to delete slot: ${response.status}`);
      }

      return true;
    } catch (error) {
      console.error("Error deleting interview slot:", error);
      throw error;
    }
  };

  // Use shared time formatting utility
  const formatTimeForDisplayInBox = formatTimeRange;

  const calculateDuration = (startTime, endTime) => {
    // Handle time range format (e.g., "09:00-09:30")
    if (startTime.includes("-")) {
      const [start, end] = startTime.split("-");
      const [startHour, startMin] = start.split(":").map(Number);
      const [endHour, endMin] = end.split(":").map(Number);
      
      const startTotalMin = startHour * 60 + startMin;
      const endTotalMin = endHour * 60 + endMin;
      
      return endTotalMin - startTotalMin;
    }
    
    // Handle separate start and end times
    const [startHour, startMin] = startTime.split(":").map(Number);
    const [endHour, endMin] = endTime.split(":").map(Number);

    const startTotalMin = startHour * 60 + startMin;
    const endTotalMin = endHour * 60 + endMin;

    return endTotalMin - startTotalMin;
  };

  const handleSlotClick = async (time, event) => {
    console.log("=== TIMESLOTPICKER CLICK DEBUG ===");
    console.log("Clicked time:", time);
    console.log("Current selectedTimes:", localSelectedTimes);
    console.log("Available slots:", availableSlotsInternal);
    console.log("Booked slots:", bookedSlots);
    
    let newSelectedTimes = [...localSelectedTimes];
    const isCtrlHeld = event?.ctrlKey || event?.metaKey;
    const isAvailable = availableSlotsInternal.includes(time);
    const isBooked = bookedSlots.includes(time);
    const isNewSlot = !isAvailable && !isBooked;
    const selectionModeAvailable = isModal || isBooking;
    
    console.log("isAvailable:", isAvailable, "isBooked:", isBooked, "isNewSlot:", isNewSlot);

    // Selection gating: when booking (or modal), allow only available slots; otherwise allow creating new slots
    if (selectionModeAvailable) {
      if (!isAvailable) return;
    } else {
      if (!isNewSlot) return;
    }

    if (selectionModeAvailable) {
      // When booking or in modal, always single-select the available slot
      newSelectedTimes = [time];
    } else if (isCtrlHeld) {
      // Multi-select mode for creating new slots
      if (newSelectedTimes.includes(time)) {
        newSelectedTimes = newSelectedTimes.filter((t) => t !== time);
      } else {
        newSelectedTimes.push(time);
      }
    } else {
      // Single-select mode for creating new slots
      newSelectedTimes = [time];
    }

    lastClickedTimeRef.current = time;
    newSelectedTimes.sort();
    setLocalSelectedTimes(newSelectedTimes);

    // Calculate duration based on selected times
    let duration = 0;
    if (newSelectedTimes.length > 0) {
      const timeRange = newSelectedTimes[0]; // This is a time range like "09:00-09:30"
      duration = calculateDuration(timeRange, null); // Pass the time range directly
    }

    console.log("=== CALLING onSelectTimes ===");
    console.log("newSelectedTimes:", newSelectedTimes);
    console.log("duration:", duration);
    onSelectTimes(newSelectedTimes, duration);
  };

  if (isLoading) {
    return <div className="slots-loading">Loading available time slots...</div>;
  }


  // Combine all actual slots from API data
  const allActualSlots = [
    ...new Set([...availableSlotsInternal, ...bookedSlots]),
  ];

  // Always show generated time slots alongside API data to allow creating new slots
  const allGeneratedSlots = generateTimeSlots();
  const combinedSlots = [...new Set([...allActualSlots, ...allGeneratedSlots])];

  // Sort slots by time for better display
  const slotsToDisplay = combinedSlots.sort((a, b) => {
    const timeA = a.split("-")[0];
    const timeB = b.split("-")[0];
    return timeA.localeCompare(timeB);
  });

  const slotElements = slotsToDisplay.map((time) => {
    const isSelected = localSelectedTimes.includes(time);
    const isAvailable = availableSlotsInternal.includes(time);
    const isBooked = bookedSlots.includes(time);
    const isNewSlot = !isAvailable && !isBooked;

    const displayTime = formatTimeForDisplayInBox(time);

    // Get slot details if available
    const slotDetail = window.slotDetails?.get(time);
    const capacityInfo = slotDetail
      ? `${slotDetail.currentBookings}/${slotDetail.totalCapacity}`
      : "";
    const interviewType = slotDetail?.aiInterviewType || "";

    let slotClass = "time-slot";
    let tooltipText = "";
    let statusLabel = "";
    let isClickable = false;

    if (isBooked) {
      slotClass += " booked";
      tooltipText = "This slot is already booked";
      statusLabel = "BOOKED";
      isClickable = false;
    } else if (isAvailable) {
      slotClass += " available";
      tooltipText = `Available slot${
        capacityInfo ? ` (${capacityInfo} capacity)` : ""
      }${interviewType ? ` - ${interviewType}` : ""}`;
      statusLabel = "AVAILABLE";
      isClickable = true;
    } else {
      slotClass += " new-slot";
      tooltipText = isModal
        ? "Not available for selection"
        : "New slot (can be created)";
      statusLabel = isModal ? "UNAVAILABLE" : "NEW";
      isClickable = !isModal; // Only clickable in non-modal mode
    }

    if (isSelected) {
      slotClass += " selected";
    }

    // Add disabled class for non-clickable slots
    if (!isClickable) {
      slotClass += " disabled";
    }

    return (
      <div key={time} className="slot-container">
        <div className="slot-time-label">{displayTime}</div>
        <div
          className={slotClass}
          onClick={isClickable ? (e) => handleSlotClick(time, e) : undefined}
          title={tooltipText}
          style={{ cursor: isClickable ? "pointer" : "not-allowed" }}
        >
          <div className="slot-status-main">{statusLabel}</div>
          <div className="slot-capacity-main">
            {!isNewSlot ? capacityInfo : ""}
          </div>
          {interviewType && (
            <div className="slot-type-main">{interviewType}</div>
          )}
        </div>
      </div>
    );
  });

  return (
    <div className="time-slot-picker-wrapper">
      <div className="time-slot-picker-scroll-container">
        <div className="time-slot-picker-scroll-area">{slotElements}</div>
      </div>
    </div>
  );
};

TimeSlotPicker.propTypes = {
  selectedTimes: PropTypes.arrayOf(PropTypes.string),
  onSelectTimes: PropTypes.func,
  selectedDate: PropTypes.instanceOf(Date).isRequired,
  baseURL: PropTypes.string,
  isBooking: PropTypes.bool,
  setIsBooking: PropTypes.func,
  onAvailableSlotsChange: PropTypes.func,
  onAllSlotsChange: PropTypes.func,
  aiInterviewType: PropTypes.string,
  isModal: PropTypes.bool,
};

export default TimeSlotPicker;
