// Simple test to check if server is accessible
const { chromium } = require('playwright');

async function testServer() {
  console.log('🚀 Starting simple server test...');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    console.log('📡 Connecting to http://localhost:8000...');
    await page.goto('http://localhost:8000', { timeout: 10000 });
    
    console.log('✅ Successfully connected to server');
    
    // Check if login page loads
    console.log('🔍 Checking for login page...');
    await page.goto('http://localhost:8000/login', { timeout: 10000 });
    
    const title = await page.title();
    console.log('📄 Page title:', title);
    
    // Check if login form exists
    const emailInput = await page.$('input#email');
    const passwordInput = await page.$('input#password');
    const submitButton = await page.$('[data-testid="submit-button"]');
    
    console.log('🔍 Login form elements:');
    console.log('  - Email input:', emailInput ? '✅ Found' : '❌ Not found');
    console.log('  - Password input:', passwordInput ? '✅ Found' : '❌ Not found');
    console.log('  - Submit button:', submitButton ? '✅ Found' : '❌ Not found');
    
    if (emailInput && passwordInput && submitButton) {
      console.log('🎯 Attempting login...');
      await emailInput.fill('admin@example.com');
      await passwordInput.fill('password123');
      await submitButton.click();
      
      // Wait a bit to see what happens
      await page.waitForTimeout(3000);
      
      const currentUrl = page.url();
      console.log('🌐 Current URL after login attempt:', currentUrl);
      
      if (currentUrl !== 'http://localhost:8000/login') {
        console.log('✅ Login appears to have redirected (success?)');
        
        // Check for chat interface
        const chatInput = await page.$('#chat-input input[aria-label="Type your message"]');
        console.log('💬 Chat input found:', chatInput ? '✅ Yes' : '❌ No');
        
        if (chatInput) {
          console.log('🧮 Testing math question...');
          await chatInput.fill('What is 4 + 4?');
          
          const chatSubmit = await page.$('#chat-input button[type="submit"]');
          if (chatSubmit) {
            await chatSubmit.click();
            console.log('📤 Math question submitted');
            
            // Wait for response
            await page.waitForTimeout(5000);
            
            const messages = await page.$$eval('[role="article"] p', elements => 
              elements.map(el => el.textContent || '')
            );
            
            console.log('💬 Chat messages:', messages);
            
            const hasEight = messages.some(text => /\b8\b/.test(text));
            console.log('🎯 Found answer "8":', hasEight ? '✅ Yes' : '❌ No');
          }
        }
      } else {
        console.log('❌ Login did not redirect - may have failed');
      }
    }
    
  } catch (error) {
    console.error('❌ Error during test:', error.message);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

testServer().catch(console.error);