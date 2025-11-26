# Read file
with open('src/components/auth/LoginForm.tsx', 'r') as f:
    content = f.read()

# Replace exact string
content = content.replace("Verify you're using", "Verify you're using")

# Write back to file
with open('src/components/auth/LoginForm.tsx', 'w') as f:
    f.write(content)

print('Fixed unescaped entity in LoginForm.tsx')
