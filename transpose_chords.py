import re

CHORDS_SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
CHORDS_FLAT  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
# SMART_NOTES maps the 12 semitones to the most common/readable representation
SMART_NOTES  = ['C','Db','D','Eb','E','F','F#','G','Ab','A','Bb','B']

def transpose_note(note, semitones):
    if note in CHORDS_SHARP:
        i = CHORDS_SHARP.index(note)
    elif note in CHORDS_FLAT:
        i = CHORDS_FLAT.index(note)
    else:
        return note
    
    target_idx = (i + semitones) % 12
    return SMART_NOTES[target_idx]

def transpose_chord(chord, semitones):
    match = re.match(r'([A-G][b#]?)(.*)', chord)
    if not match:
        return chord
    root, rest = match.groups()
    return transpose_note(root, semitones) + rest

# More robust regex for chords, including common jazz and tension notation
CHORD_REGEX = re.compile(
    r'\b[A-G][b#]?(?:m|maj|min|dim|aug|sus|add|M)?\d*(?:(?:add|no|sus|b|#)\d+)*(?:\/[A-G][b#]?)?\b'
)

def transpose_text(text, semitones):
    def repl(match):
        chord = match.group(0)
        if '/' in chord:
            parts = chord.split('/')
            return "/".join(transpose_chord(p, semitones) for p in parts)
        return transpose_chord(chord, semitones)
    return CHORD_REGEX.sub(repl, text)

if __name__ == "__main__":
    import sys
    # Example usage: cat song.txt | python transpose_chords.py 2
    semitones = 1
    if len(sys.argv) > 1:
        try:
            semitones = int(sys.argv[1])
        except ValueError:
            pass
    input_text = sys.stdin.read()
    print(transpose_text(input_text, semitones))
