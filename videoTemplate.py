# To be used for testing purposes in adding new features - limited to a smaller processing time that is needed

import os
import sys
import pickle
import PIL.Image as plim
import gizeh as gz
import mingus.extra.tunings as tunings
import aggdraw
from mingus.containers import Note
from PIL import Image, ImageFont, ImageDraw
from moviepy.editor import *
from moviepy.video.io.bindings import PIL_to_npimage
from unidecode import unidecode

# Setup violin instrument for analysis
instrument = tunings.StringTuning('Fiddle', 'Standard tuning', ['G-3', 'D-4', 'A-4', 'E-5'])
instrument_info = violin = [[['(110-(t*10.5))','(180*t)'],['(145-(t*4.5))','(180*t)'],['(178+(t*4.7))','(180*t)'],['(211+(t*11))','(180*t)']],['1.77'],['violin_background.png'],[['192'],['862']],['4']]
position = []

# Pixel dimensions
size = 640,360
W,H = 640,360
x = 0

# Gets the current directory
dir_path = os.path.dirname(os.path.realpath(__file__))

# Color defs.
norm = (0,0,255)
lower = (153,153,0)
higher = (255,10,10)
black = (25,0,0)
white = (255,255,255)


# Font information
fontname = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
font = ImageFont.FreeTypeFont(fontname, 38)

staff_notes_high = ['B6', 'A6', 'G6', 'F6', 'E6', 'D6', 'C6', 'B5', 'A5', 'G5', 'F5', 'E5', 'D5', 'C5', 'B4', 'A4', 'G4', 'F4', 'E4', 'D4', 'C4']
staff_notes_low = ['B3','A3','G3','F3','E3','D3','C3','B2','A2','G2','F2','E2','D2','C2','B1','A1','G1','F1','E1','D1','C1']

class video(object):
	# Local vars.
	frame,errors,modifier= 0,0,0
	last_pop_frame,last_pop_frame_time = 0,0
	spool,spool_circle,spool_line,spool_note_timer,spool_circle_timer,spool_line_timer = [],[],[],[],[],[]
	test = False

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
		self.spool_line.append('drawl.line(((622)-(158*t), %s, (632)-(158*t), %s), p)'.replace('t','(t-%s)' % t) % (y,y))

	# Adds sharp
	def add_sharp(self,y,t):
		self.spool_line_timer.append(t)
		self.spool_line.append('drawl.line(((632)-(158*t), %s-3, (642)-(158*t), %s-3), p)'.replace('t','(t-%s)' % t) % (y,y))
		self.spool_line.append('drawl.line(((632)-(158*t), %s-1, (642)-(158*t), %s-1), p)'.replace('t','(t-%s)' % t) % (y,y))
		self.spool_line.append('drawl.line(((635.3)-(158*t), %s-6, (635.3)-(158*t), %s+2), p)'.replace('t','(t-%s)' % t) % (y,y))
		self.spool_line.append('drawl.line(((638.7)-(158*t), %s-6, (638.7)-(158*t), %s+2), p)'.replace('t','(t-%s)' % t) % (y,y))

	# Generates the frames
	def make_frame(self,t):
		note = 'G#5'
		# Setup landscape
		im = plim.new('RGB',size)
		draw = ImageDraw.Draw(im)
	
		if self.test == False:
			note_type = "quarter"

			# Saves Sharp/Flat for later
			if '#' in note:
				self.modifier += 1
			elif 'b' in note:
				self.modifier -= 1

			note = note.replace('#','')
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

			# Add sharp icon
			if self.modifier == 1:
				self.add_sharp(y+(staff_position * 1.8),t)

			self.test = True

		# Check to see if a symbol (circle with a line) for sheet music nees to be popped as well
		if len(self.spool_circle_timer) > 0:
			# If the circle is done being shown - pop it from the spooler
			if (t - float(self.spool_circle_timer[0])) > float(instrument_info[1][0]):
				self.spool_circle.pop(0)
				self.spool_circle_timer.pop(0)
		if len(self.spool_line_timer) > 0:
			# If the line is done being shown - pop it from the spooler
			if (t - float(self.spool_line_timer[0])) > float(instrument_info[1][0]):
				self.spool_line.pop(0)
				self.spool_line_timer.pop(0)

		# Draw the circles from spool if not empty
		for x in range(0,len(self.spool_circle)):
			exec(self.spool_circle[x])

		# Setup for drawing lines
		drawl = aggdraw.Draw(im)
		drawl.setantialias(False)
		p = aggdraw.Pen(color=black,width=1)

		# Draw the lines from spool if not empty
		for x in range(0,len(self.spool_line)):
			exec(self.spool_line[x])

		# Whoosh!
		drawl.flush()

		# Returns the instance frame to be added to the movie
		return PIL_to_npimage(im)

	# Generates the video
	def generate(self):
		# Creates the backdrop
		bg = ImageClip('images/violin_background.png').set_duration(5)
		
		# Sets up the moving notes overlay
		overlay = VideoClip(self.make_frame,duration=(5))
		overlay_mask = vfx.mask_color(overlay, color=[0,0,0])

		# Combine and finalize animations
		final = CompositeVideoClip([bg,overlay_mask], size=size)

		# Export animation as video
		final.write_videofile('/root/Scripts/MusicConverter/videos/test.mp4', fps=24)

if __name__ == '__main__':
	video().generate()


