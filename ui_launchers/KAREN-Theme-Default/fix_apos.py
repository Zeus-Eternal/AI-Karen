# Read the file
with open('src/components/auth/LoginForm.tsx', 'r') as f:
    lines = f.readlines()

# Find and replace the specific line
for i, line in enumerate(lines):
    if "Verify you're using the correct credentials:" in line:
        lines[i] = line.replace("you're", "you're")
        print(f"Fixed line {i+1}: {lines[i].strip()}")
        break

# Write back to file
with open('src/components/auth/LoginForm.tsx', 'w') as f:
    f.writelines(lines)

print('Fixed unescaped entity in LoginForm.tsx')