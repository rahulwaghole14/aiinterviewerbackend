# Interview Time Slots Information

## Available Time Slots (24-Hour Format)

The system supports **24-hour availability** with **10-minute interval slots**.

### Time Slot Range
- **Start Time**: 00:00 (Midnight)
- **End Time**: 23:50 (11:50 PM)
- **Last Slot**: 23:50 - 24:00 (Midnight)

### Slot Duration
- **Default Duration**: 10 minutes per slot
- **Interval**: 10 minutes between slots

### Total Slots Per Day
- **144 slots** per day (24 hours × 6 slots per hour)
- Each slot is 10 minutes long

### Example Time Slots

**Morning Slots:**
- 00:00 - 00:10
- 00:10 - 00:20
- 00:20 - 00:30
- ...
- 08:00 - 08:10 (Default start time)
- 08:10 - 08:20
- ...

**Afternoon Slots:**
- 12:00 - 12:10
- 12:10 - 12:20
- 12:20 - 12:30
- ...

**Evening/Night Slots:**
- 18:00 - 18:10
- 18:10 - 18:20
- ...
- 23:40 - 23:50
- 23:50 - 24:00 (Last slot)

### How It Works

1. **Creating Slots**: When creating a slot in the AI Interview Scheduler, you can select:
   - **Date**: Any future date
   - **Start Time**: Any time from 00:00 to 23:50 (in 10-minute intervals)
   - **End Time**: Automatically calculated as start_time + 10 minutes (or custom duration)

2. **Time Format**: All times are in **24-hour format** (00:00 to 23:59)

3. **Timezone**: Times are stored in UTC but displayed in the user's local timezone (IST/Asia/Kolkata)

### Customization

You can create slots with:
- **Custom start time**: Any time between 00:00 and 23:50
- **Custom duration**: Default is 10 minutes, but can be changed
- **Custom end time**: Must be after start time

### Important Notes

- Slots must be in the **future** (cannot create past slots)
- End time must be **after** start time
- The system prevents overlapping slots for the same company/job
- Slots are available 24/7 (no restrictions on time of day)

