#!/usr/bin/env python3
"""OSS 媒体上传器单测(纯标准库,不发网络)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.oss_media import (                                    # noqa: E402
    event_media_key, AliyunOSSUploader, OSSCredentials,
    CloudflareR2Uploader, R2Credentials,
    FakeMediaUploader, _string_to_sign, _sign,
)


# ---- key / url ----

def test_event_media_key_format():
    assert event_media_key("driver-monitor", "po-000123", "first_frame") == \
        "driver-monitor/events/po-000123/first_frame.png"


def test_event_media_key_strips_prefix_slashes():
    assert event_media_key("/dm/", "e1", "frame-001", ext="jpg") == \
        "dm/events/e1/frame-001.jpg"


# ---- Fake 上传器:在线/离线/幂等 ----

def _fake():
    return FakeMediaUploader(base_url="https://b.oss-cn-test.aliyuncs.com")


def test_fake_put_online_returns_url_and_records():
    up = _fake()
    key = event_media_key("dm", "po-1", "first_frame")
    url = up.put(key, b"\x89PNG-bytes", content_type="image/png")
    assert url == "https://b.oss-cn-test.aliyuncs.com/dm/events/po-1/first_frame.png"
    assert up.object_url(key) == url                 # 预算 URL == 实际返回
    assert up.get(key) == b"\x89PNG-bytes"
    assert up.puts == [(key, len(b"\x89PNG-bytes"), "image/png")]


def test_fake_put_offline_returns_none():
    up = _fake()
    up.set_online(False)
    assert up.put("dm/events/po-1/first_frame.png", b"x") is None
    assert up.puts == []                             # 未记录,交上层存储转发


# ---- 真上传器:from_env / 签名(不发网络) ----

def test_from_env_missing_raises():
    try:
        AliyunOSSUploader.from_env(environ={})
        assert False, "should raise"
    except RuntimeError as e:
        assert "OSS_ENDPOINT" in str(e)


def test_from_env_builds_and_object_url():
    up = AliyunOSSUploader.from_env(environ={
        "OSS_ENDPOINT": "oss-cn-hangzhou.aliyuncs.com",
        "OSS_BUCKET": "mybucket",
        "OSS_ACCESS_KEY_ID": "ak",
        "OSS_ACCESS_KEY_SECRET": "sk",
    })
    assert up.object_url("dm/events/po-1/first_frame.png") == \
        "https://mybucket.oss-cn-hangzhou.aliyuncs.com/dm/events/po-1/first_frame.png"


def test_string_to_sign_canonicalization():
    """OSS V1 StringToSign 组装必须逐字符正确(签名对错全在这)。"""
    date = "Wed, 08 Jul 2026 00:00:00 GMT"
    md5_hello = "XUFAKrxLKna5cZ2REBfFkg=="            # base64(md5(b"hello"))
    sts = _string_to_sign("PUT", md5_hello, "image/png", date, "/b/k")
    assert sts == f"PUT\n{md5_hello}\nimage/png\n{date}\n/b/k"


def test_build_headers_shape_and_signature_stability():
    up = AliyunOSSUploader(OSSCredentials(
        endpoint="oss-cn-hangzhou.aliyuncs.com", bucket="b",
        access_key_id="ak", access_key_secret="sk"))
    date = "Wed, 08 Jul 2026 00:00:00 GMT"
    h = up._build_headers("dm/events/po-1/first_frame.png", b"hello", "image/png", date)
    assert h["Host"] == "b.oss-cn-hangzhou.aliyuncs.com"
    assert h["Content-MD5"] == "XUFAKrxLKna5cZ2REBfFkg=="
    assert h["Content-Length"] == "5"
    assert h["Authorization"].startswith("OSS ak:")
    # 签名 = base64(hmac-sha1) 恒为 28 字符;同输入稳定可复算
    sig = h["Authorization"].split(":", 1)[1]
    assert len(sig) == 28
    resource = "/b/dm/events/po-1/first_frame.png"
    expect = _sign("sk", _string_to_sign("PUT", "XUFAKrxLKna5cZ2REBfFkg==",
                                         "image/png", date, resource))
    assert sig == expect


# ---- Cloudflare R2:from_env / object_url / SigV4 签名(不发网络) ----

def test_r2_from_env_missing_raises():
    try:
        CloudflareR2Uploader.from_env(environ={})
        assert False, "should raise"
    except RuntimeError as e:
        assert "R2_ACCOUNT_ID" in str(e)


def test_r2_object_url_endpoint_vs_public():
    key = "driver-monitor/events/po-1/first_frame.png"
    # 无 public_base_url → S3 端点 URL(需鉴权 GET)
    up = CloudflareR2Uploader(R2Credentials(
        account_id="acct123", bucket="evidence",
        access_key_id="AKID", secret_access_key="SECRET"))
    assert up.object_url(key) == \
        "https://acct123.r2.cloudflarestorage.com/evidence/" + key
    # 配了自定义域 → 公开可访问 URL
    up2 = CloudflareR2Uploader(R2Credentials(
        account_id="acct123", bucket="evidence",
        access_key_id="AKID", secret_access_key="SECRET",
        public_base_url="https://cdn.example.com/"))
    assert up2.object_url(key) == "https://cdn.example.com/" + key


def test_r2_sigv4_pinned_vector():
    """SigV4 canonical→签名回归钉子:任何 canonicalization 改动都会打破此断言。"""
    up = CloudflareR2Uploader(R2Credentials(
        account_id="acct123", bucket="evidence",
        access_key_id="AKID", secret_access_key="SECRET"))
    h = up._build_headers(
        "driver-monitor/events/po-1/first_frame.png", b"hello",
        "image/png", "20260708T000000Z")
    assert h["Host"] == "acct123.r2.cloudflarestorage.com"
    # x-amz-content-sha256 = sha256(b"hello") 的已知标准值
    assert h["x-amz-content-sha256"] == \
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert h["Content-Length"] == "5"
    assert h["Authorization"].startswith(
        "AWS4-HMAC-SHA256 Credential=AKID/20260708/auto/s3/aws4_request, "
        "SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=")
    sig = h["Authorization"].split("Signature=", 1)[1]
    assert sig == "af271bc6f97bd3dd39d1563f4cbf4d7917ee5a4db9973b887a7ef679e95ea4b5"


# ---- 签名 URL(presign GET) ----

def test_presign_get_structure_and_signature():
    up = AliyunOSSUploader(OSSCredentials(
        endpoint="oss-cn-hangzhou.aliyuncs.com", bucket="b",
        access_key_id="ak", access_key_secret="sk"))
    key = "dm/events/po-1/first_frame.png"
    url = up.presign_get(key, expires_s=3600, now=1000000000.0)
    assert url.startswith("https://b.oss-cn-hangzhou.aliyuncs.com/" + key + "?")
    assert "OSSAccessKeyId=ak" in url and "Expires=1000003600" in url and "Signature=" in url
    # 签名 = base64(hmac-sha1(GET\n\n\n{expires}\n/b/key));独立复算比对
    import urllib.parse
    expect = _sign("sk", _string_to_sign("GET", "", "", "1000003600", "/b/" + key))
    got = urllib.parse.parse_qs(url.split("?", 1)[1])["Signature"][0]
    assert got == expect


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")
