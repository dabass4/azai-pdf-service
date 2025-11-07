"""
Normalize ALL dates in database to consistent YYYY-MM-DD format
Run this to clean up the 158 different date formats
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, '/app/backend')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'timesheet_scanner')

def normalize_date_string(date_str, week_context=None):
    """
    Normalize any date format to YYYY-MM-DD
    
    Args:
        date_str: Date string in any format
        week_context: Optional tuple of (start_date, end_date) for context
    
    Returns:
        Normalized YYYY-MM-DD string or None if can't parse
    """
    if not date_str:
        return None
    
    date_str = str(date_str).strip().replace('/', '').replace('\\', '')
    
    try:
        # Already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # YYYY-MM-DD with slashes: 2024/10/06
        match = re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # MM/DD/YYYY or MM-DD-YYYY
        match = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', date_str)
        if match:
            month, day, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # MM/DD/YY or MM-DD-YY (2-digit year)
        match = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{2})$', date_str)
        if match:
            month, day, yy = match.groups()
            year = int(yy)
            # 00-30 → 2000-2030, 31-99 → 1931-1999
            full_year = 2000 + year if year <= 30 else 1900 + year
            return f"{full_year}-{int(month):02d}-{int(day):02d}"
        
        # MM-DD or MM/DD (no year - use 2024)
        match = re.match(r'^(\d{1,2})[/-](\d{1,2})$', date_str)
        if match:
            month, day = match.groups()
            return f"2024-{int(month):02d}-{int(day):02d}"
        
        # MM.DD (dot separator)
        match = re.match(r'^(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            month, day = match.groups()
            return f"2024-{int(month):02d}-{int(day):02d}"
        
        # Single or double digit day number
        if re.match(r'^\d{1,2}$', date_str):
            day = int(date_str)
            if 1 <= day <= 31:
                # Use October 2024 as default
                return f"2024-10-{day:02d}"
        
        # 4-digit number like "1015" -> 10/15
        if re.match(r'^\d{4}$', date_str):
            month = int(date_str[:2])
            day = int(date_str[2:])
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"2024-{month:02d}-{day:02d}"
        
        # Day names - can't normalize without week context
        day_names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
                     'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        if any(day_name in date_str.lower() for day_name in day_names):
            return None  # Can't normalize day names without week context
        
        return None
        
    except Exception as e:
        print(f"Error normalizing date '{date_str}': {e}")
        return None


async def normalize_all_dates():
    """Normalize all dates in the database"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("="*60)
    print("NORMALIZING ALL DATES IN DATABASE")
    print("="*60)
    
    timesheets = await db.timesheets.find({}).to_list(2000)
    
    total_timesheets = len(timesheets)
    updated_count = 0
    failed_count = 0
    skipped_count = 0
    
    print(f"\nProcessing {total_timesheets} timesheets...\n")
    
    for ts in timesheets:
        ts_id = ts.get('id')
        filename = ts.get('filename', 'Unknown')
        
        try:
            if not ts.get('extracted_data'):
                skipped_count += 1
                continue
            
            data = ts['extracted_data']
            modified = False
            
            if data.get('employee_entries'):
                for emp in data['employee_entries']:
                    if emp.get('time_entries'):
                        for entry in emp['time_entries']:
                            original_date = entry.get('date')
                            
                            if original_date:
                                normalized_date = normalize_date_string(original_date)
                                
                                if normalized_date and normalized_date != original_date:
                                    entry['date'] = normalized_date
                                    modified = True
                                    print(f"✅ {filename}: '{original_date}' → '{normalized_date}'")
            
            if modified:
                # Update database
                await db.timesheets.update_one(
                    {"id": ts_id},
                    {"$set": {"extracted_data": data}}
                )
                updated_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            failed_count += 1
            print(f"❌ Error processing {filename}: {e}")
    
    print("\n" + "="*60)
    print("NORMALIZATION COMPLETE")
    print("="*60)
    print(f"✅ Updated: {updated_count} timesheets")
    print(f"⏭️  Skipped: {skipped_count} (no changes needed)")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total processed: {total_timesheets}")
    print("="*60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(normalize_all_dates())
