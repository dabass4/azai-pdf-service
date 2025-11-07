/**
 * Date formatting utilities for consistent date display
 */

/**
 * Format date from YYYY-MM-DD to MM/DD/YYYY
 * @param {string} dateStr - Date string in YYYY-MM-DD format
 * @returns {string} Formatted date in MM/DD/YYYY format
 */
export const formatDateForDisplay = (dateStr) => {
  if (!dateStr) return "N/A";
  
  try {
    // Handle YYYY-MM-DD format
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      const [year, month, day] = dateStr.split('-');
      return `${parseInt(month)}/${parseInt(day)}/${year}`;
    }
    
    // Handle MM/DD/YYYY format (already formatted)
    if (dateStr.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
      return dateStr;
    }
    
    // Handle MM-DD or other partial formats
    if (dateStr.match(/^\d{1,2}[-\/]\d{1,2}$/)) {
      const separator = dateStr.includes('/') ? '/' : '-';
      const [month, day] = dateStr.split(separator);
      const year = new Date().getFullYear();
      return `${parseInt(month)}/${parseInt(day)}/${year}`;
    }
    
    // Try to parse as Date object
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const year = date.getFullYear();
      return `${month}/${day}/${year}`;
    }
    
    // Return as-is if can't parse
    return dateStr;
  } catch (error) {
    console.error('Date formatting error:', error);
    return dateStr;
  }
};

/**
 * Format date from MM/DD/YYYY to YYYY-MM-DD for backend
 * @param {string} dateStr - Date string in MM/DD/YYYY format
 * @returns {string} Formatted date in YYYY-MM-DD format
 */
export const formatDateForBackend = (dateStr) => {
  if (!dateStr) return '';
  
  try {
    // Handle MM/DD/YYYY format
    if (dateStr.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
      const [month, day, year] = dateStr.split('/');
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    
    // Handle YYYY-MM-DD format (already formatted)
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return dateStr;
    }
    
    // Try to parse as Date object
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }
    
    return dateStr;
  } catch (error) {
    console.error('Date formatting error:', error);
    return dateStr;
  }
};

/**
 * Parse week range string and return formatted start/end dates
 * @param {string} weekStr - Week string (e.g., "Week of 10/6/2024")
 * @returns {object} Object with start and end dates in MM/DD/YYYY format
 */
export const parseWeekRange = (weekStr) => {
  if (!weekStr) return null;
  
  try {
    // Match "10/6/2024 - 10/12/2024" format
    const rangeMatch = weekStr.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})\s*[-–]\s*(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    if (rangeMatch) {
      const [, m1, d1, y1, m2, d2, y2] = rangeMatch;
      return {
        start: `${parseInt(m1)}/${parseInt(d1)}/${y1}`,
        end: `${parseInt(m2)}/${parseInt(d2)}/${y2}`
      };
    }
    
    // Match "Week of 10/6/2024" format
    const weekOfMatch = weekStr.match(/week\s+of\s+(\d{1,2})\/(\d{1,2})\/(\d{4})/i);
    if (weekOfMatch) {
      const [, month, day, year] = weekOfMatch;
      const startDate = new Date(year, month - 1, day);
      const endDate = new Date(startDate);
      endDate.setDate(endDate.getDate() + 6);
      
      return {
        start: `${startDate.getMonth() + 1}/${startDate.getDate()}/${startDate.getFullYear()}`,
        end: `${endDate.getMonth() + 1}/${endDate.getDate()}/${endDate.getFullYear()}`
      };
    }
    
    return null;
  } catch (error) {
    console.error('Week range parsing error:', error);
    return null;
  }
};
