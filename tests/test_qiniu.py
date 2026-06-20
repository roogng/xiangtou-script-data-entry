# tests/test_qiniu.py
import io
from unittest.mock import patch, MagicMock
from PIL import Image
from qiniu_uploader import compress_if_needed, generate_key, upload_image_bytes


def _png_bytes(size=500):
    img = Image.new("RGB", (size, size), "red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_compress_under_limit_unchanged():
    data = _png_bytes(10)
    out, _ = compress_if_needed(data, max_size=1048576)
    assert len(out) <= 1048576


def test_compress_large_image_under_1mb():
    data = _png_bytes(2000)
    assert len(data) > 1048576
    out, _ = compress_if_needed(data, max_size=1048576)
    assert len(out) <= 1048576


def test_generate_key_format():
    key = generate_key()
    assert key.startswith("public/common/")
    assert key.endswith(".jpg")


def test_upload_returns_file_key():
    with patch("qiniu_uploader.put_data") as mock_put:
        mock_put.return_value = ({"key": "public/common/abc.jpg"}, None)
        key = upload_image_bytes(b"imgbytes", "public/common/abc.jpg",
                                 bucket="b", auth=MagicMock())
        assert key == "public/common/abc.jpg"
