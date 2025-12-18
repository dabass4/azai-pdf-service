# Medicaid Number Validation - Ohio Format

## ✅ Strict Validation Rules

### Ohio Medicaid Number Format:
**Exactly 12 digits - No exceptions**

```
Format:     DDDDDDDDDDDD
Length:     12 characters
Allowed:    0-9 (digits only)
Not Allowed: Letters, spaces, hyphens, special characters
```

---

## ✅ Valid Examples

```
✓ 000123456789
✓ 123456789012
✓ 999999999999
✓ 000000000001
```

---

## ❌ Invalid Examples

```
✗ 12345678901      (only 11 digits - too short)
✗ 1234567890123    (13 digits - too long)
✗ 12345678901A     (contains letter)
✗ 123-456-789-012  (contains hyphens)
✗ 123 456 789 012  (contains spaces)
✗ #12345678901     (contains special character)
✗ 1234567890.12    (contains decimal point)
```

---

## 🔍 Validation Logic

### Regular Expression:
```python
^\d{12}$
```

**Breakdown:**
- `^` - Start of string
- `\d{12}` - Exactly 12 digits (0-9)
- `$` - End of string

### Python Implementation:
```python
import re

def validate_medicaid_number(medicaid_number: str) -> bool:
    """
    Validate Ohio Medicaid number format.
    
    Args:
        medicaid_number: String to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Remove any whitespace
    medicaid_number = medicaid_number.strip()
    
    # Must be exactly 12 digits
    if not re.match(r'^\d{12}$', medicaid_number):
        return False
    
    return True

# Examples
validate_medicaid_number("000123456789")  # True
validate_medicaid_number("12345678901")   # False (11 digits)
validate_medicaid_number("123456789ABC")  # False (contains letters)
validate_medicaid_number("123-456-789-012")  # False (contains hyphens)
```

---

## 📋 Validation in Application

### Current Implementation:
**File:** `/app/backend/validation_utils.py`

```python
# Medicaid Number (*) - Exactly 12 digits for Ohio
medicaid = patient.get('medicaid_number', '').strip()
if not medicaid or medicaid == '':
    errors.append("Medicaid Number * is required (ODM & EVV)")
elif not re.match(r'^\d{12}$', medicaid):
    errors.append("Medicaid Number must be exactly 12 digits (no letters or special characters)")
```

### Error Messages:
```
Missing:
  "Medicaid Number * is required (ODM & EVV)"

Invalid Format:
  "Medicaid Number must be exactly 12 digits (no letters or special characters)"
```

---

## 🎯 User Input Handling

### Frontend Recommendations:

**1. Input Field Configuration:**
```html
<input 
  type="text" 
  pattern="[0-9]{12}"
  maxlength="12"
  minlength="12"
  inputmode="numeric"
  placeholder="000123456789"
  required
/>
```

**2. Real-time Validation:**
```javascript
function validateMedicaidNumber(value) {
  // Remove any non-digit characters
  const cleaned = value.replace(/\D/g, '');
  
  // Check if exactly 12 digits
  if (cleaned.length !== 12) {
    return {
      valid: false,
      message: "Must be exactly 12 digits"
    };
  }
  
  return { valid: true };
}
```

**3. Auto-format on Paste:**
```javascript
function handleMedicaidPaste(event) {
  event.preventDefault();
  
  // Get pasted text
  const pastedText = event.clipboardData.getData('text');
  
  // Extract only digits
  const digitsOnly = pastedText.replace(/\D/g, '');
  
  // Take first 12 digits
  const medicaidNumber = digitsOnly.substring(0, 12);
  
  // Set in input field
  event.target.value = medicaidNumber;
  
  // Validate
  if (medicaidNumber.length === 12) {
    showSuccess("Valid Medicaid number");
  } else {
    showError("Must be exactly 12 digits");
  }
}
```

**4. Character Filtering:**
```javascript
function filterMedicaidInput(event) {
  const key = event.key;
  
  // Allow only digits 0-9
  if (!/^\d$/.test(key) && 
      key !== 'Backspace' && 
      key !== 'Delete' && 
      key !== 'Tab' &&
      key !== 'ArrowLeft' &&
      key !== 'ArrowRight') {
    event.preventDefault();
  }
  
  // Prevent input if already 12 characters
  if (event.target.value.length >= 12 && 
      key !== 'Backspace' && 
      key !== 'Delete') {
    event.preventDefault();
  }
}
```

---

## 🧪 Test Cases

### Backend Validation Tests:

```python
def test_medicaid_number_validation():
    """Test Medicaid number validation"""
    
    # Valid cases
    assert validate_medicaid_number("000123456789") == True
    assert validate_medicaid_number("123456789012") == True
    assert validate_medicaid_number("999999999999") == True
    
    # Invalid - wrong length
    assert validate_medicaid_number("12345678901") == False  # 11 digits
    assert validate_medicaid_number("1234567890123") == False  # 13 digits
    
    # Invalid - contains letters
    assert validate_medicaid_number("12345678901A") == False
    assert validate_medicaid_number("A12345678901") == False
    
    # Invalid - contains special characters
    assert validate_medicaid_number("123-456-789-012") == False
    assert validate_medicaid_number("123 456 789 012") == False
    assert validate_medicaid_number("123.456.789.012") == False
    
    # Invalid - empty or None
    assert validate_medicaid_number("") == False
    assert validate_medicaid_number(None) == False
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: User enters hyphens or spaces
**User Input:** `123-456-789-012`

**Solution:**
```python
# Strip out non-digits before validation
medicaid = ''.join(filter(str.isdigit, medicaid_input))
# Result: "123456789012" ✓
```

### Issue 2: User copies with leading/trailing spaces
**User Input:** `  123456789012  `

**Solution:**
```python
# Always strip whitespace
medicaid = medicaid_input.strip()
# Result: "123456789012" ✓
```

### Issue 3: Leading zeros removed
**User Input:** `123456789` (system adds leading zeros to make 12)

**Bad Solution:** ❌ Auto-padding
```python
medicaid = medicaid_input.zfill(12)  # DON'T DO THIS
# User entered 9 digits, this makes it 12 by adding 000
# But it might not be the correct Medicaid number!
```

**Good Solution:** ✅ Require full 12 digits
```python
if len(medicaid) != 12:
    return error("Must be exactly 12 digits")
# User must enter the complete number with leading zeros
```

### Issue 4: Pasted from document with formatting
**User Input:** `12-3456-7890-12`

**Solution:**
```python
# Extract only digits
medicaid = re.sub(r'\D', '', medicaid_input)
# Result: "123456789012" ✓
```

---

## 📊 Data Sanitization

### Before Validation:
```python
def sanitize_medicaid_number(raw_input: str) -> str:
    """
    Clean medicaid number input before validation.
    
    Returns:
        String with only digits, or original if None
    """
    if raw_input is None:
        return ''
    
    # Convert to string if not already
    raw_input = str(raw_input)
    
    # Strip whitespace
    cleaned = raw_input.strip()
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', cleaned)
    
    return digits_only

# Example usage
user_input = "123-456-789-012"
clean = sanitize_medicaid_number(user_input)  # "123456789012"
is_valid = validate_medicaid_number(clean)     # True
```

---

## 🎯 UI/UX Recommendations

### Input Field Design:
```
┌─────────────────────────────────────────┐
│ Medicaid Number *                       │
│ ┌─────────────────────────────────────┐ │
│ │ 000123456789                        │ │
│ └─────────────────────────────────────┘ │
│ Must be exactly 12 digits               │
│ Example: 000123456789                   │
└─────────────────────────────────────────┘
```

### Validation States:

**Empty:**
```
[________________________]
ℹ️ Required - 12 digits only
```

**Typing (< 12 digits):**
```
[123456789_______________]
⏳ 9/12 digits entered
```

**Valid (12 digits):**
```
[123456789012]
✅ Valid Medicaid number
```

**Invalid (letters):**
```
[123456789ABC]
❌ Must be exactly 12 digits (no letters or special characters)
```

**Invalid (too short):**
```
[12345678901]
❌ Must be exactly 12 digits (11 entered)
```

---

## 📖 Why This Matters

### For ODM Claims:
- Medicaid number is the primary identifier
- Must match exactly with Ohio Medicaid database
- Claims rejected if format is incorrect
- No manual correction possible once submitted

### For EVV:
- Used for patient identification
- Must match across all systems
- Ensures proper visit tracking
- Required for service authorization

### For Billing:
- Direct link to patient account
- Determines payment eligibility
- Must be valid for claim processing
- Affects reimbursement timing

---

## 🔐 Security Note

**Medicaid numbers are PHI (Protected Health Information)**

### Handling Requirements:
- ✅ Encrypt in transit (HTTPS)
- ✅ Encrypt at rest (database)
- ✅ Mask in UI (show last 4 digits)
- ✅ Log access (audit trail)
- ✅ Restrict access (role-based)

### Display Format:
```
Full View (admin only):  123456789012
Masked View (default):   ********9012
```

---

## 📝 Summary

**Ohio Medicaid Number Requirements:**
- ✅ Exactly 12 digits
- ✅ Digits only (0-9)
- ✅ No letters
- ✅ No spaces
- ✅ No hyphens
- ✅ No special characters
- ✅ Leading zeros included
- ✅ Required for all claims
- ✅ Required for EVV

**Validation:** `^\d{12}$`

**Example:** `000123456789`

---

**Updated:** December 2024  
**Applies to:** Ohio Medicaid only  
**Status:** Enforced in `/app/backend/validation_utils.py`
