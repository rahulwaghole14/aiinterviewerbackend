// Convert 24-hour time format to 12-hour format
export const convertTo12HourFormat = (time24) => {
  if (!time24) return '';
  const [hours, minutes] = time24.split(':');
  let hours12 = parseInt(hours, 10);
  const ampm = hours12 >= 12 ? 'PM' : 'AM';
  hours12 = hours12 % 12 || 12;
  return `${hours12}:${minutes} ${ampm}`;
};
