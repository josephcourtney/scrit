# scrit
A simple cli tool to transcribe audio you are already listening to.

<p align="center"><img src="/img/demo.gif?raw=true"/></p>

## Usage
When `%> scrit` runs in a terminal:
- It switches audio devices to capture the system output, without interrupting listening.
- It loads OpenAI's Whisper speech-to-text model
- It continuously transcribes the audio and presents a live-updating transcript
- Upon-receiving ctrl-c, it saves the final transcript to file, or copies it to the clipboard

## Installation
1. Install [BlackHole](https://github.com/ExistentialAudio/BlackHole) or another audio loopback program
2. Set up a multi-output devices to add loopback to the audio output devices you want to use
   - detailed [here](https://github.com/ExistentialAudio/BlackHole#record-system-audio) for BlackHole
   - I found it helpful to name each multi-output device "{Audio Device} (tapped)"
   - Here is the side bar of Audio MIDI Setup for my computer

     ![example audio midi setup sidebar](/img/audio_midi_setup_sidebar.png)
3. install scrit with
    -  `pip install scrit`
4. set up the mapping between tapped and un-tapped audio devices to enable automatic switching.
    - edit the scrit configuration with `scrit --edit_config`
    - in the `tap_map` section of the configuration file, edit the device names to represent the mapping between normal and tapped versions of the output devices

```json
...
    "tap_map": [
        {
            "output_device": "External Headphones",
            "tapped_output_device": "External Headphones (tapped)"
        },
        {
            "output_device": "MacBook Pro Speakers",
            "tapped_output_device": "MacBook Pro Speakers (tapped)"
        },
        {
            "output_device": "AirPods",
            "tapped_output_device": "AirPods (tapped)"
        }
    ]
...
```
    
## Acknowledgments
- This tool is based on https://github.com/davabase/whisper_real_time
- Transcription is performed by the Whisper speech-to-text model from OpenAI (https://github.com/openai/whisper)
- This tool relies on audio loopback performed by [BlackHole](https://github.com/ExistentialAudio/BlackHole) but other tools may also work
