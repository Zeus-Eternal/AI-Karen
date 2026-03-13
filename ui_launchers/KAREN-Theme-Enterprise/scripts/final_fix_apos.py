# Read the file
with open('src/components/auth/LoginForm.tsx', 'r') as f:
    content = f.read()

# Replace the unescaped entity
content = content.replace("Verify you're using the correct credentials:", "Verify you're using the correct credentials:")

# Write back to file
with open('src/components/auth/LoginForm.tsx', 'w') as f:
    f.write(content)

print('Fixed unescaped entity in LoginForm.tsx')