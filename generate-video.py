import os
import sys
import pickle
import librosa
import wikipedia
import aggdraw
import numpy
import PIL.Image as plim
import mingus.extra.tunings as tunings
from mingus.containers import Note
from PIL import ImageFont, ImageDraw
from moviepy.editor import *
from moviepy.video.io.bindings import PIL_to_npimage
from unidecode import unidecode
from shutil import copyfile

# Returns the current directory
dir_path = os.path.dirname(os.path.realpath(__file__))

# Setup possible instruments for analysis tools if need be
difficulties = ['beginner','intermediate','advanced']
violin_tuning = tunings.StringTuning('Fiddle', 'Standard tuning', ['G-3', 'D-4', 'A-4', 'E-5'])
viola_tuning = tunings.StringTuning('Viola', 'Standard tuning', ['C-3','G-3', 'D-4', 'A-4'])
guitar_tuning = tunings.StringTuning('Guitar', 'Standard tuning', ['E-2', 'A-2', 'D-3', 'G-3', 'B-3', 'E-4'])
banjo_tuning = tunings.StringTuning('Banjo', 'Standard tuning', ['G-2', 'D-3', 'A-3', 'E-4'])
violin = [[['(110-(t*10.5))','(180*t)'],['(145-(t*4.5))','(180*t)'],['(178+(t*4.7))','(180*t)'],['(211+(t*11))','(180*t)']],['1.77'],['violin_background.png'],[['192'],['862']],['4']]
viola = [[['(110-(t*10.5))','(180*t)'],['(145-(t*4.5))','(180*t)'],['(178+(t*4.7))','(180*t)'],['(211+(t*11))','(180*t)']],['1.77'],['violin_background.png'],[['127'],['557']],['4']]
guitar = [[['(290*(t/2))','(77-(t*10.3))'],['(290*(t/2))','(103-(t*7))'],['(290*(t/2))','(131+(t/4.3))'],['(290*(t/2))','(160+(t*4.2))'],['(290*(t/2))','(187+(t*9))']],['2.28'],['guitar_background.png'],[['79'],['1321']],['24']]
banjo = [[['(290*(t/2))','(90-(t*7.9))'],['(290*(t/2))','(122+(t/4.38))'],['(290*(t/2))','(154+(t*4.24))'],['(290*(t/2))','(187+(t*10))']],['2.24'],['banjo_background.png'],[['94'],['1321']],['24']]

# Notes vars.
proximity = [0.25,0.5,0.9]
staff_notes_high = ['B6', 'A6', 'G6', 'F6', 'E6', 'D6', 'C6', 'B5', 'A5', 'G5', 'F5', 'E5', 'D5', 'C5', 'B4', 'A4', 'G4', 'F4', 'E4', 'D4', 'C4']
staff_notes_low = ['B3','A3','G3','F3','E3','D3','C3','B2','A2','G2','F2','E2','D2','C2','B1','A1','G1','F1','E1','D1','C1']
notenames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
pitch_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
acc_map = {'#': 1, '': 0, 'b': -1, '!': -1}
note_map = ['C', 'C#', 'D', 'D#',
            'E', 'F', 'F#', 'G',
            'G#', 'A', 'A#', 'B']

# Pixel dimensions
size = 640,360
W,H = 640,360
x = 0
position = []

# Color defs.
norm = (0,0,255)
lower = (153,153,0)
higher = (255,10,10)
black = (25,0,0)
white = (255,255,255)

# Import args
term = str(sys.argv[1])
inst = str(sys.argv[2])
difficulty = str(sys.argv[3])

# Depending upon args., we load the instrument into memory
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
audio_clip = AudioFileClip(dir_path+'/music/%s/%s-final.mp3' % (term.replace(' ','-'),term.replace(' ','-')))

# Loads the data information pickle derived from the audio
pick = pickle.load( open(dir_path+'/music/%s/%s.pkl' % (term.replace(' ','-'),term.replace(' ','-')), "rb") )

# Calculate STD of the salience
std = numpy.std(pick[5])

# Font information
fontname = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
font = ImageFont.FreeTypeFont(fontname, 38)

# ---------------------------------------------------------------------------------------
# Create a notebin of available notes for the instrument
def create_notebins(min_note='C0', max_note='E7'):
    note_bins = [min_note]
    last_note = min_note
    idx = notenames.index(last_note[0])
    octave = int(min_note[1])
    while last_note != max_note:
        idx += 1
        last_note = notenames[idx % 12]+str(octave)
        note_bins += [last_note]
        if idx % 12 == 11:
            octave += 1
    return note_bins

# Calculate the avg magnitude for the beats in the song
def avg(list):
	sum = 0
	for elm in list:
		sum += elm
	return sum/(len(list)*1.0)
"""
def determine_scale():
	# Gets the note count
	note_counts = []
	search = ['G','G#','D','D#','A','A#','E','E#','C','C#']
	to_search = re.compile('|'.join(sorted(search, key=len, reverse=True)))
	matches = (to_search.search(el[0]) for el in pick[0])
	counts = str(Counter(match.group() for match in matches if match))
	for x in range(0,len(counts.split('Counter({')[1].split('})')[0].split(','))):
		note = counts.split('Counter({')[1].split('})')[0].split(',')[x].split("'")[1]
		count = counts.split('Counter({')[1].split('})')[0].split(',')[x].split("'")[2].split(': ')[1]
		note_counts.append([note,count])

	# Gets the majority Note (A,D,etc.) and how many counts are in it's major
	note_majority = note_counts[0][0]
	note_count = note_counts[0][1]
	major_count = 0
	for x in range(0,len(note_counts)):
		if note_counts[x].count('%s#' % note_counts[0][0]) == 1:
			major_count = note_counts[x][1]
			break

	# If there are more majors than half the normal note, then use major note scale
	if major_count > ((note_count-major_count)/2):
		# Scale = note's major
		print 'hi'
	else:
		# Scale = note
		print 'hi'
"""		
# ---------------------------------------------------------------------------------------

# Video instance varied, depending upon the input
class video(object):
	# Local vars.
	frame,errors,modifier= 0,0,0
	last_pop_frame,last_pop_frame_time = 0,0
	spool,spool_circle,spool_line,spool_note_timer,spool_circle_timer,spool_line_timer,spool_sharp_timer,spool_sharp = [],[],[],[],[],[],[],[]

	# Automate this by instrument later - tuned for violin
	notebin = create_notebins(min_note='G3', max_note='G#5')

	# Threshold is the key to making it more complex. The higher the threshold, the less notes will be played
	if difficulty == "beginner":
		threshold = avg(pick[2]) - (max(pick[2])/min(pick[2]))
	elif difficulty == "intermediate":
		threshold = (avg(pick[2]) - (max(pick[2])/min(pick[2])))/2
	elif difficulty == "advanced":
		threshold = 0
		#threshold = 5 - try it out sometime to clear out ultra low magnitude notes

	# Returns either 0.25, 0.5, or 1 to determine sheet music notation
	def getProximity(self):
		return min(proximity, key=lambda x:abs(x-(float(pick[1][self.frame+1]) - float(pick[1][self.frame]))))

	# Adds note to spool
	def add_note(self,pos,note,t,color):
		self.spool_note_timer.append(t)
		self.spool.append('draw.text((%s,%s), "%s", fill=%s, font=font)' % (pos[0].replace('t','(t-%s)' % self.spool_note_timer[len(self.spool_note_timer)-1]), pos[1].replace('t','(t-%s)' % self.spool_note_timer[len(self.spool_note_timer)-1]), note, color))

	# Adds circle to spool
	def add_circle(self,note_type,y,t,modifier):
		self.spool_circle_timer.append(t)
		alt = ''
		if note_type == 'quarter':
			alt = 'fill=(25,0,0)'
		elif (note_type == 'half') or (note_type == 'whole'):
			alt = 'fill=(255,255,255), outline=(25,0,0)'
			
		self.spool_circle.append('draw.ellipse(((627-(t*158))-2, %s-2, (627-(t*158))+2, %s+2), %s)'.replace('t','(t-%s)' % t) % (y,y,alt))

	# Adds upper line for lower notes
	def add_upper_line(self,y,t):
		self.spool_line_timer.append(t)
		self.spool_line.append('drawl.line(((629)-(158*t), %s+2, (629)-(158*t), %s-11), p)'.replace('t','(t-%s)' % t) % (y,y))

	# Adds lower line for higher notes
	def add_lower_line(self,y,t):
		self.spool_line_timer.append(t)
		self.spool_line.append('drawl.line(((626)-(158*t), %s+2, (626)-(158*t), %s+11), p)'.replace('t','(t-%s)' % t) % (y,y))

	# Adds underline 
	def add_underline(self,y,t):
		self.spool_line_timer.append(t)
		self.spool_line.append('drawl.line(((622)-(158*t), %s, (632)-(158*t), %s), p_thin)'.replace('t','(t-%s)' % t) % (y,y))

	# Adds sharp
	def add_sharp(self,y,t):
		self.spool_sharp_timer.append(t)
		self.spool_sharp.append('drawl.line(((632)-(158*t), %s-3, (642)-(158*t), %s-3), p)'.replace('t','(t-%s)' % t) % (y,y))
		self.spool_sharp.append('drawl.line(((632)-(158*t), %s-1, (642)-(158*t), %s-1), p)'.replace('t','(t-%s)' % t) % (y,y))
		self.spool_sharp.append('drawl.line(((635.3)-(158*t), %s-6, (635.3)-(158*t), %s+2), p)'.replace('t','(t-%s)' % t) % (y,y))
		self.spool_sharp.append('drawl.line(((638.7)-(158*t), %s-6, (638.7)-(158*t), %s+2), p)'.replace('t','(t-%s)' % t) % (y,y))

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

			# If the note's magnitude is above the threshold, and standard deviation for salience, show the note
			if (int(pick[2][self.frame]) >= self.threshold) and (float(pick[5][self.frame]) > std):
				# Convert note into string, position, sharpness & how it appears in video
				try:
					# Gets the current note from pickle and format
					note = str(pick[0][self.frame][0]).replace("'","")
					note = note[:len(note)-1] + '-' + note[len(note)-1:]
					note_len = len(note)
					note_str = note
					note = Note(note)
					loop_counter = 0

					# Enables note switching of octaves
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

					# Something something something
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
				self.add_note(pos,pos_note,t,color)

				# Saves Sharp/Flat for later
				if '#' in note:
					self.modifier += 1
				elif 'b' in note:
					self.modifier -= 1

				# Add the generated sheet music
				try:
					determine = self.getProximity()
					note = note.replace('-','').replace('#','')
					if determine == 0.25:
						note_type = 'quarter'
					elif determine == 0.5:
						note_type = 'half'
					elif determine == 0.9:
						note_type = 'whole'
				except Exception as e:
					note_type = 'quarter'
					pass
				note = (note.replace('#','')).replace('-','')
				try:
					staff_position = staff_notes_high.index(note)
					y = 265 
					if int(note[1:]) >= 5:
						if note_type != 'whole':
							self.add_lower_line(y+(staff_position * 1.8),t)
						if staff_position <= 8:
							for x in range(8,staff_position-1,-2):
								self.add_underline(y+(x * 1.8),t)
					else:
						if note_type != 'whole':
							self.add_upper_line(y+(staff_position * 1.8),t)	
				except Exception as e:
					staff_position = staff_notes_low.index(note)
					y = 310
					if int(note[1:]) == 3:
						if note_type != 'whole':
							self.add_lower_line(y+(staff_position * 1.8),t)
					else:
						if note_type != 'whole':
							self.add_upper_line(y+(staff_position * 1.8),t)
						if staff_position >= 11:
							for x in range(11,staff_position+1,2):
								self.add_underline(y+(x * 1.8),t)

				# Add note and timing to the spooler for sheet music
				self.add_circle(note_type,y+(staff_position * 1.8),t,self.modifier)

				# Add sharp icon if present in note
				if self.modifier == 1:
					self.add_sharp(y+(staff_position * 1.8),t)

			# If the spooler is empty - get it ready
			if len(self.spool) == 0:
				self.last_pop_frame = self.frame
				self.last_pop_frame_time = str(pick[1][self.frame])[:5]

			# Increment to the next note
			self.frame += 1

		# Check to see if a note needs to be popped from spool:
		if len(self.spool_note_timer) > 0:
			# If the note is done being played - pop it from the spooler
			if (t - float(self.spool_note_timer[0])) > float(instrument_info[1][0]):
				self.spool.pop(0)
				self.spool_note_timer.pop(0)
				self.last_pop_frame += 1
				if (self.frame < len(pick[0])):
					self.last_pop_frame_time = str(pick[1][self.last_pop_frame])[:5]
		# Check to see if a symbol (circle with a line) for sheet music nees to be popped as well
		if len(self.spool_circle_timer) > 0:
			# If the circle is done being shown - pop it from the spooler
			if (t - float(self.spool_circle_timer[0])) > float(instrument_info[1][0]):
				self.spool_circle.pop(0)
				self.spool_circle_timer.pop(0)
		# Lines pop
		if len(self.spool_line_timer) > 0:
			# If the line is done being shown - pop it from the spooler
			while True:
				try:
					if (t - float(self.spool_line_timer[0])) > float(instrument_info[1][0]):
						self.spool_line.pop(0)
						self.spool_line_timer.pop(0)
					else:
						break
				except Exception as e:
					break
		# Sharp symbol pop
		if len(self.spool_sharp_timer) > 0:
			while True:
				try:
					# If the line is done being shown - pop it from the spooler
					if (t - float(self.spool_sharp_timer[0])) > float(instrument_info[1][0]):
						for x in range(0,4):
							self.spool_sharp.pop(x)
							self.spool_sharp_timer.pop(x)
					else:
						break
				except Exception as e:
					break

		# Draw the notes from spool if not empty
		for x in range(0,len(self.spool)):
			exec(self.spool[x])

		# Draw the circles from spool if not empty
		for x in range(0,len(self.spool_circle)):
			exec(self.spool_circle[x])

		# Setup for drawing lines
		drawl = aggdraw.Draw(im)
		drawl.setantialias(False)
		p = aggdraw.Pen(color=black,width=2)
		p_thin = aggdraw.Pen(color=black,width=1)

		# Draw the lines from spool if not empty
		for x in range(0,len(self.spool_line)):
			exec(self.spool_line[x])

		# Draw the sharps from spool if not empty
		for x in range(0,len(self.spool_sharp)):
			exec(self.spool_sharp[x])

		# Whoosh!
		drawl.flush()
		
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

# Generate video and upload
if __name__ == '__main__':
	print 'Making the video'

	# Makes a video from the notes and music
	video().generate()

	# Updates file with string position
	copyfile(dir_path+'/music/%s/%s.txt' % (term.replace(' ','-'),term.replace(' ','-')), dir_path+'/music/%s/%s-%s-%s.txt' % (term.replace(' ','-'),term.replace(' ','-'),inst,difficulty))
	position = ','.join(map(str,position)).replace("'","")	
	with open(dir_path+'/music/%s/%s-%s-%s.txt' % (term.replace(' ','-'),term.replace(' ','-'),inst,difficulty),'a') as f:
		f.write('\n'+position)

	# Gets the proper title information from a simple search on google
	info = os.popen('timeout 30 casperjs '+dir_path+'/casperjs/googleHeaderInfo.js --term="%s"' % term).read()
	if 'null' in info:
		title = term.capitalize()
	else:
		title = info.replace('"','').split('-')[1].strip()

	# Uploads video to youtube automatically
	url = os.popen('youtube-upload --title="How to play %s on %s - lvl.%s" --description="Created by automation software, programmed by Alicia The AGI. Visit the website to play alongside the music and be graded from your microphone." --policyId="5742860067573271" --category=Music %s/videos/%s-%s-%s.mp4' % (title,inst.capitalize(),str(difficulties.index(difficulty)+1),dir_path,term.replace(' ','-'),inst,difficulty)).read()
	print 'Your video has been uploaded to youtube'



