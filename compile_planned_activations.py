#!/usr/bin/env python
"""Compile planned_activations translations using polib"""
import os
import sys

# Try using polib if available, otherwise use manual compilation
try:
    import polib
    HAS_POLIB = True
except ImportError:
    HAS_POLIB = False
    import struct

if HAS_POLIB:
    def compile_po_to_mo(po_file, mo_file):
        """Compile using polib (recommended)"""
        print(f"Compiling: {po_file}")
        po = polib.pofile(po_file)
        po.save_as_mofile(mo_file)
        print(f"✓ Compiled {len([e for e in po if not e.obsolete])} messages to {mo_file}")
else:
    def compile_po_to_mo(po_file, mo_file):
        """Simple .po to .mo compiler with proper encoding"""
        print(f"Compiling: {po_file}")
        
        with open(po_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse messages
        messages = {}
        msgid = msgstr = None
        in_msgid = False
        in_msgstr = False
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('msgid '):
                if msgid is not None and msgstr is not None:
                    messages[msgid] = msgstr
                msgid = line[6:].strip('"')
                msgstr = None
                in_msgid = True
                in_msgstr = False
            elif line.startswith('msgstr '):
                msgstr = line[7:].strip('"')
                in_msgid = False
                in_msgstr = True
            elif line.startswith('"'):
                # Continuation line
                content = line.strip('"')
                if in_msgid and msgid is not None:
                    msgid += content
                elif in_msgstr and msgstr is not None:
                    msgstr += content
        
        # Add last message
        if msgid is not None and msgstr is not None:
            messages[msgid] = msgstr
        
        # IMPORTANT: Add metadata header for charset
        metadata = (
            "Content-Type: text/plain; charset=UTF-8\\n"
            "Content-Transfer-Encoding: 8bit\\n"
            "Language: pl\\n"
        )
        messages[''] = metadata
        
        # Build .mo file
        keys = sorted(messages.keys())
        offsets = []
        ids = strs = b''
        
        for key in keys:
            msgid_enc = key.encode('utf-8')
            msgstr_enc = messages[key].encode('utf-8')
            
            offsets.append((len(ids), len(msgid_enc), len(strs), len(msgstr_enc)))
            ids += msgid_enc + b'\0'
            strs += msgstr_enc + b'\0'
        
        # MO file format
        keystart = 7 * 4 + 16 * len(offsets)
        valuestart = keystart + len(ids)
        
        output = struct.pack('Iiiiiii',
            0x950412de,                     # Magic
            0,                              # Version
            len(offsets),                   # Number of entries
            7 * 4,                          # Start of key index
            7 * 4 + len(offsets) * 8,      # Start of value index
            0, 0                            # Hash table
        )
        
        for o1, l1, o2, l2 in offsets:
            output += struct.pack('ii', l1, o1 + keystart)
        
        for o1, l1, o2, l2 in offsets:
            output += struct.pack('ii', l2, o2 + valuestart)
        
        output += ids + strs
        
        os.makedirs(os.path.dirname(mo_file), exist_ok=True)
        with open(mo_file, 'wb') as f:
            f.write(output)
        
        print(f"✓ Compiled {len(offsets)} messages to {mo_file}")

if __name__ == '__main__':
    po = 'planned_activations/locale/pl/LC_MESSAGES/django.po'
    mo = 'planned_activations/locale/pl/LC_MESSAGES/django.mo'
    
    if not HAS_POLIB:
        print("Note: polib not installed, using manual compilation")
        print("For better results: pip install polib")
        print()
    
    compile_po_to_mo(po, mo)

