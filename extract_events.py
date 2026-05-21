import re

def parse_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    glossary = {}
    
    # Regex to match event headers: #### `0xXX` — MNEMONIC · *Title*
    # Or: #### `0xXX` — *Title*
    header_re = re.compile(r'#### `(0x[0-9A-Fa-f]+)` — (?:([A-Z0-9_]+) · )?\*(.*)\*')
    
    sections = re.split(r'\n#### ', content)
    for section in sections[1:]: 
        section = '#### ' + section
        lines = section.strip().split('\n')
        header = lines[0]
        match = header_re.match(header)
        if match:
            code = match.group(1)
            mnemonic = match.group(2) or '-'
            title = match.group(3).strip()
            
            description_parts = [title]
            
            # Extract paragraphs until the table or next section or category header
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('###') or line.startswith('##'): # Stop at headers
                    break
                if line.startswith('|') or line.startswith('---'):
                    # Skip tables
                    continue
                if line.startswith('####'):
                    break
                description_parts.append(line)
            
            description = ' '.join(description_parts)
            # Remove redundant spaces if any
            description = re.sub(r'\s+', ' ', description).strip()
            
            glossary[code] = {
                'Mnemonic': mnemonic,
                'Description': description
            }
            
    return glossary

if __name__ == "__main__":
    glossary = parse_md('/home/carol/Área de trabalho/selecao-eventos2/arm_cortex_a53_pmu_events.md')
    print("EVENT_GLOSSARY = {")
    for code in sorted(glossary.keys()):
        item = glossary[code]
        # Use replace for single quotes to avoid issues in the dict literal
        desc = item['Description'].replace("'", "\\'")
        print(f"    '{code}': {{'Mnemonic': '{item['Mnemonic']}', 'Description': '{desc}'}},")
    print("}")
