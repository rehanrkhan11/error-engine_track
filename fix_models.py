
import os
 
files = [
    'app/agents/agent1_visual.py',
    'app/agents/agent3_pattern.py',
    'app/agents/agent4_synth.py',
    'app/agents/agent5_executor.py',
]
 
for f in files:
    txt = open(f, encoding='utf-8').read()
    txt = txt.replace('gemini-2.0-flash', 'gemini-2.0-flash-lite')
    txt = txt.replace('gemini-1.5-flash-latest', 'gemini-2.0-flash-lite')
    txt = txt.replace('gemini-1.5-pro', 'gemini-2.0-flash-lite')
    open(f, 'w', encoding='utf-8').write(txt)
    print('Fixed:', f)
 
print('Done! Now restart the server.')
 
