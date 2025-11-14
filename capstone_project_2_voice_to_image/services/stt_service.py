import audioop
import io
import json
import shutil
import wave
import zipfile
from pathlib import Path
from typing import Dict, Optional
from urllib.request import urlretrieve

import vosk

from services.logger import log


MODEL_REGISTRY: Dict[str, Dict[str, str]] = {
    "vosk-model-en-us-0.22": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
        "archive": "vosk-model-en-us-0.22.zip",
        "folder": "vosk-model-en-us-0.22",
    },
    "vosk-model-en-us-0.22-lgraph": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip",
        "archive": "vosk-model-en-us-0.22-lgraph.zip",
        "folder": "vosk-model-en-us-0.22-lgraph",
    },
    "vosk-model-small-en-us-0.15": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "archive": "vosk-model-small-en-us-0.15.zip",
        "folder": "vosk-model-small-en-us-0.15",
    },
}


class ModelDownloadError(RuntimeError):
    pass


class VoskSTTService:

    def __init__(self, config: Optional[Dict[str, str]] = None) -> None:
        default_config = {
            "model_name": "vosk-model-en-us-0.22",
            "download_dir": Path("models"),
        }
        self._config = {**default_config, **(config or {})}
        self._model_path = self._ensure_model()
        self._model = vosk.Model(str(self._model_path))

    def _ensure_model(self) -> Path:
        model_name = self._config["model_name"]
        if model_name not in MODEL_REGISTRY:
            raise ValueError(
                f"Unknown Vosk model: {model_name}. "
                f"Available options: {', '.join(MODEL_REGISTRY.keys())}"
            )

        info = MODEL_REGISTRY[model_name]
        target_root = Path(self._config["download_dir"])
        target_root.mkdir(parents=True, exist_ok=True)
        extracted_dir = target_root / info["folder"]

        if extracted_dir.exists():
            log(f"Using cached Vosk model at {extracted_dir}.")
            return extracted_dir

        archive_path = target_root / info["archive"]

        if not archive_path.exists():
            try:
                log(f"Downloading Vosk model from {info['url']} ...")
                urlretrieve(info["url"], archive_path)
            except Exception as ex:
                raise ModelDownloadError(
                    f"Failed to download Vosk model: {ex}"
                ) from ex

        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                temp_dir = target_root / "tmp_extract"
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                log("Extracting Vosk model archive...")
                archive.extractall(temp_dir)
                inner_dir = temp_dir / info["folder"]
                if not inner_dir.exists():
                    raise ModelDownloadError(
                        "Vosk archive does not contain the expected directory."
                    )
                shutil.move(str(inner_dir), extracted_dir)
                shutil.rmtree(temp_dir)
        except ModelDownloadError:
            raise
        except Exception as ex:
            raise ModelDownloadError(
                f"Failed to extract Vosk model: {ex}"
            ) from ex

        log(f"Vosk model prepared at {extracted_dir}.")
        return extracted_dir

    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            raise ValueError("Audio payload is empty.")

        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_reader:
            sample_width = wav_reader.getsampwidth()
            if sample_width != 2:
                raise ValueError(
                    "Expected 16-bit PCM audio. Please provide a different recording."
                )

            channels = wav_reader.getnchannels()
            sample_rate = wav_reader.getframerate()
            raw_frames = wav_reader.readframes(wav_reader.getnframes())

        if channels == 0 or sample_rate == 0:
            raise ValueError("Invalid WAV parameters.")

        if channels > 2:
            raise ValueError(
                "Only mono or stereo WAV files are supported. "
                "Please re-record with a single channel."
            )
        if channels == 2:
            raw_frames = audioop.tomono(raw_frames, sample_width, 0.5, 0.5)
            channels = 1

        if sample_rate != 16000:
            raw_frames, _ = audioop.ratecv(
                raw_frames, sample_width, channels, sample_rate, 16000, None
            )
            sample_rate = 16000

        recognizer = vosk.KaldiRecognizer(self._model, sample_rate)
        recognizer.SetWords(True)

        chunks = []
        chunk_size = 4000
        for offset in range(0, len(raw_frames), chunk_size):
            data = raw_frames[offset: offset + chunk_size]
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                chunks.append(result.get("text", ""))

        final_result = json.loads(recognizer.FinalResult())
        chunks.append(final_result.get("text", ""))

        transcript = " ".join(part for part in chunks if part).strip()
        if not transcript:
            transcript = "(no transcription output)"

        log(f"Transcription completed: {transcript}")
        return transcript

