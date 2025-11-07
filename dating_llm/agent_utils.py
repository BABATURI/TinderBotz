import io
import json
import requests

from PIL import Image

def get_image_data(url):
	resp = requests.get(url, timeout=10)
	resp.raise_for_status()
	orig_bytes = resp.content

	try:
		img = Image.open(io.BytesIO(orig_bytes))
		# Resize if larger than max dimension
		max_dim = 1024
		if max(img.size) > max_dim:
			ratio = max_dim / max(img.size)
			new_size = (int(img.width * ratio), int(img.height * ratio))
			img = img.resize(new_size, Image.Resampling.LANCZOS)

		out = io.BytesIO()
		# Preserve alpha by using PNG, otherwise compress to JPEG

		img = img.convert("RGB")
		img.save(out, format="JPEG", quality=70, optimize=True, progressive=True)

		img_data = out.getvalue()
		out.close()
	except Exception:
		# On failure, fall back to original bytes
		img_data = orig_bytes
	return img_data


def response_to_json(text):
	if not isinstance(text, str):
		text = str(text)
	start_marker = "```json"
	end_marker = "```"
	start = text.find(start_marker)
	if start == -1:
		raise ValueError("No '```json' block found in response")
	start += len(start_marker)
	end = text.find(end_marker, start)
	if end == -1:
		raise ValueError("No closing '```' found for JSON block")
	json_str = text[start:end].strip()
	try:
		return json.loads(json_str)
	except json.JSONDecodeError as e:
		try:
			return json.loads(json_str.replace("'", '"'))
		except Exception:
			raise ValueError("Failed to parse JSON from code block") from e