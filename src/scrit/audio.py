import subprocess

import pyaudio


class AudioDeviceHandler:
    def __init__(self, config):
        self.original_input_device = None
        self.original_output_device = None

        self.sas_path = config.sas_path
        self.loopback_device = config.loopback_device
        self.tap_map = config.tap_map
        self.tap_map_rev = config.tap_map_rev

        pa = pyaudio.PyAudio()

        self.audio_devices = {
            pa.get_device_info_by_index(i)["name"]: pa.get_device_info_by_index(i)
            for i in range(pa.get_device_count())
        }

        self.original_input_device = pa.get_default_input_device_info()["name"]
        self.original_output_device = pa.get_default_output_device_info()["name"]

    def setup_loopback(self):
        if self.loopback_device in self.audio_devices:
            self.set_system_audio_device("input", self.loopback_device)

        if self.original_output_device in self.tap_map:
            self.set_system_audio_device(
                "output",
                self.tap_map[self.original_output_device],
            )
        elif self.original_output_device in self.tap_map_rev:
            self.original_output_device = self.tap_map_rev[self.original_output_device]
        else:
            pass

    def set_system_audio_device(self, device_type, device):
        if device not in self.audio_devices:
            msg = (
                f"cannot set {device_type} to {device} because it does not appear in"
                f"device list: {list(self.audio_devices.keys())}"
            )
            raise ValueError(msg)
        return subprocess.run(
            [self.sas_path, "-t", device_type, "-s", device],  # noqa: S603
            check=True,
            capture_output=True,
        )

    def revert(self):
        if self.original_output_device is not None:
            self.set_system_audio_device("output", self.original_output_device)
        if self.original_input_device is not None:
            self.set_system_audio_device("input", self.original_input_device)
