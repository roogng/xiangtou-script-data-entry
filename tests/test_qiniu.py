# tests/test_qiniu.py
import io
from unittest.mock import patch, MagicMock
from PIL import Image
from qiniu_uploader import compress_if_needed, generate_key, upload_image_bytes


def _png_bytes(size=500, noise=False):
    if noise:
        # high-entropy random image so PNG is genuinely large (incompressible)
        import random
        rng = random.Random(0)
        img = Image.new("RGB", (size, size))
        img.putdata([(rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
                     for _ in range(size * size)])
    else:
        img = Image.new("RGB", (size, size), "red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_compress_under_limit_unchanged():
    data = _png_bytes(10)
    out, _ = compress_if_needed(data, max_size=1048576)
    assert len(out) <= 1048576


def test_compress_large_image_under_1mb():
    data = _png_bytes(700, noise=True)  # random noise -> large PNG, forces compression
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


def test_upload_url_sends_browser_user_agent():
    # image CDNs (Pixabay) block the default python-requests UA; upload_url must
    # send a browser UA so fallback images actually download.
    from unittest.mock import patch
    from qiniu_uploader import QiniuUploader
    with patch("qiniu_uploader.requests.get") as g, \
         patch("qiniu_uploader.upload_image_bytes", return_value="public/common/x.jpg"):
        resp = MagicMock(); resp.content = b"\xff\xd8\xffimg"
        resp.raise_for_status.return_value = None
        g.return_value = resp
        up = QiniuUploader("ak", "sk", "bucket", "domain", 1048576,
                           "public/common/{uuid}.jpg")
        fk, _sz = up.upload_url("http://x/a.jpg")
        assert fk == "public/common/x.jpg"
        _, kwargs = g.call_args
        assert "Mozilla" in kwargs["headers"]["User-Agent"]
