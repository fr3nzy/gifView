import kivy

from kivy.config import Config
Config.set('graphics','resizable',0)

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.video import Video
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

import os, subprocess
from PIL import Image as pil_img


class RootWidget(RelativeLayout):

	def __init__(self):
		super(RootWidget, self).__init__()
	
	@staticmethod
	def select_folder():
		Interface()


#TODO events aren't triggered if class doesn't inherit from Widget class
#TODO when is it actually used?  bind doesn't work without it, 
#TODO understand kivy gui main loop ->

#TODO gifView popup has moveable slider to change webm position, play, pause, next, back, mute buttons
#TODO add image to buttons not the other way round
#TODO load up gifs not just webms with seperate popup view
#TODO search through files shown

class Interface(Widget):

	def __init__(self):
		super().__init__()
		self.folder_popup()
		
	
	def folder_popup(self, *args):
		pop_layout = BoxLayout(orientation='vertical', spacing=20,padding=10)
		label = Label(text='Set folder to scan for gifs/webms\n(defaults to $HOME/Pictures folder if non specified)',halign='center',size_hint_y=None)
		self.txt_input = TextInput(multiline=False,hint_text='eg. /home/user/gifs',size_hint_y=None,height=Window.height/20,focus=False)
		btn = Button(text='Continue',size_hint_y=None, height=Window.height/15)
		btn.bind(on_press=self.btn_press)
	
		pop_layout.add_widget(label)
		pop_layout.add_widget(self.txt_input)
		pop_layout.add_widget(btn)
		
		self.popup = Popup(title='Select Folder',
				content=pop_layout,
				size_hint=(0.5,0.5))
		self.popup.auto_dismiss = True if 'not first' in args else False
		self.popup.open()	
		
	
	# on_press event triggers callback passed with parameter - instance of btn here
	def btn_press(self, instance):
		self.popup.dismiss()
		self.app = App.get_running_app()
		try:
			self.app.root.remove_widget(self.app.root.ids.open_popup) 
		except Exception as e:
			print('\n\n\n'+str(e)+'\n\n\n')
		
		dirName = os.environ['HOME']+'/Pictures' if self.txt_input.text == '' \
					else self.txt_input.text
					
		Clock.schedule_once(lambda dt: self.load_layout(dirName, 'first run'), 0.13)
		
		
	def load_layout(self, dir, *args):
		self.dir = dir
		
		##########################################################
		###################### base layout ############################
		
		try:
			if len(self.app.root.children)>0: # has stack_layout been been instantiated before?
				for widget in self.app.root.children:
					self.app.root.remove_widget(widget)
		except Exception as e:
			print(e)
		
		
		# navbar canvas objects load on next frame(s) load_button() so attributes have loaded
		self.navbar = Widget(size_hint=(None,None), pos_hint={'y':0.932})
		self.app.root.add_widget(self.navbar)
		
		if 'subdir' in args:
			self.back_btn = Button(size_hint=(None,None), size=(80,30), \
											pos_hint={'x': 0.003,'center_y': 0.963})
			img = Image(source='img/alpha.png', allow_stretch=True, size=(80,34))
			self.back_btn.bind(on_release=self.back_btn_setup)
			self.back_btn.add_widget(img)
			self.app.root.add_widget(self.back_btn)
		
		# img source is alpha until interface loaded otherwise img visibile at 0,0 
		self.folder_btn = Button(size_hint=(None,None), size=(80,30), \
											pos_hint={'x': 0.89,'center_y': 0.963})
		img = Image(source='img/alpha.png', allow_stretch=True, size=(80,24))
		self.folder_btn.bind(on_release=lambda instance: self.folder_popup('not first'))
		self.folder_btn.add_widget(img)
		self.app.root.add_widget(self.folder_btn)
		
		self.scroll_layout = ScrollView(pos_hint={'center_x': 0.5, 'center_y': 0.42})
		self.stack_layout = StackLayout(padding=12, \
														spacing=(12,30), \
														size_hint_y=None)
		
		self.scroll_layout.add_widget(self.stack_layout)
		self.app.root.add_widget(self.scroll_layout)
	
		#######################################################			
		
		# delete ',gif_cache' dir from previous run in case changes have been made since then
		if 'first run' in args:
			for directory,subdir,files in os.walk(self.dir):
				subprocess.call(['rm', '-rf', directory+'/.gif_cache'])
			self.dirNames = [] # when subdir is entered parent dir added to index 0,
			#when back pressed & parent dir entered, index 0 is removed so new index 0 is new parent dir
		
		# if not first time going through dir no need to recreate thumbnails
		if '.gif_cache' not in os.listdir(self.dir): # if first time going through directory
			self.first=True		
			# loading screen
			self.progress = ProgressBar(
					max=sum([1 if (fn[-4:] == 'webm') or (os.path.isdir(''.join([self.dir,'/',fn]))) else 0 for fn in os.listdir(self.dir)]))
			self.loading_popup = Popup(title='Loading thumbnails..', \
												content=self.progress, \
												size_hint=(0.4,0.3), \
												auto_dismiss=False)
			self.loading_popup.open()
			os.mkdir(self.dir+'/'+'.gif_cache')	
		else:
			self.first=False
		
		self.ctr=0
		self.fNames = []
		self.fns = os.listdir(self.dir)
		Clock.schedule_interval(lambda dt: self.load_thumbnails(), 0)
	
	
	def load_thumbnails(self):
		if self.ctr == len(self.fns): # if we have gone through all files in current dir
			try:
				self.loading_popup.dismiss()
			except Exception as e:
				print('\n\n\n'+str(e)+'\n\n\n')
			
			# relate stack_layout height to number of children - to allow scroll child must be larger than scroll
			height = sum([100/4.5 for child in self.stack_layout.children])
			self.stack_layout.height = height	
			
			Clock.schedule_once(self.load_buttons) # next frame - required for widgets to update attributes
			return False # cancels clock event
		
		# slice filename str if too long to fit in label optimally
		if len(self.fns[self.ctr]) < 11:
			label_fn = self.fns[self.ctr]
		else:
			label_fn = self.fns[self.ctr][:10]+'..'
			
		
		if self.fns[self.ctr][-4:] == 'webm':
			thumbnail_fn = self.dir+'/'+'.gif_cache'+'/'+str(self.ctr)+'img.jpg'
			if self.first: # create thumbnails
				# get first frame of webm
				subprocess.call(['ffmpeg', '-i', self.dir+'/'+self.fns[self.ctr], '-ss', '00:00:00.0', '-vframes', '1', thumbnail_fn])
				self.progress.value+=1
				
			self.fNames.append('{}/{}'.format(self.dir,self.fns[self.ctr]))
			self.thumbnail = Image(source=thumbnail_fn,size_hint=(None,None),
					allow_stretch=True, keep_ratio=False)
			label = Label(text=label_fn, text_size=(100, None))
			
		elif os.path.isdir(self.dir+'/'+self.fns[self.ctr]):
			if self.fns[self.ctr] == '.gif_cache': # config folder not for viewing
				self.ctr+=1
				return
			if self.first:
				self.progress.value+=1
				
			self.fNames.append('{}/{}'.format(self.dir,self.fns[self.ctr]))
			self.thumbnail = Image(source='img/System-folder-icon.png',size_hint=(None,None),
					allow_stretch=True, keep_ratio=False)
			label = Label(text=label_fn, text_size=(100, None))
			
		else:
			self.ctr+=1
			return
			
		# thumb_layout size defaults to 100,100 so all children will extend past layout without increasing size
		thumb_layout = BoxLayout(orientation='vertical', size_hint=(None,None), spacing=15) 
		thumb_layout.add_widget(self.thumbnail)
		thumb_layout.add_widget(label)
		
		self.stack_layout.add_widget(thumb_layout,
				index=len(self.stack_layout.children)) # add widgets to end 	
		self.ctr+=1
		
	
	def load_buttons(self, dt):
		for layout in self.stack_layout.children: # images are children to boxlayouts which are child to stacklayout
			image = layout.children[1] # widgets are added to front of list not end 
			btn = Button(background_normal='img/alpha.png',pos=(image.x, image.y))
			btn.bind(on_release=self.gif_press)
			image.add_widget(btn)
		# navbar canvas objects	
		with self.navbar.canvas.before:
			Color(92/360,92/360,92/360,1) 
			Rectangle(pos=self.navbar.pos, size=(self.app.root.width,40))
		# navbar dir btn property updates
		self.folder_btn.children[0].source = 'img/folder.png'
		self.folder_btn.children[0].x = self.folder_btn.x
		self.folder_btn.children[0].y = self.folder_btn.y+4 # why +5?
		try:
			self.back_btn.children[0].source = 'img/back.png'
			self.back_btn.children[0].pos = self.back_btn.pos
		except Exception as e:
			print('\n\n\n'+str(e)+'\n\n\n')
			
		
	def gif_press(self, instance):
		for i in range(len(self.fNames)): #fNames same len as stacklayout children
			if instance == self.stack_layout.children[i].children[1].children[0]:
				# loop continues at some unkown point when widgets have been removed resulting in index error
				# return breaks the loop so..
				return self.gifView(self.fNames[i], instance) 
	
	
	def gifView(self, source, widget):		
		if os.path.isdir(source):
			self.dirNames.insert(0, self.dir) # self.dir is cwd - when going back will be parent(s) to subdir(s)
			self.load_layout(source, 'subdir')
		else:
			self.gif = Video(source=source, volume=0, state='play', anim_loop=0, \
									allow_stretch=True, size_hint=(1,0.85), pos_hint={'y':0.15})
			self.slider = Slider(size_hint=(0.9,None), height=10, pos_hint={'center_x':0.5, 'y':0.1})
			
			relative_layout = RelativeLayout()
			relative_layout.add_widget(self.gif)
			relative_layout.add_widget(self.slider)
			popup = Popup(title=source, size_hint=(0.9,0.95), content=relative_layout)
			popup.open()	
			
			self.loaded_check = Clock.schedule_interval(self.gif_loaded, 0)
			
	def gif_loaded(self, dt):
		if self.gif.loaded:
			self.slider.max=self.gif.duration
			self.loaded_check.cancel()
			# gif.duration / (gif.duration // 1) - in order for slider movement to be truly accurate to len of video
			slider_update = Clock.schedule_interval(self.update_slider, self.gif.duration / (self.gif.duration // 1))
	
	def update_slider(self, dt):
		print(self.gif.position)
		self.slider.value+=1
		# rounding of floating point division for silder_update implies slight difference 
		# between final clock callback video.position and actual video.duration
		if (self.gif.position // 1) == (self.gif.duration // 1): 
			return False

	
	def back_btn_setup(self, instance):
		previous_dir = self.dirNames[0]
		if len(self.dirNames)==1:
			del self.dirNames[0]
			self.load_layout(previous_dir) 
		else: 
			del self.dirNames[0]
			self.load_layout(previous_dir,'subdir')
		


class GifApp(App):
	
	def build(self):
		return RootWidget()
		
		
		
GifApp().run()
