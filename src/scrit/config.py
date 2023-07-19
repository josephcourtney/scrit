import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    loopback_device: str
    sas_path: Path
    model: str
    model_choices: list[str]
    energy_threshold: int
    record_timeout: float
    phrase_timeout: float
    tap_map: dict[str, str]
    tap_map_rev: dict[str, str]
    language_suffix: str
    copy_to_clipboard: bool
    write_to_file: bool
    output_path: Path

    @classmethod
    def load(cls):
        with (Path(__file__).parent / "settings.json").open("r") as f:
            config_dict = json.load(f)

        if not config_dict["sas_path"]:
            sas_path = shutil.which("SwitchAudioSource")
            if sas_path is None:
                msg = (
                    "could not change audio source. "
                    "make sure that SwitchAudioSource is installed and in your path. "
                    'it can be installed with "brew install switchaudio-osx" '
                )
                raise RuntimeError(msg)

        tap_map = {
            e["output_device"]: e["tapped_output_device"]
            for e in config_dict["tap_map"]
        }
        tap_map_rev = {v: k for k, v in tap_map.items()}

        output_path = Path(config_dict["output_path"]).absolute()
        return cls(
            loopback_device=config_dict["loopback_device"],
            sas_path=sas_path,
            model=config_dict["model"],
            model_choices=config_dict["model_choices"],
            energy_threshold=config_dict["energy_threshold"],
            record_timeout=config_dict["record_timeout"],
            phrase_timeout=config_dict["phrase_timeout"],
            tap_map=tap_map,
            tap_map_rev=tap_map_rev,
            language_suffix=(".en" if config_dict["english"] else ""),
            copy_to_clipboard=config_dict["copy_to_clipboard"],
            write_to_file=False,
            output_path=output_path,
        )

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--edit_config",
            help="change mapping of audio devices to tapped versions",
            action="store_true",
        )
        parser.add_argument(
            "--model",
            default=self.model,
            help="Model to use",
            choices=self.model_choices,
        )
        parser.add_argument(
            "--non_english",
            action="store_true",
            help="Don't use the english model.",
        )
        parser.add_argument(
            "--energy_threshold",
            default=self.energy_threshold,
            help="Energy level for mic to detect.",
            type=int,
        )
        parser.add_argument(
            "--record_timeout",
            default=self.record_timeout,
            help="How real time the recording is in seconds.",
            type=float,
        )
        parser.add_argument(
            "--phrase_timeout",
            default=self.phrase_timeout,
            help="How much empty space between recordings before we "
            "consider it a new line in the transcription.",
            type=float,
        )
        parser.add_argument(
            "--clipboard",
            help="copy final transcript to clipboard",
            action="store_false",
        )
        parser.add_argument(
            "--out",
            help="output file for final transcript",
            type=lambda p: Path(p).absolute(),
        )
        args = parser.parse_args()

        if args.edit_config:
            self.edit()

        self.model = args.model
        if self.model not in self.model_choices:
            msg = f"model ({self.model}) must be one of {self.model_choices}"
            raise ValueError(msg)

        if args.non_english:
            self.language_suffix = ""
        else:
            self.language_suffix = ".en"

        self.energy_threshold = args.energy_threshold
        self.record_timeout = args.record_timeout
        self.phrase_timeout = args.phrase_timeout

        self.copy_to_clipboard = args.clipboard
        self.write_to_file = bool(args.out)
        self.output_path = args.out

    def edit(self):
        vim_path = shutil.which("vim")
        subprocess.run(
            [vim_path, Path(__file__).parent / "settings.json"],  # noqa: S603
            check=True,
        )
        sys.exit()
