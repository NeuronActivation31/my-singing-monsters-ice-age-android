import sys

with open('game_android.py', 'r') as f:
    lines = f.readlines()

# Find line where main loop starts (line numbers 0-indexed)
# We'll look for '# Load saved game'
for i, line in enumerate(lines):
    if line.strip() == '# Load saved game':
        start_idx = i
        break
else:
    start_idx = len(lines)

# Insert if __name__ guard before that line
lines.insert(start_idx, 'if __name__ == "__main__":\n')
# Indent all subsequent lines by 4 spaces
for j in range(start_idx + 1, len(lines)):
    lines[j] = '    ' + lines[j]

with open('game_android.py', 'w') as f:
    f.writelines(lines)