import os
import sys
import subprocess
import numpy as np
import librosa
import pickle
from subprocess import call

# Gets the current directory
dir_path = os.path.dirname(os.path.realpath(__file__))

# List of options
instruments = ['violin','viola','guitar','banjo']
difficulties = ['beginner','intermediate','advanced']
hop = [512,1024]

# Saves args
term = str(sys.argv[1])
instrument = str(sys.argv[2])
difficulty = str(sys.argv[3])

# Creates new directory for music & information if not already made
if not os.path.exists("%s/music/%s" % (dir_path,term.replace(' ','-')) ):
	os.makedirs("%s/music/%s" % (dir_path,term.replace(' ','-')) )

# ---------------------------------------------------------------------------------------
# Get the pitch at a time with note
def detect_pitch(y, sr, t):
	index = magnitudes[:, t].argmax()
	pitch = pitches[index, t] 
	return pitch

# Gets the energy of harmonics at a time
def get_energy(y, sr, t):
	index = magnitudes[:, t].argmax()
	energy = S_sal[index, t]
	return energy
# ---------------------------------------------------------------------------------------

# If there isn't music for that term already, download it
if (os.path.exists(dir_path+'/music/%s/%s.mp3' % (term.replace(' ','-'),term.replace(' ','-'))) == False):
	# Get the url for a term, download mp3 and information on it
	for x in range(2,5):
		try:
			url = os.popen('timeout 30 casperjs %s/casperjs/download.js --term="%s" --attempt="%s"' % (dir_path,term,str(x))).read().split('"')[1]
		except Exception as e:
			print 'URL cannot be resolved - Retrying'
			continue
		os.system('wget --output-document="%s/music/%s/%s.mp3" "%s"' % (dir_path,term.replace(' ','-'),term.replace(' ','-'),url))
		break
	else:
		print 'No adequate files could be attained'
		exit()

# If the pickle for this term has not been generated before, generate one
if (os.path.exists(dir_path+'/music/%s/%s.pkl' % (term.replace(' ','-'),term.replace(' ','-'))) == False):
	print 'Extracting notes/etc. from song'
	# Returns sample rate
	file_length = os.popen('mp3info -p "%S" '+dir_path+'/music/'+term.replace(' ','-')+'/'+term.replace(' ','-')+'.mp3').read()

	# Load the music
	y, sr = librosa.load(dir_path+'/music/%s/%s.mp3' % (term.replace(' ','-'),term.replace(' ','-')) )

	# Set the hop length depending on sample rate
	hop_length = min(hop, key=lambda x:abs(x-(sr / 43))) 

	# Separate harmonics and percussives into two waveforms
	stft = librosa.stft(y)
	H, P = librosa.decompose.hpss(stft) #, margin=(5,1))
	y_harmonic = librosa.core.istft(H)
	y_percussive = librosa.core.istft(P)

	# Estimates harmonic energy
	S = np.abs(librosa.stft(y))
	freqs = librosa.core.fft_frequencies(sr)
	harms = [1, 2, 3, 4] 
	weights = [1.0, 0.5, 0.33, 0.25]
	S_sal = librosa.salience(S, freqs, harms, weights, fill_value=0)

	# Estimates of a possible beat to be filtered later, and it's timing, magnitude
	onset_env = librosa.onset.onset_strength(y=y, sr=sr,aggregate=np.median)
	tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env,hop_length=hop_length,y=y_harmonic,sr=sr,tightness=0.1)
	timing = librosa.frames_to_time(beat_frames)
	pitches, magnitudes = librosa.core.piptrack(y=y_harmonic, sr=sr, n_fft=(hop_length*4), hop_length=hop_length, threshold=0.1)

	# Notes are the corresponding to the timing variable to be plotted -> sent to pickle
	notes,pick,mags,freq,harm = [],[],[],[],[]
	for x in range(0,len(beat_frames)):
		try:
			freq.append(detect_pitch(y_harmonic, sr, beat_frames[x]))
			harm.append(get_energy(y_harmonic, sr, beat_frames[x]))
			note = librosa.hz_to_note(detect_pitch(y_harmonic, sr, beat_frames[x]))
			notes.append(note)
			mags.append(magnitudes[:, beat_frames[x]].argmax())
		except Exception as e:
			notes.append('0')
			mags.append('0')
			continue

	# Pickle to be used as a template
	pick.extend([notes])
	pick.extend([timing])
	pick.extend([mags])
	pick.extend([file_length])
	pick.extend([tempo])
	pick.extend([harm])

	# Save for generate-video.py to use
	with open(dir_path+'/music/%s/%s.pkl' % (term.replace(' ','-'),term.replace(' ','-')), 'wb') as fp:
		pickle.dump(pick, fp)

	# Ready Txt file vars. to be used for web player with microphone
	freq = ','.join(map(str,freq)).replace("'","")
	timing = ','.join(map(str,timing)).replace("'","")
	mags = ','.join(map(str,mags)).replace("'","")

	# Save for web player
	with open(dir_path+'/music/%s/%s.txt' % (term.replace(' ','-'),term.replace(' ','-')),'w') as f:
		f.write(freq+'\n'+timing+'\n'+mags)

# Generate the midi for merging
os.system('python midi.py "%s"' % term)	

# Generates video animations depending upon instruments and difficulties - Uploads to Youtube currently
if (difficulty != 'all') and (instrument != 'all'):
	if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instrument,difficulty)) == False):
		os.system('python generate-video.py "%s" "%s" "%s"' % (term,instrument,difficulty))
elif (difficulty == 'all') and (instrument == 'all'):
	for x in range(0,len(instruments)):
		for y in range(0,len(difficulties)):
			if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instruments[x],difficulties[y])) == False):
				os.system('python generate-video.py "%s" "%s" "%s"' % (term,instruments[x],difficulties[y]))
elif (difficulty == 'all') and (instrument != 'all'):
	for y in range(0,len(difficulties)):
		if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instrument,difficulties[y])) == False):
			os.system('python generate-video.py "%s" "%s" "%s"' % (term,instrument,difficulties[y]))	
elif (difficulty != 'all') and (instrument == 'all'):
	for y in range(0,len(instruments)):
		if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instruments[y],difficulty)) == False):
			os.system('python generate-video.py "%s" "%s" "%s"' % (term,instruments[y],difficulty))	



