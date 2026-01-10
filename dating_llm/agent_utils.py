import io
import json
from typing import Dict, Any

import requests

from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import ReadTimeout

from PIL import Image


def get_image_data(url: str) -> bytes:
    if url == "":
        return b''
    
    s = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.3,
                    status_forcelist=[ 500, 502, 503, 504 ])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    # print(url)
    for _ in range(5):
        try:
            resp = s.get(url, timeout=3)
            break
        except Exception:
            pass
    s.close()

    resp.raise_for_status()
    orig_bytes: bytes = resp.content
    try:
        img: Image.Image = Image.open(io.BytesIO(orig_bytes))
        # Resize if larger than max dimension
        max_dim: int = 1024
        if max(img.size) > max_dim:
            ratio: float = max_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        out = io.BytesIO()
        # Preserve alpha by using PNG, otherwise compress to JPEG

        img = img.convert("RGB")
        img.save(out, format="JPEG", quality=80, optimize=True, progressive=True)

        img_data: bytes = out.getvalue()
        out.close()
    except Exception:
        # On failure, fall back to original bytes
        img_data = orig_bytes
    return img_data


def response_to_json(text: Any) -> Dict[str, Any]:
    if not isinstance(text, str):
        text = str(text)
    start_marker: str = "```"
    end_marker: str = "```"
    out = {}

    start: int = text.find(start_marker)
    if start == -1:
        start = 0
        end = len(text)
    else:
        start += len(start_marker)
        end: int = text.find(end_marker, start)
        if end == -1:
            end = len(text)
    
    for line in text[start:end].splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        value = value.strip()
        
        if key.strip().lower() not in ["reason", "decision", "like_message"]:
            continue
        out[key.strip().lower()] = value
    return out