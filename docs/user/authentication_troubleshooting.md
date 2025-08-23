# Authentication Troubleshooting Guide

## Overview

This guide helps you resolve common authentication and session issues. The system provides intelligent error messages to guide you through most problems, but this document offers additional context and solutions.

## Common Issues and Solutions

### 1. Getting Logged Out When Refreshing the Page

**Problem:** You log in successfully, but when you refresh the page or navigate back to the application, you're asked to log in again.

**Intelligent Error Message:**
> **Session Expired**
> Your session has expired. Please log in again to continue.
> 
> **What you can do:**
> - Click the login button to sign in again
> - Your work will be saved automatically

**Solutions:**

1. **Check Browser Settings**
   - Ensure cookies are enabled in your browser
   - Check if you're in private/incognito mode (sessions don't persist)
   - Verify that third-party cookies aren't blocked

2. **Clear Browser Data**
   ```
   1. Open browser settings
   2. Go to Privacy/Security section
   3. Clear cookies and site data for this domain
   4. Try logging in again
   ```

3. **Check Network Connection**
   - Ensure stable internet connection
   - Try refreshing the page after a few seconds
   - Check if you're behind a corporate firewall

4. **Browser Compatibility**
   - Use a modern browser (Chrome 90+, Firefox 88+, Safari 14+)
   - Disable browser extensions that might interfere
   - Try a different browser to isolate the issue

### 2. "API Key Missing" Errors

**Problem:** You see errors about missing API keys when trying to use AI features.

**Intelligent Error Messages:**

**OpenAI API Key Missing:**
> **OpenAI API Key Missing**
> OpenAI API key is missing from your configuration
> 
> **What you can do:**
> - Add OPENAI_API_KEY to your .env file
> - Get your API key from https://platform.openai.com/api-keys
> - Restart the application after adding the key

**Anthropic API Key Missing:**
> **Anthropic API Key Missing**
> Anthropic API key is missing from your configuration
> 
> **What you can do:**
> - Add ANTHROPIC_API_KEY to your .env file
> - Get your API key from https://console.anthropic.com
> - Restart the application after adding the key

**Solutions:**

1. **For Users (Self-hosted):**
   ```bash
   # Edit your .env file
   nano .env
   
   # Add the missing API key
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   
   # Restart the application
   docker-compose restart
   ```

2. **For Managed Hosting Users:**
   - Contact your system administrator
   - Provide them with the specific error message
   - They will need to configure the API keys on the server

3. **Getting API Keys:**
   - **OpenAI**: Visit https://platform.openai.com/api-keys
   - **Anthropic**: Visit https://console.anthropic.com
   - **Note**: You'll need to create accounts and may need to add billing information

### 3. Rate Limit Exceeded

**Problem:** You're making too many requests and hitting rate limits.

**Intelligent Error Message:**
> **Rate Limit Exceeded**
> You've exceeded the rate limit for API requests
> 
> **What you can do:**
> - Wait 5 minutes before trying again
> - Consider upgrading your plan for higher limits
> - Reduce the frequency of your requests

**Solutions:**

1. **Wait and Retry**
   - The error message will tell you exactly how long to wait
   - Don't keep trying immediately - this will extend the wait time

2. **Upgrade Your Plan**
   - Check your API provider's pricing page
   - Upgrade to a higher tier for increased limits
   - Consider pay-per-use plans if available

3. **Optimize Usage**
   - Batch multiple requests together when possible
   - Cache responses to avoid repeated requests
   - Use shorter prompts when appropriate

### 4. Invalid Login Credentials

**Problem:** You can't log in with your username and password.

**Intelligent Error Message:**
> **Invalid Login Credentials**
> The email or password you entered is incorrect
> 
> **What you can do:**
> - Double-check your email address and password
> - Use the 'Forgot Password' link if you can't remember your password
> - Contact admin if you continue having trouble

**Solutions:**

1. **Verify Credentials**
   - Check for typos in email address
   - Ensure Caps Lock is off
   - Try typing password in a text editor first to verify

2. **Password Reset**
   - Use the "Forgot Password" link on the login page
   - Check your email for reset instructions
   - Follow the link to create a new password

3. **Account Issues**
   - Your account might be locked after too many failed attempts
   - Contact your system administrator
   - Wait 15 minutes if you've been rate limited

### 5. Database Connection Errors

**Problem:** You see errors about database connections or missing tables.

**Intelligent Error Messages:**

**Database Connection Failed:**
> **Database Connection Failed**
> Unable to connect to the database
> 
> **What you can do:**
> - Contact admin immediately
> - This is a system-level issue that requires technical support

**Database Not Initialized:**
> **Database Not Initialized**
> The database is not properly initialized
> 
> **What you can do:**
> - Contact admin to run database migrations
> - The system needs to be properly set up

**Solutions:**

1. **For Users:**
   - This is a system administration issue
   - Contact your IT support or system administrator
   - Provide them with the exact error message
   - Don't attempt to fix this yourself

2. **For Administrators:**
   ```bash
   # Check database connection
   python scripts/validate_database_connection.py
   
   # Run database migrations
   python scripts/run_migrations.py
   
   # Initialize database schema
   python create_tables.py
   ```

### 6. Service Temporarily Unavailable

**Problem:** External AI services (OpenAI, Anthropic) are down or unavailable.

**Intelligent Error Message:**
> **Service Temporarily Unavailable**
> The OpenAI service is currently unavailable
> 
> **What you can do:**
> - Try again in a few minutes
> - Check https://status.openai.com for service updates
> - Consider using an alternative provider if available

**Solutions:**

1. **Wait and Retry**
   - Service outages are usually temporary
   - Check the provider's status page for updates
   - Try again after the suggested wait time

2. **Use Alternative Providers**
   - Switch to Anthropic if OpenAI is down
   - Switch to OpenAI if Anthropic is down
   - Check if local models are available

3. **Check Provider Status**
   - **OpenAI**: https://status.openai.com
   - **Anthropic**: https://status.anthropic.com
   - Follow their social media for updates

### 7. Network and Connection Issues

**Problem:** Requests are timing out or failing due to network issues.

**Intelligent Error Message:**
> **Request Timeout**
> The request took too long to complete
> 
> **What you can do:**
> - Check your internet connection
> - Try again in a moment
> - Contact admin if the problem persists

**Solutions:**

1. **Check Your Connection**
   - Test internet connectivity
   - Try accessing other websites
   - Restart your router if needed

2. **Network Configuration**
   - Check if you're behind a corporate firewall
   - Verify proxy settings if applicable
   - Try connecting from a different network

3. **Browser Issues**
   - Clear browser cache and cookies
   - Disable VPN temporarily
   - Try a different browser

## Advanced Troubleshooting

### Browser Developer Tools

1. **Open Developer Tools**
   - Press F12 or right-click → "Inspect"
   - Go to the "Network" tab
   - Try the action that's failing

2. **Check for Errors**
   - Look for red entries in the Network tab
   - Check the "Console" tab for JavaScript errors
   - Note any 401, 403, 429, or 500 status codes

3. **Examine Cookies**
   - Go to "Application" tab → "Cookies"
   - Look for `refresh_token` and `session_token`
   - Check if they have proper expiration dates

### Session Storage Debugging

1. **Check Local Storage**
   - Open Developer Tools → "Application" tab
   - Look under "Local Storage" for your domain
   - Verify access token is present (if applicable)

2. **Clear Session Data**
   ```javascript
   // In browser console
   localStorage.clear();
   sessionStorage.clear();
   
   // Clear cookies for this domain
   document.cookie.split(";").forEach(function(c) { 
     document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
   });
   ```

### Network Debugging

1. **Check Request Headers**
   - Look for `Authorization: Bearer ...` header
   - Verify `Cookie` header contains session tokens
   - Check `Content-Type` is correct

2. **Examine Response Headers**
   - Look for `X-New-Access-Token` header
   - Check `Set-Cookie` headers
   - Note any CORS-related headers

## Getting Help

### When to Contact Support

Contact your system administrator or support team when you see:

- **Critical severity errors** (red indicators)
- **"Contact admin" messages** in error responses
- **Database or system-level errors**
- **Persistent issues** after trying suggested solutions

### Information to Provide

When contacting support, include:

1. **Exact Error Message**
   - Copy the complete error text
   - Include any error codes or technical details

2. **Steps to Reproduce**
   - What you were trying to do
   - Exact sequence of actions
   - When the error first appeared

3. **Environment Information**
   - Browser name and version
   - Operating system
   - Network environment (home, office, mobile)

4. **Screenshots**
   - Error messages
   - Browser developer tools (if comfortable)
   - Any relevant UI states

### Self-Service Resources

1. **Documentation**
   - API Documentation: `/docs/api/authentication_api.md`
   - System Architecture: `/docs/architecture.md`
   - Deployment Guide: `/docs/deployment.md`

2. **Health Checks**
   - Visit `/auth/health` to check system status
   - Look for any configuration issues
   - Note any warnings or recommendations

3. **Community Resources**
   - Check GitHub issues for similar problems
   - Search community forums
   - Review changelog for recent updates

## Prevention Tips

### Best Practices

1. **Browser Hygiene**
   - Keep your browser updated
   - Regularly clear cache and cookies
   - Don't use too many browser extensions

2. **Network Stability**
   - Use stable internet connections
   - Avoid switching networks during sessions
   - Consider using ethernet instead of WiFi for important work

3. **Account Security**
   - Use strong, unique passwords
   - Don't share login credentials
   - Log out when using shared computers

4. **System Maintenance**
   - Keep the application updated
   - Monitor system health regularly
   - Backup important data

### Monitoring Your Session

1. **Watch for Warning Signs**
   - Slow response times
   - Intermittent login issues
   - Unusual error messages

2. **Regular Maintenance**
   - Clear browser data weekly
   - Check for application updates
   - Verify API key validity

3. **Performance Optimization**
   - Close unused browser tabs
   - Restart browser periodically
   - Monitor system resource usage

## Emergency Procedures

### Complete System Reset

If you're experiencing persistent issues:

1. **Clear All Browser Data**
   ```
   1. Open browser settings
   2. Go to Privacy/Security
   3. Choose "Clear all data" or "Reset browser"
   4. Restart browser
   ```

2. **Reset Application State**
   - Log out completely
   - Clear all cookies for the domain
   - Close all browser tabs
   - Wait 5 minutes
   - Try logging in again

3. **Alternative Access Methods**
   - Try a different browser
   - Use incognito/private mode temporarily
   - Access from a different device
   - Use mobile app if available

### Escalation Path

1. **Level 1**: Try solutions in this guide
2. **Level 2**: Contact your local IT support
3. **Level 3**: Contact system administrator
4. **Level 4**: Contact application vendor support

Remember: The system provides intelligent error messages to guide you through most issues. Always read the error message carefully and follow the suggested next steps before escalating to support.