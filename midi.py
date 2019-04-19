import os
import sys
import pickle
import librosa
import numpy
from midiutil.MidiFile import MIDIFile

# Gets the current directory
dir_path = os.path.dirname(os.path.realpath(__file__))

# Import args
term = str(sys.argv[1])

# Loads the data information pickle derived from the audio
pick = pickle.load( open(dir_path+'/music/%s/%s.pkl' % (term.replace(' ','-'),term.replace(' ','-')), "rb") )

# Returns the sample rate so we can possibly make the midi the same to be merged later
file_info = (os.popen('mp3info -p '+'"%Q %L %v %o %r"'+' %s/music/%s/%s.mp3' % (dir_path,term.replace(' ','-'),term.replace(' ','-'))).read()).split()[0]

# Creates STD
std = numpy.std(pick[5])

# An upper limit to the energy - to compensate for sharp noises not necessarily from the melody
#limit = max(pick[5]) - numpy.mean(pick[5])

# Create your MIDI object
mf = MIDIFile(1) 
track = 0   
time = 0

# Creates the track with tempo from pickle
mf.addTrackName(track, time, "Sample Track")
mf.addTempo(track, time, pick[4])

# Add some notes
channel = 0
volume = 100

# Delay until the first note
mf.addNote(0, 0, 0, 0, float(pick[1][0]), 1)

# Add notes to the track respective of time, and magnitude for the volume
for x in range(0, len(pick[0])):
	try:
		if (float(pick[5][x]) > std): # and (float(pick[5][x]) < limit):
			pitch = librosa.note_to_midi(pick[0][x][0])
			time = float(pick[1][x])*(pick[4]/60)
			duration = float(float(pick[1][x+1])-float(pick[1][x]))
			volume = 100
			mf.addNote(track, channel, pitch, time, duration, volume)
	except Exception as e:
		pass

# Write it to disk
with open(dir_path+"/music/%s/%s.mid" % (term.replace(' ','-'),term.replace(' ','-')), 'wb') as outf:
    mf.writeFile(outf)

os.popen('timidity %s/music/%s/%s.mid -Ow -o - | ffmpeg -i - -acodec libmp3lame -ab %s %s/music/%s/%s-midi.mp3' % (dir_path,term.replace(' ','-'),term.replace(' ','-'),file_info,dir_path,term.replace(' ','-'),term.replace(' ','-')))
os.popen('sox -m %s/music/%s/%s-midi.mp3 %s/music/%s/%s.mp3 %s/music/%s/%s-final.mp3' % (dir_path,term.replace(' ','-'),term.replace(' ','-'),dir_path,term.replace(' ','-'),term.replace(' ','-'),dir_path,term.replace(' ','-'),term.replace(' ','-')) )
