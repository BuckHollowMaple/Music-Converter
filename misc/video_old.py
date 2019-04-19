import os
import sys
import pickle
import librosa
import wikipedia
import PIL.Image as plim
import mingus.extra.tunings as tunings
from mingus.containers import Note
from PIL import ImageFont, ImageDraw
from moviepy.editor import *
from moviepy.video.io.bindings import PIL_to_npimage
from unidecode import unidecode
from shutil import copyfile

# Gets the current directory
dir_path = os.path.dirname(os.path.realpath(__file__))

# Setup instrument for analysis
violin_tuning = tunings.StringTuning('Fiddle', 'Standard tuning', ['G-3', 'D-4', 'A-4', 'E-5'])
viola_tuning = tunings.StringTuning('Viola', 'Standard tuning', ['C-3','G-3', 'D-4', 'A-4'])
guitar_tuning = tunings.StringTuning('Guitar', 'Standard tuning', ['E-2', 'A-2', 'D-3', 'G-3', 'B-3', 'E-4'])
banjo_tuning = tunings.StringTuning('Banjo', 'Standard tuning', ['G-2', 'D-3', 'A-3', 'E-4'])

violin = [[['(110-(t*10.5))','(180*t)'],['(145-(t*4.5))','(180*t)'],['(178+(t*4.7))','(180*t)'],['(211+(t*11))','(180*t)']],['1.77'],['violin_background.png'],[['192'],['862']],['4']]
viola = [[['(110-(t*10.5))','(180*t)'],['(145-(t*4.5))','(180*t)'],['(178+(t*4.7))','(180*t)'],['(211+(t*11))','(180*t)']],['1.77'],['violin_background.png'],[['127'],['557']],['4']]
guitar = [[['(290*(t/2))','(77-(t*10.3))'],['(290*(t/2))','(103-(t*7))'],['(290*(t/2))','(131+(t/4.3))'],['(290*(t/2))','(160+(t*4.2))'],['(290*(t/2))','(187+(t*9))']],['2.28'],['guitar_background.png'],[['79'],['1321']],['24']]
banjo = [[['(290*(t/2))','(90-(t*7.9))'],['(290*(t/2))','(122+(t/4.38))'],['(290*(t/2))','(154+(t*4.24))'],['(290*(t/2))','(187+(t*10))']],['2.24'],['banjo_background.png'],[['94'],['1321']],['24']]

difficulties = ['beginner','intermediate','advanced']

# Pixel dimensions
size = 640,360
W,H = 640,360
x = 0
position = []

# Color defs.
norm = (0,0,255)
lower = (153,153,0)
higher = (255,10,10)

# Import args
term = str(sys.argv[1])
inst = str(sys.argv[2])
difficulty = str(sys.argv[3])

if (inst == 'violin'):
	instrument = violin_tuning
	instrument_info = violin
elif (inst == 'viola'):
	instrument = viola_tuning
	instrument_info = viola
elif (inst == 'guitar'):
	instrument = guitar_tuning
	instrument_info = guitar
elif (inst == 'banjo'):
	instrument = banjo_tuning
	instrument_info = banjo

# Loads the audio for the movie
audio_clip = AudioFileClip(dir_path+'/music/%s.mp3' % term.replace(' ','-'))

# Loads the data information pickle derived from the audio
pick = pickle.load( open(dir_path+'/music_info/%s.pkl' % term.replace(' ','-'), "rb") )

# Font information
fontname = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
font = ImageFont.FreeTypeFont(fontname, 38)

# Calculate the avg magnitude for the list
def avg(list):
	sum = 0
	for elm in list:
		sum += elm
	return sum/(len(list)*1.0)

class video(object):
	# Local vars.
	frame = 0
	last_pop_frame = 0
	last_pop_frame_time = 0
	spool = []
	spool_timer = []
	errors = 0
	# Threshold is the key to making it more complex. The higher the threshold, the less notes will be played
	if difficulty == "beginner":
		threshold = avg(pick[2]) - (max(pick[2])/min(pick[2]))
	elif difficulty == "intermediate":
		threshold = (avg(pick[2]) - (max(pick[2])/min(pick[2])))/2
	elif difficulty == "advanced":
		threshold = 0

	# Adds to spool
	def add(self,pos,note,t,color):
		self.spool_timer.append(t)
		self.spool.append('draw.text((%s,%s), "%s", fill=%s, font=font)' % (pos[0].replace('t','(t-%s)' % self.spool_timer[len(self.spool_timer)-1]), pos[1].replace('t','(t-%s)' % self.spool_timer[len(self.spool_timer)-1]), note, color))

	# Generates the frames
	def make_frame(self,t):
		# Setup landscape
		im = plim.new('RGB',size)
		draw = ImageDraw.Draw(im)

		# If the next note time is up - add it to the spool
		if (self.frame < len(pick[0])) and (t > float(str(pick[1][self.frame])[:5])):
			# Reset vars.
			pos = []
			brk = False

			# If the note's magnitude is above the threshold, show the note
			if int(pick[2][self.frame]) >= self.threshold:
				# Convert note into string, position, sharpness & how it appears in video
				try:
					# If the note is within frequency range
					#if int(instrument_info[3][1][0]) > float(librosa.note_to_hz(pick[0][self.frame][0])[0]) > int(instrument_info[3][0][0]):
					# Gets the current note from pickle and format
					note = str(pick[0][self.frame][0]).replace("'","")
					note = note[:len(note)-1] + '-' + note[len(note)-1:]
					note_len = len(note)
					note_str = note
					note = Note(note)
					loop_counter = 0

					while True:
						if (len(instrument.find_fingering([note])) == 0) or (instrument.find_fingering([note])[0][0][1] > int(instrument_info[4][0])):
							# Finger position is unavailable
							if len(instrument.find_fingering([note])) == 0:
								if int(note_str[note_len-1:]) > int(instrument_info[4][0]):
									note.octave_down()
								else:
									note.octave_up()
							# Finger position is greater than max
							elif instrument.find_fingering([note])[0][0][1] > int(instrument_info[4][0]):
								note.octave_down()
						else:
							break
						if loop_counter == 6:
							brk = True
							break
						loop_counter += 1
					if brk == False:
						note = str(note).replace("'","")
						string, pos_note = instrument.find_fingering([note])[0][0]
						position.append(string)

						# Color of animation depending on pitch grade
						if pos_note == (int(instrument_info[4][0])+1):
							pos_note -= 1
							color = higher
						elif ('#' in note) and (pos_note != 0):
							color = higher
						elif ('#' in note) and (pos_note == 0):
							pos_note += 1
							color = lower
						elif 'b' in note:
							color = lower
						else:
							color = norm

						# Get the position of note for animation
						pos = instrument_info[0][string]
					else:
						position.append('10')
					#else:
					#	position.append('10')
					#	brk = True
				# Error with converting note - omit it from spooler
				except Exception as e:
					position.append('10')
					brk = True
			else:
				position.append('10')
				brk = True

			# Found a note to use
			if brk == False:
				# Add note and timing to the spooler
				self.add(pos,pos_note,t,color)

				# If the spooler is empty - get it ready
				if len(self.spool) == 0:
					self.last_pop_frame = self.frame
					self.last_pop_frame_time = str(pick[1][self.frame])[:5]

			# Increment to the next note
			self.frame += 1

		# Check to see if a note needs to be popped from spool:
		if len(self.spool_timer) > 0:
			# If the note is done being played - pop it from the spooler
			if (t - float(self.spool_timer[0])) > float(instrument_info[1][0]):
				self.spool.pop(0)
				self.spool_timer.pop(0)
				self.last_pop_frame += 1
				self.last_pop_frame_time = str(pick[1][self.last_pop_frame])[:5]

		# Draw the lines from spool if not empty
		for x in range(0,len(self.spool)):
			exec(self.spool[x])
		
		# Returns the instance frame to be added to the movie
		return PIL_to_npimage(im)

	# Generates the video
	def generate(self):
		# Creates the backdrop
		bg = ImageClip('images/%s' % instrument_info[2][0]).set_duration(int(pick[3])+10)
		
		# Sets up the moving notes overlay
		overlay = VideoClip(self.make_frame,duration=(int(pick[3])))
		overlay_mask = vfx.mask_color(overlay, color=[0,0,0])

		# Adds music track - image delay due to the time it takes for animation to reach bottom
		overlay_mask.audio = audio_clip.set_start(float(instrument_info[1][0]))

		# Combine and finalize animations
		final = CompositeVideoClip([bg,overlay_mask], size=size)

		# Export animation as video
		final.write_videofile(dir_path+'/videos/%s-%s-%s.mp4' % (term.replace(' ','-'),inst,difficulty), fps=24)

if __name__ == '__main__':
	print 'Making the video'
	video().generate()
	# Updates file with string position
	position = ','.join(map(str,position)).replace("'","")
	copyfile(dir_path+'/music_info/%s.txt' % term.replace(' ','-'), dir_path+'/music_info/%s-%s-%s.txt' % (term.replace(' ','-'),inst,difficulty))
	with open(dir_path+'/music_info/%s-%s-%s.txt' % (term.replace(' ','-'),inst,difficulty),'a') as f:
		f.write('\n'+position)
	# Gets the proper title information
	info = os.popen('timeout 30 casperjs '+dir_path+'/casperjs/googleHeaderInfo.js --term="%s"' % term).read()
	if 'null' in info:
		title = term.capitalize()
	else:
		title = info.replace('"','').split('-')[1].strip()
	# Uploads video to youtube automatically
	url = os.popen('youtube-upload --title="How to play %s on %s - lvl.%s" --description="Created by automation software, programmed by Alicia The AGI" --policyId="5742860067573271" --category=Music %s/videos/%s-%s-%s.mp4' % (title,inst.capitalize(),str(difficulties.index(difficulty)+1),dir_path,term.replace(' ','-'),inst,difficulty)).read()




