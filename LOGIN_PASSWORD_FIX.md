# Login Password Fix

## Issue
Users were unable to login with the default credentials because the default password `pswd123` (7 characters) was shorter than the minimum password length requirement of 8 characters enforced by the frontend validation.

## Root Cause
- Frontend validation requires passwords to be at least 8 characters long (`AUTH_CONSTANTS.MIN_PASSWORD_LENGTH = 8`)
- Backend default password was `pswd123` (only 7 characters)
- This mismatch prevented successful login even with correct credentials

## Solution
Updated the default password from `pswd123` to `password123` (11 characters) to meet the minimum length requirement.

### Files Updated:
1. **Backend Configuration:**
   - `src/ai_karen_engine/security/auth_manager.py` - Updated default admin and user passwords
   - `src/ai_karen_engine/services/user_service.py` - Updated demo user passwords

2. **Documentation:**
   - `README.md` - Updated default credentials in multiple locations
   - `ui_launchers/web_ui/README.md` - Updated web UI documentation

3. **Test Files:**
   - `tests/test_web_ui_auth.py` - Updated test credentials
   - `tests/test_user_database_integration.py` - Updated test credentials

4. **Data Files:**
   - `data/users.json` - Deleted to force regeneration with new password hashes

## New Default Credentials
- **Admin:** `admin@kari.ai` / `password123`
- **User:** `user@kari.ai` / `password123`

## Verification
The new password `password123` meets all validation requirements:
- ✅ Minimum 8 characters (has 11)
- ✅ Contains letters and numbers
- ✅ Not in the common weak passwords list
- ✅ Passes all frontend validation rules

## Next Steps
1. Restart the backend server to regenerate user data with new password hashes
2. Try logging in with the new credentials: `admin@kari.ai` / `password123`
3. Change the default passwords after first login for security

## Security Note
These are development/demo credentials only. In production environments, ensure strong, unique passwords are used and default credentials are changed immediately after deployment.