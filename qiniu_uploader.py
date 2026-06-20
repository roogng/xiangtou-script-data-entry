# qiniu_uploader.py
import io
import logging
import uuid
import requests
from PIL import Image
from qiniu import Auth, put_data

# Silence the qiniu SDK's region-cache warning. On Windows the SDK persists region
# info using strftime('%s.%f'), which fails (ValueError) and triggers a noisy logging
# error. Region info is still used in-memory, so caching is non-essential.
logging.getLogger("qiniu").setLevel(logging.ERROR)



def generate_key(template: str = "public/common/{uuid}.jpg") -> str:
    return template.format(uuid=uuid.uuid4().hex)


def compress_if_needed(data: bytes, max_size: int) -> tuple:
    """Return (bytes, ext). Compress to JPEG under max_size by lowering quality."""
    if len(data) <= max_size:
        return data, _sniff_ext(data)
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    quality = 90
    out = b""
    while quality >= 20:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        out = buf.getvalue()
        if len(out) <= max_size:
            return out, "jpg"
        quality -= 10
    return out, "jpg"  # best effort


def _sniff_ext(data: bytes) -> str:
    if data[:8].startswith(b"\x89PNG"):
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"GIF8":
        return "gif"
    return "jpg"


def upload_image_bytes(data: bytes, key: str, bucket: str, auth: Auth) -> str:
    token = auth.upload_token(bucket, key, 3600)
    ret, _ = put_data(token, key, data)
    return ret["key"]


class QiniuUploader:
    def __init__(self, access_key, secret_key, bucket, domain, max_size, template):
        self._auth = Auth(access_key, secret_key)
        self._bucket = bucket
        self._domain = domain
        self._max_size = max_size
        self._template = template

    @classmethod
    def from_config(cls, cfg):
        q = cfg["qiniu"]
        return cls(q["access_key"], q["secret_key"], q["bucket"], q["domain"],
                   int(q["max_size_bytes"]), q["image_path_template"])

    def upload_url(self, url: str):
        """Download a remote image, compress, upload. Returns (file_key, size) or ('', 0) on failure."""
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.content
        except Exception:
            return "", 0
        data, _ext = compress_if_needed(data, self._max_size)
        key = generate_key(self._template)
        try:
            fk = upload_image_bytes(data, key, self._bucket, self._auth)
            return fk, len(data)
        except Exception:
            return "", 0
