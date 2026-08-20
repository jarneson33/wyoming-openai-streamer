from __future__ import annotations

import os
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Tuple
from openai import OpenAI

@dataclass
class AudioFormat:
    rate: int      # Hz
    width: int     # bytes per sample (e.g., 2 for 16-bit)
    channels: int  # 1=mono, 2=stereo

class BaseTTSEngine:
    """Uniform async streaming API for TTS engines.

    stream(text, voice_name, cli_args) -> async generator that yields:
      ('format', AudioFormat) exactly once, then
      ('chunk', bytes) one or more times with PCM frames.
    """
    async def stream(
        self, text: str, voice_name: str, cli_args
    ) -> AsyncGenerator[Tuple[str, object], None]:
        raise NotImplementedError

class OpenAITTSEngine(BaseTTSEngine):
    """Uses OpenAI TTS streaming; SDK streams WAV by default, so strip header once."""

    def __init__(self) -> None:
        self.default_model = "gpt-4o-mini-tts"

    def _parse_speed(self) -> Optional[float]:
        speed_raw = os.getenv("OPENAI_TTS_SPEED", "").strip()
        if not speed_raw:
            return None

        try:
            speed = float(speed_raw)
        except ValueError:
            return None

        # OpenAI speed range
        if speed < 0.25:
            return 0.25
        if speed > 4.0:
            return 4.0
        return speed

    def _create_client(self) -> OpenAI:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()

        client_kwargs = {}
        if base_url:
            client_kwargs["base_url"] = base_url

        if api_key:
            client_kwargs["api_key"] = api_key
        elif base_url:
            # Some OpenAI-compatible local providers don't require a real key,
            # but the SDK expects a non-empty api_key value.
            client_kwargs["api_key"] = "not-needed"

        return OpenAI(**client_kwargs)

    def _parse_voice(self, voice_name: str) -> str:
        # Accept "en-US-openai-alloy" or plain "alloy"
        n = voice_name.strip()
        if "-openai-" in n.lower():
            return n.split("-openai-", 1)[1]
        return n

    async def stream(
        self, text: str, voice_name: str, cli_args
    ) -> AsyncGenerator[Tuple[str, object], None]:
        client = self._create_client()
        voice = self._parse_voice(voice_name)

        # Resolve model precedence: ENV > default
        model = os.getenv("OPENAI_TTS_MODEL") or self.default_model
        speed = self._parse_speed()

        # WAV header parsing state
        got_header = False
        header_buf = b""

        # Fallbacks until header is parsed
        sample_rate = 24000
        channels = 1
        width = 2

        def try_parse_wav_header(buf: bytes):
            # Minimal RIFF/WAVE PCM parse; returns (ok, data_offset, sr, ch, width_bytes)
            if len(buf) < 44:
                return (False, 0, None, None, None)
            if not (buf[0:4] == b"RIFF" and buf[8:12] == b"WAVE"):
                # If it's already raw PCM for some reason
                return (True, 0, None, None, None)
            ch = int.from_bytes(buf[22:24], "little", signed=False)
            sr = int.from_bytes(buf[24:28], "little", signed=False)
            bits = int.from_bytes(buf[34:36], "little", signed=False)
            data_offset = 44
            return (True, data_offset, sr, ch, (bits // 8) if bits else None)

        # Start streaming; no 'format'/'sample_rate' kwargs here
        request_kwargs = {
            "model": model,
            "voice": voice,
            "input": text,
        }
        if speed is not None:
            request_kwargs["speed"] = speed

        with client.audio.speech.with_streaming_response.create(**request_kwargs) as resp:
            # We'll emit ('format', ...) once we know the real numbers
            for chunk in resp.iter_bytes():
                if not chunk:
                    continue

                if not got_header:
                    header_buf += chunk
                    ok, data_off, sr, ch, w = try_parse_wav_header(header_buf)
                    if not ok:
                        continue

                    if sr: sample_rate = sr
                    if ch: channels = ch
                    if w:  width = w

                    # Announce real audio format now
                    yield ("format", AudioFormat(rate=sample_rate, width=width, channels=channels))

                    # Emit any payload trailing the header
                    payload = header_buf[data_off:]
                    if payload:
                        yield ("chunk", payload)

                    got_header = True
                    continue

                # After header all chunks are PCM
                yield ("chunk", chunk)

class EngineRegistry:
    def __init__(self) -> None:
        self._engines = {
            "openai": OpenAITTSEngine(),
        }

    def pick(self, voice_name: str) -> Tuple[str, BaseTTSEngine, str]:
        """Return (provider, engine, normalized_voice) based on voice_name."""
        v = (voice_name or "").strip().lower()
        return ("openai", self._engines["openai"], v)

ENGINE_REGISTRY = EngineRegistry()
