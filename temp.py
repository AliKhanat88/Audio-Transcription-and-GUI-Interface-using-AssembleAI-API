from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
import string
import os

class FolderPopup(Popup):
    def __init__(self,drive, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.content = BoxLayout(orientation='vertical')
        self.fileChooser = FileChooserIconView(path=drive, dirselect=True)
        self.content.add_widget(self.fileChooser)
        self.content.add_widget(Button(text="Choose", on_press=self.on_choose, size_hint= (0.2, 0.1), pos_hint= {'center_x': 0.9}))
        self.auto_dismiss = False
        self.title = "Select Folder"

    def on_choose(self, button):
        self.callback(self.fileChooser.path)
        self.dismiss()
        

class DrivePopup(Popup):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.drives = [f"{drive}:\\" for drive in string.ascii_uppercase if os.path.exists(f"{drive}:\\")]
        self.content = BoxLayout(orientation='vertical',pos_hint= {'center_x': 0.1, 'center_y': 1.2})
        for drive in self.drives:
            self.content.add_widget(Button(text=drive, on_press=self.on_choose, size_hint= (None, None), width= 200))
        self.auto_dismiss = False
        self.title = "Select Drive"

    def on_choose(self, button):
        self.dismiss()
        FolderPopup(drive=button.text, callback=self.callback).open()
        



class myApp(App):
    def build(self):
        self.ding = "sklak"
        return Button(text="Open", on_press=self.openPopup)
    

    def openPopup(self, button):
        DrivePopup(callback=self.on_folder_selected).open()

    def on_folder_selected(self, path):
        print(self.ding)
    
if __name__ == "__main__":
    myApp().run()



