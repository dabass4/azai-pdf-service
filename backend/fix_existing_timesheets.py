"""
Fix existing timesheets with improved time normalization
Reprocesses time entries to ensure consistent 12-hour format
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
sys.path.insert(0, '/app/backend')

from time_utils import normalize_am_pm, calculate_units_from_times

async def fix_timesheets():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'timesheet_scanner')]
    
    print("="*60)
    print("FIXING EXISTING TIMESHEETS - Time Format Normalization")
    print("="*60)
    
    # Get all timesheets
    timesheets = await db.timesheets.find({}).to_list(1000)
    
    print(f"\nFound {len(timesheets)} timesheets to process\n")
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
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
                            time_in = entry.get('time_in', '')
                            time_out = entry.get('time_out', '')
                            
                            if time_in or time_out:
                                # Normalize times
                                new_time_in = normalize_am_pm(time_in) if time_in else ''
                                new_time_out = normalize_am_pm(time_out) if time_out else ''
                                
                                # Recalculate units and hours
                                units, hours = calculate_units_from_times(new_time_in, new_time_out)
                                
                                # Check if anything changed
                                if (new_time_in != time_in or 
                                    new_time_out != time_out or
                                    entry.get('units') != units):
                                    
                                    modified = True
                                    
                                    print(f"\n📝 Fixing: {filename}")
                                    print(f"   Before: {time_in} → {time_out} | {entry.get('units')} units | {entry.get('hours_worked')} hrs")
                                    print(f"   After:  {new_time_in} → {new_time_out} | {units} units | {hours} hrs")
                                    
                                    # Update entry
                                    entry['time_in'] = new_time_in
                                    entry['time_out'] = new_time_out
                                    entry['units'] = units
                                    entry['hours_worked'] = str(hours) if hours else entry.get('hours_worked')
            
            if modified:
                # Update database
                await db.timesheets.update_one(
                    {"id": ts_id},
                    {"$set": {"extracted_data": data}}
                )
                fixed_count += 1
                print(f"   ✅ Updated in database")
            else:
                skipped_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error processing {filename}: {e}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Fixed: {fixed_count}")
    print(f"⏭️  Skipped (no changes): {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total processed: {len(timesheets)}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(fix_timesheets())
