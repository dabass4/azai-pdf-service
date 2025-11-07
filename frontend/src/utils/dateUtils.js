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
    // Remove any trailing slashes or extra characters
    dateStr = dateStr.toString().trim().replace(/\/$/, '');
    
    // Handle YYYY-MM-DD format (database standard)
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      const [year, month, day] = dateStr.split('-');
      return `${parseInt(month)}/${parseInt(day)}/${year}`;
    }
    
    // Handle MM/DD/YYYY format (already correct)
    if (dateStr.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
      return dateStr;
    }
    
    // Handle MM/DD/YY format (2-digit year)
    const mmddyy = dateStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2})$/);
    if (mmddyy) {
      const [, month, day, yy] = mmddyy;
      // Convert 2-digit year: 00-30 → 2000-2030, 31-99 → 1931-1999
      const year = parseInt(yy) <= 30 ? `20${yy}` : `19${yy}`;
      return `${parseInt(month)}/${parseInt(day)}/${year}`;
    }
    
    // Handle MM-DD-YY format (with dashes)
    const mmddyyDash = dateStr.match(/^(\d{1,2})-(\d{1,2})-(\d{2})$/);
    if (mmddyyDash) {
      const [, month, day, yy] = mmddyyDash;
      const year = parseInt(yy) <= 30 ? `20${yy}` : `19${yy}`;
      return `${parseInt(month)}/${parseInt(day)}/${year}`;
    }
    
    // Handle MM-DD or MM/DD (partial date - use current year)
    const partial = dateStr.match(/^(\d{1,2})[-\/](\d{1,2})$/);
    if (partial) {
      const [, month, day] = partial;
      // Use 2024 as default year for old timesheets
      const year = 2024;
      return `${parseInt(month)}/${parseInt(day)}/${year}`;
    }
    
    // Handle MM.DD format (dot separator)
    const dotFormat = dateStr.match(/^(\d{1,2})\.(\d{1,2})$/);
    if (dotFormat) {
      const [, month, day] = dotFormat;
      const year = 2024;
      return `${parseInt(month)}/${parseInt(day)}/${year}`;
    }
    
    // Handle day names (Sunday, Monday, Mon, Tue, etc.)
    const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 
                     'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
    if (dayNames.includes(dateStr.toLowerCase().replace(/\s+\d+$/, ''))) {
      // Return as-is with note
      return `${dateStr} (Need Week Context)`;
    }
    
    // Handle single/double digit (day of month)
    if (dateStr.match(/^\d{1,2}$/)) {
      const day = parseInt(dateStr);
      if (day >= 1 && day <= 31) {
        return `?/${day}/2024 (Need Month)`;
      }
    }
    
    // Try to parse as Date object (handles various formats)
    const date = new Date(dateStr);
    if (!isNaN(date.getTime()) && date.getFullYear() > 1900 && date.getFullYear() < 2100) {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const year = date.getFullYear();
      return `${month}/${day}/${year}`;
    }
    
    // Return as-is with warning for unrecognized formats
    return `${dateStr} (Invalid Format)`;
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
