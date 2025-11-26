import re

# Read the file
with open('src/components/auth/LoginForm.tsx', 'r') as f:
    content = f.read()

# Replace the unescaped entity using regex
content = re.sub(r"Verify you're using the correct credentials:", r"Verify you're using the correct credentials:", content)

# Write back to file
with open('src/components/auth/LoginForm.tsx', 'w') as f:
    f.write(content)

print('Fixed unescaped entity in LoginForm.tsx')