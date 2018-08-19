import kivy

from kivy.config import Config
Config.set('graphics','resizable',0)

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock

import os

# TODO show load dialog whilst thumbnails load, add label with name of image below the image buttons. switch image buttons so button is child to image so visual feedback is present when selecting a thumbnail. Move loading thumbnails to seperate class to keep FolderPopup() entirely for popup function and representation

# no idea why **kwargs required in RootWidget __init__ 
# all init functions in classes inheriting from kivy widgets must pass **kwargs to super constructor
class RootWidget(RelativeLayout):

	def __init__(self):
		super(RootWidget, self).__init__()
		self.ids.scroll_layout.size_hint = (None,None)
	
	@staticmethod
	def select_folder():
		FolderPopup()



# events aren't triggered if class doesn't inherit from widget 
# apparently widget is the kivy base class - it seems required for full functionality
class FolderPopup(Widget):

	def __init__(self):
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
		# why go through app.root - if Widget is parent class why does remove_widget not work?
		self.app.root.remove_widget(self.app.root.ids.open_popup) 
		self.app.root.ids.scroll_layout.size_hint = (1,1)
		
		self.dirName = os.environ['HOME']+'/Pictures' if self.txt_input.text == '' else self.txt_input.text
		
		# load image buttons based on number of images
		self.fileNames = []
		for fn in os.listdir(self.dirName):
			if fn[-3:] == 'jpg':
				self.fileNames.append(fn)
				
				btn = Button(size_hint=(None,None),background_normal='img/alpha.png')
				btn.bind(on_press=self.gif_press)
						
				self.app.root.ids.stack_layout.add_widget(btn,
						index=len(self.app.root.ids.stack_layout.children)) # add widgets to end 	
		Clock.schedule_once(self.load_thumbnails) # requires dt argument - wait for next frame
				
		# root is presumably created in the GifApp().run() or __init__ method
		# root is an attribute of app, root points to an instance of RootWidget
		# ids is child of root and a list of weak references to Widget instances in kv file
		# stack_layout is weak reference to widget with id stack_layout
		# children is list of objects child to stack_layout widget - new widgets added to front of list
		print(self.app.root.ids.stack_layout.children)
		#  ids contains a list of weakproxy references to the objects referenced by ids
		# what is weakproxy?
		
		
	def load_thumbnails(self, dt):
		# add images to image buttons				
		ctr=0
		for widget in self.app.root.ids.stack_layout.children: # len = len(self.fileNames)
					widget.add_widget(Image(
							source=self.dirName+'/'+self.fileNames[len(self.fileNames)-(ctr+1)], 
							allow_stretch=True, keep_ratio=False, pos=(widget.x,widget.y)))
					ctr+=1
	
		
	def gif_press(self, instance):
		for i in range(len(self.app.root.ids.stack_layout.children)):
			if self.app.root.ids.stack_layout.children[i] == instance:
				print(self.fileNames[len(self.app.root.ids.stack_layout.children)-(i+1)])



class ScrollLayout(ScrollView):
	pass
		


class GifApp(App):
	
	def build(self):
		return RootWidget()
		
GifApp().run()
