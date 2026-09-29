# LiteLLM Proxy Image Generation Vignette

This vignette shows how to generate images through LiteLLM Proxy and save them locally. Note: this vignette was generated with GPT 5.3 Codex and may contain inaccuracies. Use at your own risk.

## 1) Add variables to `.env`

```env
LITELLM_PROXY_URL=https://litellm.toxpipe.niehs.nih.gov
LITELLM_PROXY_API_KEY=your_proxy_key_here

# Model alias/name exposed by your LiteLLM proxy
LITELLM_IMAGE_MODEL=openai/azure-gpt-image-2

# Optional: path to CA bundle/cert if your environment requires custom trust
LITELLM_PROXY_CA_CERT_PATH=
```

## 2) Install dependencies

```bash
pip install litellm python-dotenv
```

## 3) Example script: `examples/litellm_image_vignette.py`

```python
from pathlib import Path
import base64
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
    model = _require_env("LITELLM_IMAGE_MODEL")

    ca_cert_path = os.getenv("LITELLM_PROXY_CA_CERT_PATH", "").strip()
    if ca_cert_path:
        os.environ["REQUESTS_CA_BUNDLE"] = ca_cert_path

    response = litellm.image_generation(
        model=model,
        api_base=api_base,
        api_key=api_key,
        prompt=(
            "A scientific infographic style image of a modular toxicology AI pipeline, "
            "with clean labels, neutral colors, and white background."
        ),
    )

    b64_string = response.data[0].b64_json
    image_bytes = base64.b64decode(b64_string)

    output_path = Path("litellm-generated-image.png")
    output_path.write_bytes(image_bytes)
    print(f"Saved image to {output_path.resolve()}")


if __name__ == "__main__":
    main()
```

## 4) Run

```bash
python examples/litellm_image_vignette.py
```

If successful, you should get `litellm-generated-image.png` in your working directory.

## Notes

- If your proxy exposes a different image model alias, update `LITELLM_IMAGE_MODEL` in `.env`.
- Keep `.env` local and never commit real keys.
