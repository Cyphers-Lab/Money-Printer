#!/usr/bin/env python3
"""Utility script to list available Azure neural voices and test them."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tts_generator import TTSGenerator
from config.settings import Settings

def main():
    settings = Settings()
    if not settings.AZURE_TTS_KEY:
        print("\nError: AZURE_TTS_KEY not set. Please set it in your environment variables.")
        print("You can get a key from: https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/")
        sys.exit(1)
        
    try:
        tts = TTSGenerator(settings)
    except Exception as e:
        print(f"\nError initializing TTS: {e}")
        sys.exit(1)
    
    print("\nAvailable Azure Neural Voices:")
    print("----------------------------")
    
    voices = tts.get_available_voices()
    voice_list = list(voices.items())
    
    for i, (name, voice_id) in enumerate(voice_list, 1):
        print(f"\n{i}. {name}")
        print(f"   Voice ID: {voice_id}")
    
    while True:
        try:
            choice = input("\nOptions:")
            print("1-9: Test a voice")
            print("r: Adjust rate (-100 to +100)")
            print("p: Adjust pitch (-100 to +100)")
            print("q: Quit")
            print("\nEnter choice: ")
            
            choice = choice.lower()
            if choice == 'q':
                break
                
            if choice == 'r':
                try:
                    rate = int(input("Enter rate (-100 to +100, 0 is normal): "))
                    if -100 <= rate <= 100:
                        settings.TTS_RATE = rate
                        print(f"Rate set to {rate}%")
                    else:
                        print("Invalid rate value. Must be between -100 and +100")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                continue
                
            if choice == 'p':
                try:
                    pitch = int(input("Enter pitch (-100 to +100, 0 is normal): "))
                    if -100 <= pitch <= 100:
                        settings.TTS_PITCH = pitch
                        print(f"Pitch set to {pitch}%")
                    else:
                        print("Invalid pitch value. Must be between -100 and +100")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                continue
                
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(voice_list):
                    name, voice_id = voice_list[idx]
                    print(f"\nTesting voice: {name}")
                    tts.set_voice(voice_id)
                    
                    test_text = "This is a test of the selected neural voice. How does it sound?"
                    print("Generating audio...")
                    tts.generate_audio(test_text)
                    print("\nTest audio generated as 'narration.mp3' in the temp directory")
                    print("\nTo use this voice, set these environment variables:")
                    print(f"AZURE_TTS_VOICE={voice_id}")
                    if settings.TTS_RATE != 0:
                        print(f"TTS_RATE={settings.TTS_RATE}")
                    if settings.TTS_PITCH != 0:
                        print(f"TTS_PITCH={settings.TTS_PITCH}")
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or command letter.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
