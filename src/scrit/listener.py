import datetime
import io
import warnings
from pathlib import Path
from queue import Queue
from tempfile import NamedTemporaryFile

import speech_recognition as sr
import torch
from numba import NumbaDeprecationWarning

warnings.simplefilter("ignore", category=NumbaDeprecationWarning)
import whisper  # noqa: E402


class Listener:
    def __init__(self, config):
        # The last time a recording was retreived from the queue.
        self.utterance_time = None
        # Current raw audio bytes.
        self.last_sample = b""
        # Thread safe Queue for passing data from the threaded recording callback.
        self.data_queue = Queue()
        # We use SpeechRecognizer to record our audio because it has a nice feauture
        # where it can detect when speech ends.
        recorder = sr.Recognizer()
        recorder.energy_threshold = config.energy_threshold
        # Definitely do this, dynamic energy compensation lowers the energy threshold
        # dramtically to a point where the SpeechRecognizer never stops recording.
        recorder.dynamic_energy_threshold = False

        self.source = sr.Microphone(sample_rate=16000)

        # Load / Download model
        self.audio_model = whisper.load_model(config.model + config.language_suffix)

        with self.source:
            recorder.adjust_for_ambient_noise(self.source)

        # Create a background thread that will pass us raw audio bytes.
        recorder.listen_in_background(
            self.source,
            self.record_callback,
            phrase_time_limit=config.record_timeout,
        )

        self.utterance_complete = False
        self.current_utterance = ""
        self.utterance_timeout = config.phrase_timeout
        self.temp_file = Path(NamedTemporaryFile().name)
        self.running = True

    def record_callback(self, _, audio: sr.AudioData) -> None:
        # Grab the raw bytes and push it into the thread safe queue.
        self.data_queue.put(audio.get_raw_data())

    def stop(self):
        self.running = False

    def __iter__(self):
        while True:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if not self.running:
                return

            # Pull raw recorded audio from the queue.
            if not self.data_queue.empty():
                self.utterance_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if (
                    self.utterance_time
                    and now - self.utterance_time
                    > datetime.timedelta(
                        seconds=self.utterance_timeout,
                    )
                ):
                    self.last_sample = b""
                    self.utterance_complete = True
                # This is the last time we received new audio data from the queue.
                self.utterance_time = now

                # Concatenate our current audio data with the latest audio data.
                while not self.data_queue.empty():
                    data = self.data_queue.get()
                    self.last_sample += data

                # Use AudioData to convert the raw data to wav data.
                audio_data = sr.AudioData(
                    self.last_sample,
                    self.source.SAMPLE_RATE,
                    self.source.SAMPLE_WIDTH,
                )
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # Write wav data to the temporary file as bytes.
                with self.temp_file.open("w+b") as f:
                    f.write(wav_data.read())

                # Read the transcription.
                result = self.audio_model.transcribe(
                    str(self.temp_file),
                    fp16=torch.cuda.is_available(),
                )
                self.current_utterance = result["text"].strip()

                yield self.current_utterance, self.utterance_complete
