"""
Silero Voice Activity Detection service.

only detects speech right now , no warm up models
"""

import numpy as np
import torch

from silero_vad import (
    load_silero_vad,
    get_speech_timestamps
)


class SileroVADService:

    def __init__(self):

        self.model = load_silero_vad()

        self.sample_rate = 16000


    def detect_speech(
        self,
        audio_bytes: bytes
    ) -> bool:

        try:

            audio_np = np.frombuffer(
                audio_bytes,
                dtype=np.int16
            )

            if len(audio_np) == 0:
                return False

            audio_float = (
                audio_np.astype(np.float32)
                / 32768.0
            )

            audio_tensor = torch.from_numpy(
                audio_float
            )

            speech = get_speech_timestamps(
                audio_tensor,
                self.model,
                sampling_rate=self.sample_rate
            )

            return len(speech) > 0

        except Exception as error:

            print(
                f"VAD Error: {error}",
                flush=True
            )

            return False