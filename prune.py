import sys

with open('README.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
skip_mode = False

implemented_headers = [
    'the "black book"', 'the "motion" solver', 'strategic briefing',
    'the first task for your manager', 'why this order?', 'digital nervous system',
    'local voice', 'whisper', 'piper', 'oracle-optimized', 'free voice',
    'colab', 'unsloth', 'scrollytelling', 'auto mode', 'autodream',
    'favor & leverage', 'n8n workflow engine', 'motion ai core', 'unified deployment',
    'flutter scrollytelling', 'shadow tracking', 'honest score', 'learning engine',
    'state file', 'self-cleaning', 'manager’s "master prompt"'
]

unimplemented_headers = [
    'how andrew handles each app', 'whatsapp', 'imessage', 'messaging integration',
    'scenario a: the youtube video link', 'two ways to control andrew',
    'andrew trust score', 'persona vault', 'contextual dna', 'deep mirroring',
    'relationship mapping'
]

for line in lines:
    lower_line = line.lower()
    
    # If the line is a header, decide if we skip
    is_header = line.strip().startswith('#')
    
    if is_header:
        # Check if it matches implemented
        if any(h in lower_line for h in implemented_headers):
            skip_mode = True
        elif any(h in lower_line for h in unimplemented_headers):
            skip_mode = False
        # Neutral headers like "What comes after this?"
        elif 'project andrew' in lower_line or 'missing pieces' in lower_line:
            skip_mode = False

    if not skip_mode:
        output.append(line)

with open('README_pruned2.md', 'w', encoding='utf-8') as f:
    f.writelines(output)

print(f'Original lines: {len(lines)}, Kept: {len(output)}')
