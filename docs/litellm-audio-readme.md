# LiteLLM Proxy Audio Vignette (TTS + STT)

This vignette shows how to call Text-to-Speech (TTS) and Speech-to-Text (STT) models through your LiteLLM Proxy endpoint. Note: this vignette was generated with GPT 5.3 Codex and may contain inaccuracies. Use at your own risk.

## 1) Add variables to `.env`

```env
LITELLM_PROXY_URL=https://litellm.toxpipe.niehs.nih.gov
LITELLM_PROXY_API_KEY=your_proxy_key_here

# Model aliases/names exposed by your LiteLLM proxy
LITELLM_TTS_MODEL=openai/azure-gpt-4o-mini-tts
LITELLM_STT_MODEL=openai/whisper-1

# Optional: path to CA bundle/cert if your environment requires custom trust
LITELLM_PROXY_CA_CERT_PATH=
```

## 2) Install dependencies

```bash
pip install litellm python-dotenv
```

## 3) Example script: `examples/litellm_audio_vignette.py`

```python
from pathlib import Path
import os

from dotenv import load_dotenv
import litellm


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    load_dotenv()

    api_base = _require_env("LITELLM_PROXY_URL")
    api_key = _require_env("LITELLM_PROXY_API_KEY")
    tts_model = _require_env("LITELLM_TTS_MODEL")
    stt_model = _require_env("LITELLM_STT_MODEL")

    ca_cert_path = os.getenv("LITELLM_PROXY_CA_CERT_PATH", "").strip()
    if ca_cert_path:
        os.environ["REQUESTS_CA_BUNDLE"] = ca_cert_path

    # --- TTS: synthesize speech from text ---
    tts_response = litellm.speech(
        model=tts_model,
        api_base=api_base,
        api_key=api_key,
        voice="alloy",
        input="This is a test for ToxPipe LiteLLM Proxy audio generation.",
    )

    tts_out = Path("speech.mp3")
    tts_out.write_bytes(tts_response.read())
    print(f"Saved TTS output to {tts_out.resolve()}")

    # --- STT: transcribe audio file to text ---
    audio_in = Path("speech.mp3")
    with audio_in.open("rb") as audio_fp:
        stt_response = litellm.transcription(
            model=stt_model,
            file=audio_fp,
            api_base=api_base,
            api_key=api_key,
        )

    transcript = stt_response.get("text", "")
    print("Transcription:")
    print(transcript)


if __name__ == "__main__":
    main()
```

## 4) Run

```bash
python examples/litellm_audio_vignette.py
```

If successful, you should get:

- `speech.mp3` written to your working directory
- a transcript printed in the console

## Notes

- If your proxy expects a different model alias, change `LITELLM_TTS_MODEL` and `LITELLM_STT_MODEL` in `.env`.
- Keep `.env` local and never commit real keys.
