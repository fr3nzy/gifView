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
from kivy.uix.video import Video
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

import os, subprocess


class RootWidget(RelativeLayout):

	def __init__(self):
		super(RootWidget, self).__init__()
	
	@staticmethod
	def select_folder():
		Interface()



# TODO events aren't triggered if class doesn't inherit from widget 
# TODO apparently widget is the kivy base class - it seems required for full functionality
# TODO when is it actually used?
# TODO Why do we inherit from Widget() class, bind doesn't work without it, 

#TODO understand gui main loop and why waiting for frames is important

# TODO load pop_layout when 'folder' button is pressed
class Interface(Widget):

	def __init__(self):
		super().__init__()
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
				size_hint=(0.5,0.5), auto_dismiss=False)
		self.popup.open()		
	
	
	# on_press event triggers callback passed with parameter - instance of btn here
	def btn_press(self, instance):
		self.popup.dismiss()
		self.app = App.get_running_app()
		self.app.root.remove_widget(self.app.root.ids.open_popup) 
		
		dirName = os.environ['HOME']+'/Pictures' if self.txt_input.text == '' \
					else self.txt_input.text
		Clock.schedule_once(lambda dt: self.load_layout(dirName, 'first run'), 0.13)
		
		
	def load_layout(self, dir, *args):
		self.dir = dir
		
		##########################################################
		###################### base layout ############################
		
		try:
			if len(self.stack_layout.children)>0: # has stack_layout been been instantiated before?
				self.app.root.remove_widget(self.scroll_layout)
				self.app.root.remove_widget(self.app.root.children[0])
		except Exception as e:
			print(e)
		
		
		# navbar canvas objects load on next frame(s) load_button() so attributes have loaded
		self.navbar = Widget(size_hint=(None,None), pos_hint={'y':0.932})
		self.app.root.add_widget(self.navbar)
		
		if 'subdir' in args:
			back_btn = Button(text='Back', \
										size_hint=(None,None), \
										size=(80,30), \
										pos_hint={'x': 0.03, 'center_y': 0.963})
			back_btn.bind(on_press=lambda instance: self.load_layout(args[1]))
			self.app.root.add_widget(back_btn)
		
		folder_btn = Button(text='folder', \
									size_hint=(None,None), \
									size=(80,30), \
									pos_hint={'x': 0.89,'center_y': 0.963})
		self.app.root.add_widget(folder_btn)
		
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
		
		Clock.schedule_once(lambda dt: self.load_thumbnails(), 0.15)
	
	
	def load_thumbnails(self):
		img_ctr,self.total_ctr=0,1 # for variable thumbnail names
		self.fNames = []
		for fn in os.listdir(self.dir):
		
			if fn[-4:] == 'webm':
				thumbnail_fn = self.dir+'/'+'.gif_cache'+'/'+str(img_ctr)+'img.jpg'
				if self.first: # create thumbnails
					# get first frame of webm <fn>
					subprocess.call(['ffmpeg', '-i', self.dir+'/'+fn, '-ss', '00:00:00.0', '-vframes', '1', thumbnail_fn])
					Clock.schedule_once(self.update_progress, 0.1)
					
					
				self.fNames.append('{}/{}'.format(self.dir,fn))
				self.thumbnail = Image(source=thumbnail_fn,size_hint=(None,None),
						allow_stretch=True, keep_ratio=False)
				label = Label(text=fn[:10]+'..', text_size=(100, None))
				img_ctr+=1
				self.total_ctr+=1
			
			elif os.path.isdir(self.dir+'/'+fn):
				if fn == '.gif_cache': # config folder not for viewing
					continue
				self.fNames.append('{}/{}'.format(self.dir,fn))
				self.thumbnail = Image(source='img/System-folder-icon.png',size_hint=(None,None),
						allow_stretch=True, keep_ratio=False)
				label = Label(text=fn[:10]+'..', text_size=(100, None))
				self.total_ctr+=1
			else:
				continue
				
			# thumb_layout size defaults to 100,100 so all children will extend past layout without increasing size
			thumb_layout = BoxLayout(orientation='vertical', size_hint=(None,None), spacing=15) 
			thumb_layout.add_widget(self.thumbnail)
			thumb_layout.add_widget(label)
			
			self.stack_layout.add_widget(thumb_layout,
					index=len(self.stack_layout.children)) # add widgets to end 	
		
		# relate stack_layout height to number of children - to allow scroll child must be larger than scroll
		height = sum([100/4.5 for child in self.stack_layout.children])
		self.stack_layout.height = height
		
		try:
			self.loading_popup.dismiss()
		except Exception as e:
			print('\n\n\n'+str(e)+'\n\n\n')
		
		Clock.schedule_once(self.load_buttons) # next frame - required for widgets to update attributes
		
	
	def load_buttons(self, dt):
		for layout in self.stack_layout.children: # images are children to gridlayouts which are child to stacklayout
			image = layout.children[1] # widgets are added to front of list not end 
			btn = Button(background_normal='img/alpha.png',pos=(image.x, image.y))
			btn.bind(on_press=self.gif_press)
			image.add_widget(btn)
		# navbar canvas objects	
		with self.navbar.canvas.before:
			Color(92/360,92/360,92/360,1) 
			Rectangle(pos=self.navbar.pos, size=(self.app.root.width,40))
			
		
	def gif_press(self, instance):
		for i in range(len(self.fNames)): #fNames same len as stacklayout children
			if instance == self.stack_layout.children[i].children[1].children[0]:
				# loop continues at some unkown point when widgets have been removed resulting in index error
				# return breaks the loop so..
				return self.gifView(self.fNames[i]) 
	
	
	def gifView(self, source):
		if os.path.isdir(source):
			self.load_layout(source, 'subdir', self.dir) # self.dir is current working dir before moving to subdir
		else:
			gif = Video(source=source, volume=0, state='play', anim_loop=0, allow_stretch=True)
			popup = Popup(title=source, size_hint=(0.6,0.6),content=gif)
			popup.open()
			
	def update_progress(self, dt):
		self.progress.value = self.total_ctr
		print(self.progress.value)



class GifApp(App):
	
	def build(self):
		return RootWidget()
		
		
		
GifApp().run()
