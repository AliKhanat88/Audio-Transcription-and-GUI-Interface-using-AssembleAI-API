import requests
import json
import time
import os
from collections import defaultdict
import time

your_api_token = "aa9d5d03ebbb425c9c7b5adec67fe8cb"

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

def main():
    dict = defaultdict(lambda:False)

    print("At the end of folder path, always write / if you are using Mac and \ if you are using Windows.")
    # Source Folder
    pickingFolder = input("Please enter the source folder: ")
    while not os.path.exists(pickingFolder) or pickingFolder[-1] not in ("/", "\\"):
        print("This folder does not exist.")
        pickingFolder = input("Please enter the source folder: ")

    # Destination Folder
    destinationFolder = input("Please enter the destination folder: ")
    while not os.path.exists(destinationFolder) or destinationFolder[-1] not in ("/", "\\"):
        print("This folder does not exist.")
        destinationFolder = input("Please enter the destination folder: ")

    destinationFiles = os.listdir(destinationFolder)

    while True:
        files = os.listdir(pickingFolder)
        for file in files:
            filename, extension = os.path.splitext(file)
            if extension in (".mp3", ".wav", ".m4a"):
                if dict[file] == False and filename + ".txt" not in destinationFiles:
                    print(f"{file} => ", end="")
                    try:
                        # Upload a local file
                        upload_url = upload_file(your_api_token, pickingFolder + file)

                        # Transcribe it
                        transcript = create_transcript(your_api_token, upload_url)

                        # Print the completed transcript object
                        temp_file = open(f"{destinationFolder}{filename}.txt", "w")
                        writeUtterances(temp_file, transcript["utterances"])
                        temp_file.close()
                        dict[file] = True
                        print("Success")
                    except:
                        print("Failure")
        print("Cheking for new files!!!")
        time.sleep(3)

        


if __name__ == "__main__":
    main()