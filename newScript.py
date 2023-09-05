from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import requests
import os
import time
import threading
from kivy.config import Config
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
import string
import os

Config.set('kivy', 'log_level', 'warning')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
your_api_token = "aa9d5d03ebbb425c9c7b5adec67fe8cb"

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
        self.content = BoxLayout(orientation='vertical')
        for drive in self.drives:
            self.content.add_widget(Button(text=drive, on_press=self.on_choose, size_hint= (None, None), width= 200))
        self.auto_dismiss = False
        self.title = "Select Drive"

    def on_choose(self, button):
        self.dismiss()
        FolderPopup(drive=button.text, callback=self.callback).open()

def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data

def upload_file(api_token, path):
    """
    Upload a file to the AssemblyAI API.

    Args:
        api_token (str): Your API token for AssemblyAI.
        path (str): Path to the local file.

    Returns:
        str: The upload URL.
    """
    headers = {'authorization': api_token}
    response = requests.post('https://api.assemblyai.com/v2/upload',
                             headers=headers,
                             data=read_file(path))

    if response.status_code == 200:
        return response.json()["upload_url"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def create_transcript(api_token, audio_url):
    """
    Create a transcript using AssemblyAI API.

    Args:
        api_token (str): Your API token for AssemblyAI.
        audio_url (str): URL of the audio file to be transcribed.

    Returns:
        dict: Completed transcript object.
    """
    # Set the API endpoint for creating a new transcript
    url = "https://api.assemblyai.com/v2/transcript"

    # Set the headers for the request, including the API token and content type
    headers = {
        "authorization": api_token,
        "content-type": "application/json"
    }

    # Set the data for the request, including the URL of the audio file to be transcribed
    data = {
        "audio_url": audio_url,
        "speaker_labels": True
    }

    # Send a POST request to the API to create a new transcript, passing in the headers and data
    response = requests.post(url, json=data, headers=headers)

    # Get the transcript ID from the response JSON data
    transcript_id = response.json()['id']

    # Set the polling endpoint URL by appending the transcript ID to the API endpoint
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    # Keep polling the API until the transcription is complete
    while True:
        # Send a GET request to the polling endpoint, passing in the headers
        transcription_result = requests.get(polling_endpoint, headers=headers).json()

        # If the status of the transcription is 'completed', exit the loop
        if transcription_result['status'] == 'completed':
            break

        # If the status of the transcription is 'error', raise a runtime error with the error message
        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

        # If the status of the transcription is not 'completed' or 'error', wait for 3 seconds and poll again
        else:
            time.sleep(3)

    return transcription_result

def writeUtterances(file, utterances):
    for utterance in utterances:
        file.write(f"Speaker {utterance['speaker']}\n")
        file.write(f"{utterance['text']}\n")
        file.write("\n")


class appApp(App):
    def build(self):
        self.running = True
        self.root = GridLayout(cols=1, spacing=50, padding=50)
        
        self.status = Label(text="Waiting For Input...")

        self.sourceWidget = GridLayout(cols=3)
        self.sourceText = TextInput()
        self.sourceText.readonly = True
        self.sourceWidget.add_widget(Label(text="[b]Source Path[/b]", markup=True))
        self.sourceWidget.add_widget(self.sourceText)
        self.sourceWidget.add_widget(Button(text="Load", on_press=self.open_source_select,size_hint= (0.2, 1)))

        self.destinationWidget = GridLayout(cols=3)
        self.destinationText = TextInput()
        self.destinationText.readonly = True
        self.destinationWidget.add_widget(Label(text="[b]Destination Path[/b]", markup=True))
        self.destinationWidget.add_widget(self.destinationText)
        self.destinationWidget.add_widget(Button(text="Load", on_press=self.open_destination_select, size_hint= (0.2, 1)))

        self.apiWidget = GridLayout(cols=3)
        self.apiText = TextInput(text="aa9d5d03ebbb425c9c7b5adec67fe8cb")
        self.apiWidget.add_widget(Label(text="[b]API Key[/b]", markup=True))
        self.apiWidget.add_widget(self.apiText)
        self.apiWidget.add_widget(Label(text="", size_hint= (0.2, 1)))
        
        self.buttonEnter = Button(text="Enter")
        self.buttonEnter.bind(on_release=self.onEnter)

        self.completed = Label(text=f"Completed  0", size_hint = (0.1, 0.1))

        self.processing = Label(text=f"Processing   0", size_hint = (0.1, 0.1))


        self.root.add_widget(self.status)
        self.root.add_widget(self.sourceWidget)
        self.root.add_widget(self.destinationWidget)
        self.root.add_widget(self.apiWidget)
        self.root.add_widget(self.buttonEnter)
        self.root.add_widget(self.completed)
        self.root.add_widget(self.processing)

        return self.root
    
    def open_source_select(self, button):
        DrivePopup(callback=self.on_source_selected).open()

    def on_source_selected(self, path):
        self.sourceText.text = path

    def open_destination_select(self, button):
        DrivePopup(callback=self.on_destination_selected).open()

    def on_destination_selected(self, path):
        self.destinationText.text = path
    
    def processFiles(self, pickingFolder, destinationFolder):
        self.status.text = "Searching for files..."
        completed = 0
        while self.running:
            files = os.listdir(pickingFolder)
            destinationFiles = os.listdir(destinationFolder)
            processing = len(files)
            time.sleep(60)
            for file in files:
                filename, extension = os.path.splitext(file)
                if extension in (".mp3", ".wav", ".m4a") and filename + ".txt" not in destinationFiles:
                        try:
                            self.status.text = f"Transcribing {file}"
                            # Upload a local file
                            upload_url = upload_file(your_api_token, f"{pickingFolder}\\{file}")

                            # Transcribe it
                            transcript = create_transcript(your_api_token, upload_url)

                            # Print the completed transcript object
                            temp_file = open(f"{destinationFolder}\\{filename}.txt", "w")
                            writeUtterances(temp_file, transcript["utterances"])
                            temp_file.close()
                            completed += 1
                            self.completed.text = f"Completed  {completed}"
                        except:
                            pass
                processing -= 1
                self.processing.text = f"Processing  {processing}"
            self.status.text = "Searching for files..."

    def onEnter(self, button):
        
        pickingFolder = self.sourceText.text

        if pickingFolder == "" or not os.path.exists(pickingFolder):
            self.status.text = "This source path does not exist."
            return
        
        # Destination Folder
        destinationFolder = self.destinationText.text
        if destinationFolder == "" or not os.path.exists(destinationFolder):
            self.status.text = "This destination folder does not exist."
            return
        
        if self.apiText.text.strip() == "":
            self.status.text = "Api key is empty"
            return
        
        self.buttonEnter.disabled = True

        global your_api_token 
        your_api_token = self.apiText.text
        threading.Thread(target=self.processFiles, args=[pickingFolder, destinationFolder], daemon=True).start()


if __name__ == "__main__":
    appApp().run()
