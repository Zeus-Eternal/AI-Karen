// Debug script to see what's actually on the login page
const { chromium } = require('playwright');

async function debugLoginPage() {
  console.log('🔍 Debugging login page...');
  
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    await page.goto('http://localhost:8000/login', { timeout: 10000 });
    
    console.log('📄 Page loaded, taking screenshot...');
    await page.screenshot({ path: 'login-debug.png' });
    
    // Get page content
    const content = await page.content();
    console.log('📝 Page HTML length:', content.length);
    
    // Look for input elements
    const inputs = await page.$$eval('input', elements => 
      elements.map(el => ({
        type: el.type,
        id: el.id,
        name: el.name,
        placeholder: el.placeholder,
        className: el.className
      }))
    );
    
    console.log('🔍 Found input elements:', inputs);
    
    // Look for buttons
    const buttons = await page.$$eval('button', elements => 
      elements.map(el => ({
        type: el.type,
        textContent: el.textContent?.trim(),
        className: el.className,
        testId: el.getAttribute('data-testid')
      }))
    );
    
    console.log('🔘 Found button elements:', buttons);
    
    // Look for forms
    const forms = await page.$$eval('form', elements => 
      elements.map(el => ({
        action: el.action,
        method: el.method,
        className: el.className
      }))
    );
    
    console.log('📋 Found form elements:', forms);
    
    // Wait a bit for any dynamic content
    await page.waitForTimeout(3000);
    
    // Check again after waiting
    const inputsAfterWait = await page.$$eval('input', elements => 
      elements.map(el => ({
        type: el.type,
        id: el.id,
        name: el.name,
        placeholder: el.placeholder,
        className: el.className
      }))
    );
    
    console.log('🔍 Input elements after wait:', inputsAfterWait);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await browser.close();
  }
}

debugLoginPage().catch(console.error);