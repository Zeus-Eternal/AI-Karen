// Debug button import
const fs = require('fs');
const path = require('path');

const buttonPath = path.join(__dirname, 'src/components/ui/button.tsx');
console.log('Button file exists:', fs.existsSync(buttonPath));

const buttonContent = fs.readFileSync(buttonPath, 'utf8');
console.log('Button exports found:', buttonContent.includes('export const Button'));
console.log('Button forwardRef found:', buttonContent.includes('React.forwardRef'));