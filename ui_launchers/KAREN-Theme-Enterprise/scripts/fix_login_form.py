# Read the file
with open('src/components/auth/LoginForm.tsx', 'r') as f:
    lines = f.readlines()

# Fix line 245 (index 244)
if len(lines) > 244:
    lines[244] = lines[244].replace("you're", "you're")

# Fix line 377 (index 376)
if len(lines) > 376:
    lines[376] = lines[376].replace("app's", "app's")

# Write back to file
with open('src/components/auth/LoginForm.tsx', 'w') as f:
    f.writelines(lines)

print('Fixed unescaped entities in LoginForm.tsx')
