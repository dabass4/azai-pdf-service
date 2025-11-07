"""
Normalize ALL times in database to consistent format
Cleans up 374+ different time formats to standard 00:00 AM/PM
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
import re

sys.path.insert(0, '/app/backend')
from time_utils import normalize_am_pm, parse_time_string

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'timesheet_scanner')

def clean_malformed_time(time_str):
    """
    Clean obviously malformed time entries
    Returns cleaned version or None if unrecoverable
    """
    if not time_str or time_str in ['-', 'Missed', 'unabl', 'unable', 'K']:
        return None
    
    time_str = str(time_str).strip()
    
    # Remove obvious OCR garbage
    if len(time_str) > 20 or any(c in time_str for c in ['円', 'px', 'Sile', 'BBAL', 'GZS']):
        return None
    
    # Fix common OCR errors
    time_str = time_str.replace('O', '0').replace('o', '0')  # O → 0
    time_str = time_str.replace('l', '1').replace('I', '1')  # l/I → 1
    time_str = time_str.replace('S', '5').replace('s', '5')  # S → 5
    time_str = time_str.replace('B', '8').replace('b', '8')  # B → 8
    time_str = time_str.replace('Z', '2').replace('z', '2')  # Z → 2
    time_str = time_str.replace('G', '6').replace('g', '6')  # G → 6
    
    # Fix common separators
    time_str = time_str.replace('.', ':')  # 8.30 → 8:30
    time_str = time_str.replace(',', ':')  # 8,30 → 8:30
    time_str = time_str.replace(';', ':')  # 8;30 → 8:30
    time_str = time_str.replace('/', ':')  # 8/30 → 8:30
    
    # Remove extra spaces and newlines
    time_str = ' '.join(time_str.split())
    
    # Fix malformed AM/PM
    time_str = time_str.replace('pn', 'pm').replace('pri', 'pm').replace('pm', ' PM')
    time_str = time_str.replace('am', ' AM').replace('AM', ' AM').replace('PM', ' PM')
    time_str = re.sub(r'\s+', ' ', time_str)  # Multiple spaces to single
    
    # Remove trailing/leading special chars
    time_str = re.sub(r'[^\d:APMapm\s]', '', time_str)
    
    return time_str.strip() or None


def normalize_time_comprehensive(time_str):
    """
    Comprehensive time normalization to 00:00 AM/PM format
    Handles 400+ different time formats
    """
    if not time_str:
        return None
    
    # Clean malformed entries first
    time_str = clean_malformed_time(time_str)
    if not time_str:
        return None
    
    try:
        # Try existing normalize_am_pm first
        result = normalize_am_pm(time_str)
        
        # Check if result is valid (has : and AM/PM)
        if ':' in result and ('AM' in result or 'PM' in result):
            # Check for invalid hours (>23 or minutes >59)
            match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', result)
            if match:
                hour, minute, am_pm = match.groups()
                hour, minute = int(hour), int(minute)
                
                # Fix invalid hours
                if hour > 12:
                    hour = hour % 12
                    if hour == 0:
                        hour = 12
                
                # Fix invalid minutes
                if minute > 59:
                    minute = 59
                
                return f"{hour:02d}:{minute:02d} {am_pm}"
            
            return result
        
        return None
        
    except Exception as e:
        print(f"Error normalizing '{time_str}': {e}")
        return None


async def normalize_all_times():
    """Normalize all times in the database"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("="*60)
    print("NORMALIZING ALL TIMES IN DATABASE")
    print("="*60)
    
    timesheets = await db.timesheets.find({}).to_list(2000)
    
    total_timesheets = len(timesheets)
    updated_count = 0
    failed_count = 0
    skipped_count = 0
    null_time_count = 0
    
    print(f"\nProcessing {total_timesheets} timesheets...\n")
    
    for ts in timesheets:
        ts_id = ts.get('id')
        filename = ts.get('filename', 'Unknown')
        
        try:
            extracted = ts.get('extracted_data')
            if not extracted:
                skipped_count += 1
                continue
            
            modified = False
            
            if extracted.get('employee_entries'):
                for emp in extracted['employee_entries']:
                    if emp.get('time_entries'):
                        for entry in emp['time_entries']:
                            time_in = entry.get('time_in')
                            time_out = entry.get('time_out')
                            
                            # Normalize time_in
                            if time_in:
                                normalized_in = normalize_time_comprehensive(time_in)
                                if normalized_in and normalized_in != time_in:
                                    entry['time_in'] = normalized_in
                                    modified = True
                                    print(f"✅ {filename}: IN '{time_in}' → '{normalized_in}'")
                                elif not normalized_in:
                                    entry['time_in'] = None
                                    null_time_count += 1
                                    print(f"⚠️  {filename}: Removed invalid time_in '{time_in}'")
                                    modified = True
                            
                            # Normalize time_out
                            if time_out:
                                normalized_out = normalize_time_comprehensive(time_out)
                                if normalized_out and normalized_out != time_out:
                                    entry['time_out'] = normalized_out
                                    modified = True
                                    print(f"✅ {filename}: OUT '{time_out}' → '{normalized_out}'")
                                elif not normalized_out:
                                    entry['time_out'] = None
                                    null_time_count += 1
                                    print(f"⚠️  {filename}: Removed invalid time_out '{time_out}'")
                                    modified = True
            
            if modified:
                # Update database
                await db.timesheets.update_one(
                    {"id": ts_id},
                    {"$set": {"extracted_data": extracted}}
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
    print(f"⚠️  Nulled invalid times: {null_time_count}")
    print(f"⏭️  Skipped: {skipped_count} (no changes needed)")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total processed: {total_timesheets}")
    print("="*60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(normalize_all_times())
