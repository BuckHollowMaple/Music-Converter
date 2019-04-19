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

# Saves args
term = str(sys.argv[1])
instrument = str(sys.argv[2])
difficulty = str(sys.argv[3])

# Get the pitch at a time with note
def detect_pitch_harm(y, sr, t):
	index = magnitudes_harm[:, t].argmax()
	pitch = pitches_harm[index, t]
	return pitch

def detect_pitch_perc(y, sr, t):
	index = magnitudes_perc[:, t].argmax()
	pitch = pitches_perc[index, t]
	return pitch


# Get the url for a term, download mp3 and information on it
if (os.path.exists(dir_path+'/music/%s.mp3' % term.replace(' ','-')) == False) or (os.path.exists(dir_path+'/music/%s-instrumental.mp3' % term.replace(' ','-')) == False):
	for x in range(2,5):
		try:
			url = os.popen('timeout 30 casperjs %s/casperjs/download.js --term="%s" --attempt="%s"' % (dir_path,term,str(x))).read().split('"')[1]
		except Exception as e:
			print 'URL cannot be resolved - Retrying'
			continue
		os.system('wget --output-document="%s/music/%s.mp3" %s' % (dir_path,term.replace(' ','-'),url))
		sox = os.popen('sox %s/music/%s.mp3 %s/music/%s-instrumental.mp3 oops 2>&1' % (dir_path,term.replace(' ','-'),dir_path,term.replace(' ','-'))).read()
		if 'FAIL' in sox:
			print 'Failure in sox conversion - Retrying'
			continue
		else:
			print 'Found an audio file source that works'
			break
	else:
		print 'No adequate files could be attained'
		exit()

if (os.path.exists(dir_path+'/music_info/%s.pkl' % term.replace(' ','-')) == False):
	print 'Extracting notes/etc. from song'
	file_info = (os.popen('mp3info -p "%Q %L %v %o %r" '+dir_path+'/music/'+term.replace(' ','-')+'-instrumental.mp3').read()).split()[0]
	file_length = os.popen('mp3info -p "%S" '+dir_path+'/music/'+term.replace(' ','-')+'-instrumental.mp3').read()

	# Load the music
	y, sr = librosa.load(dir_path+'/music/%s.mp3' % term.replace(' ','-'))

	# Set the hop length depending on fileinfo
	hop_length = 512

	# Separate harmonics and percussives into two waveforms
	y_harmonic, y_percussive = librosa.effects.hpss(y)

	# Beat track on the percussive signal
	onset_env = librosa.onset.onset_strength(y, sr=sr,aggregate=np.median)
	tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env,sr=sr,tightness=1)
	timing = librosa.frames_to_time(beat_frames)
	pitches_harm, magnitudes_harm = librosa.core.piptrack(y=y_harmonic, sr=sr, fmin=79, fmax=1321, threshold=0)
	pitches_perc, magnitudes_perc = librosa.core.piptrack(y=y_percussive, sr=sr, fmin=79, fmax=1321, threshold=0)

	# Notes are the corresponding to the timing variable to be plotted
	notes,pick,mags,freq = [],[],[],[]
	for x in range(0,len(beat_frames)):
		try:
			if (magnitudes_harm[:, beat_frames[x]].argmax()) > (magnitudes_perc[:, beat_frames[x]].argmax()):
				freq.append(detect_pitch_harm(y_harmonic, sr, beat_frames[x]))
				note = librosa.hz_to_note(detect_pitch_harm(y_harmonic, sr, beat_frames[x]))
				notes.append(note)
				mags.append(magnitudes_harm[:, beat_frames[x]].argmax())
			else:
				freq.append(detect_pitch_perc(y_percussive, sr, beat_frames[x]))
				note = librosa.hz_to_note(detect_pitch_perc(y_percussive, sr, beat_frames[x]))
				notes.append(note)
				mags.append(magnitudes_perc[:, beat_frames[x]].argmax())
		except Exception as e:
			notes.append('0')
			mags.append('0')
			continue

	# Prep variables into pickle and txt
	pick.extend([notes])
	pick.extend([timing])
	pick.extend([mags])
	pick.extend([file_length])
	pick.extend([tempo])
	freq = ','.join(map(str,freq)).replace("'","")
	timing = ','.join(map(str,timing)).replace("'","")
	mags = ','.join(map(str,mags)).replace("'","")

	# Save for web player
	with open(dir_path+'/music_info/%s.txt' % term.replace(' ','-'),'w') as f:
		f.write(freq+'\n'+timing+'\n'+mags)

	# Save the pickle
	with open(dir_path+'/music_info/%s.pkl' % term.replace(' ','-'), 'wb') as fp:
		pickle.dump(pick, fp)

# Generate the midi
#os.system('python midi.py "%s"' % term)	

# Generates video animations
if (difficulty != 'all') and (instrument != 'all'):
	if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instrument,difficulty)) == False):
		os.system('python video.py "%s" "%s" "%s"' % (term,instrument,difficulty))
elif (difficulty == 'all') and (instrument == 'all'):
	for x in range(0,len(instruments)):
		for y in range(0,len(difficulties)):
			if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instruments[x],difficulties[y])) == False):
				os.system('python video.py "%s" "%s" "%s"' % (term,instruments[x],difficulties[y]))
elif (difficulty == 'all') and (instrument != 'all'):
	for y in range(0,len(difficulties)):
		if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instrument,difficulties[y])) == False):
			os.system('python video.py "%s" "%s" "%s"' % (term,instrument,difficulties[y]))	
elif (difficulty != 'all') and (instrument == 'all'):
	for y in range(0,len(instruments)):
		if (os.path.exists(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),instruments[y],difficulty)) == False):
			os.system('python video.py "%s" "%s" "%s"' % (term,instruments[y],difficulty))	



