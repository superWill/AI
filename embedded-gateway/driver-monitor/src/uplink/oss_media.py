#!/usr/bin/env python3
"""媒体上传器 —— 把关键帧字节送上对象存储,回 object URL。

境内部署默认 **AliyunOSSUploader**;**CloudflareR2Uploader** 作为境外/备选并列实现。
二者共用 `MediaUploader` 接口,故 KeyframeThrottle / envelope 回填 / 存储转发全不感知换了谁。

设计约束(与本项目 uplink/* 一脉相承):
- **纯标准库签名**(OSS=hmac-sha1 V1;R2=AWS SigV4),不依赖 oss2/boto3 —— BL412 板端无外网无 pip。
- **离线容忍**:网络不可达/超时返回 None,由上层存储转发重试(同 UplinkTransport.publish 语义)。
- **不静默吞错**:4xx(签名/凭证/桶配置错)抛 MediaUploadError,绝不当「离线」无限重试。
- **确定性 key**:key 由 event_id + 帧名算出,故上传前就能预算最终 URL 填进 envelope。
- **凭证只从环境读**,绝不硬编码/入库;Secret 绝不进日志或异常文本。

环境变量:
  AliyunOSSUploader.from_env:
    OSS_ENDPOINT  如 oss-cn-hangzhou.aliyuncs.com / OSS_BUCKET / OSS_ACCESS_KEY_ID /
    OSS_ACCESS_KEY_SECRET / OSS_KEY_PREFIX(可选,默认 driver-monitor)
  CloudflareR2Uploader.from_env:
    R2_ACCOUNT_ID / R2_BUCKET / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY /
    R2_KEY_PREFIX(可选) / R2_PUBLIC_BASE_URL(可选:自定义域或 r2.dev,决定 object_url 能否公开访问)
"""
from __future__ import annotations

import abc
import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from email.utils import formatdate


def event_media_key(prefix: str, event_id: str, name: str, ext: str = "png") -> str:
    """确定性 object key:{prefix}/events/{event_id}/{name}.{ext}。"""
    prefix = prefix.strip("/")
    return f"{prefix}/events/{event_id}/{name}.{ext}"


def oss_object_url(endpoint: str, bucket: str, key: str, secure: bool = True) -> str:
    """由 endpoint+bucket 算对象最终 URL(非秘密;板子无凭证也能预算,用于回填 thumbnail_ref)。"""
    scheme = "https" if secure else "http"
    return f"{scheme}://{bucket}.{endpoint}/{key}"


class MediaUploadError(Exception):
    """非暂时性上传失败(HTTP 4xx)。带状态码,**不含**密钥。"""

    def __init__(self, status: int, key: str):
        super().__init__(f"PutObject 失败 status={status} key={key}")
        self.status = status
        self.key = key


OSSUploadError = MediaUploadError            # 向后兼容别名


class MediaUploader(abc.ABC):
    @abc.abstractmethod
    def object_url(self, key: str) -> str:
        """给定 key 预算最终可访问 URL(上传前即可得,用于回填 thumbnail_ref)。"""

    @abc.abstractmethod
    def put(self, key: str, data: bytes, content_type: str = "image/png") -> str | None:
        """上传一个对象。成功返回 URL;离线/暂时性失败返回 None(上层重试)。"""


def _put_object(host: str, path: str, data: bytes, headers: dict,
                secure: bool, timeout_s: float, key: str, url: str) -> str | None:
    """共用 HTTP PutObject:2xx→url,4xx→抛(不静默重试),5xx/断网→None(存储转发)。"""
    import http.client
    try:
        conn = (http.client.HTTPSConnection if secure
                else http.client.HTTPConnection)(host, timeout=timeout_s)
        try:
            conn.request("PUT", path, body=data, headers=headers)
            resp = conn.getresponse()
            resp.read()
            if 200 <= resp.status < 300:
                return url
            if 400 <= resp.status < 500:
                raise MediaUploadError(resp.status, key)       # 配置/凭证错:不静默重试
            return None                                        # 5xx:暂时,留给上层重试
        finally:
            conn.close()
    except OSError:
        return None                                            # 断网/超时/DNS:离线


@dataclass
class OSSCredentials:
    endpoint: str
    bucket: str
    access_key_id: str
    access_key_secret: str
    key_prefix: str = "driver-monitor"
    secure: bool = True
    timeout_s: float = 10.0


def _string_to_sign(verb: str, content_md5: str, content_type: str,
                    date: str, canonical_resource: str) -> str:
    # OSS V1:无 x-oss-* 头时 CanonicalizedOSSHeaders 为空字符串
    return f"{verb}\n{content_md5}\n{content_type}\n{date}\n{canonical_resource}"


def _sign(secret: str, string_to_sign: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(mac.digest()).decode("ascii")


class AliyunOSSUploader(MediaUploader):
    def __init__(self, creds: OSSCredentials):
        self.c = creds

    @classmethod
    def from_env(cls, environ: dict | None = None) -> "AliyunOSSUploader":
        e = environ if environ is not None else os.environ
        missing = [k for k in ("OSS_ENDPOINT", "OSS_BUCKET",
                               "OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET")
                   if not e.get(k)]
        if missing:
            raise RuntimeError(f"缺少 OSS 环境变量: {', '.join(missing)}")
        return cls(OSSCredentials(
            endpoint=e["OSS_ENDPOINT"].strip(),
            bucket=e["OSS_BUCKET"].strip(),
            access_key_id=e["OSS_ACCESS_KEY_ID"].strip(),
            access_key_secret=e["OSS_ACCESS_KEY_SECRET"].strip(),
            key_prefix=e.get("OSS_KEY_PREFIX", "driver-monitor").strip(),
        ))

    def _host(self) -> str:
        return f"{self.c.bucket}.{self.c.endpoint}"

    def object_url(self, key: str) -> str:
        scheme = "https" if self.c.secure else "http"
        return f"{scheme}://{self._host()}/{key}"

    def presign_get(self, key: str, expires_s: int = 3600, now: float | None = None) -> str:
        """私有桶对象的临时可访问 URL(OSS V1 签名):给人看/前端展示,免登控制台。
        无需鉴权头即可 GET,Expires 后失效。now 可注入供确定性单测。"""
        import time
        import urllib.parse
        expires = int((time.time() if now is None else now) + expires_s)
        sts = _string_to_sign("GET", "", "", str(expires), f"/{self.c.bucket}/{key}")
        sig = _sign(self.c.access_key_secret, sts)
        q = urllib.parse.urlencode({
            "OSSAccessKeyId": self.c.access_key_id,
            "Expires": expires,
            "Signature": sig,
        })
        return f"{self.object_url(key)}?{q}"

    def _build_headers(self, key: str, data: bytes, content_type: str,
                       date: str) -> dict:
        """构造 PutObject 请求头(含签名)。抽出来供签名单测,不发网络。"""
        content_md5 = base64.b64encode(hashlib.md5(data).digest()).decode("ascii")
        resource = f"/{self.c.bucket}/{key}"
        sts = _string_to_sign("PUT", content_md5, content_type, date, resource)
        sig = _sign(self.c.access_key_secret, sts)
        return {
            "Host": self._host(),
            "Date": date,
            "Content-Type": content_type,
            "Content-MD5": content_md5,
            "Content-Length": str(len(data)),
            "Authorization": f"OSS {self.c.access_key_id}:{sig}",
        }

    def put(self, key: str, data: bytes, content_type: str = "image/png") -> str | None:
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        headers = self._build_headers(key, data, content_type, date)
        return _put_object(self._host(), f"/{key}", data, headers,
                           self.c.secure, self.c.timeout_s, key, self.object_url(key))


# ---- Cloudflare R2(S3 兼容,AWS SigV4)---- 境外/备选;境内默认走上面的 OSS ----


@dataclass
class R2Credentials:
    account_id: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    key_prefix: str = "driver-monitor"
    public_base_url: str | None = None   # 自定义域 / r2.dev;None 则 object_url 回 S3 端点(需鉴权 GET)
    region: str = "auto"                  # R2 固定 auto
    timeout_s: float = 10.0


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sigv4_signing_key(secret: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _hmac_sha256(("AWS4" + secret).encode("utf-8"), date_stamp)
    k_region = _hmac_sha256(k_date, region)
    k_service = _hmac_sha256(k_region, service)
    return _hmac_sha256(k_service, "aws4_request")


class CloudflareR2Uploader(MediaUploader):
    """R2 PutObject(path-style + AWS SigV4)。凭证/接口与 AliyunOSSUploader 并列。

    注意:S3 端点 URL 需鉴权才能 GET;要公开访问须配 public_base_url(自定义域或 r2.dev)。
    我们的 key 仅含 [A-Za-z0-9-_./],SigV4 canonical URI 无需额外百分号编码。
    """

    def __init__(self, creds: R2Credentials):
        self.c = creds

    @classmethod
    def from_env(cls, environ: dict | None = None) -> "CloudflareR2Uploader":
        e = environ if environ is not None else os.environ
        missing = [k for k in ("R2_ACCOUNT_ID", "R2_BUCKET",
                               "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
                   if not e.get(k)]
        if missing:
            raise RuntimeError(f"缺少 R2 环境变量: {', '.join(missing)}")
        pub = e.get("R2_PUBLIC_BASE_URL")
        return cls(R2Credentials(
            account_id=e["R2_ACCOUNT_ID"].strip(),
            bucket=e["R2_BUCKET"].strip(),
            access_key_id=e["R2_ACCESS_KEY_ID"].strip(),
            secret_access_key=e["R2_SECRET_ACCESS_KEY"].strip(),
            key_prefix=e.get("R2_KEY_PREFIX", "driver-monitor").strip(),
            public_base_url=pub.strip() if pub else None,
        ))

    def _host(self) -> str:
        return f"{self.c.account_id}.r2.cloudflarestorage.com"

    def object_url(self, key: str) -> str:
        if self.c.public_base_url:
            return f"{self.c.public_base_url.rstrip('/')}/{key}"
        return f"https://{self._host()}/{self.c.bucket}/{key}"

    def _build_headers(self, key: str, data: bytes, content_type: str,
                       amz_date: str) -> dict:
        """构造 SigV4 PutObject 头(含签名)。抽出供单测,不发网络。amz_date=YYYYMMDDTHHMMSSZ。"""
        host = self._host()
        date_stamp = amz_date[:8]
        payload_hash = _sha256_hex(data)
        canonical_uri = f"/{self.c.bucket}/{key}"
        canonical_headers = (f"host:{host}\n"
                             f"x-amz-content-sha256:{payload_hash}\n"
                             f"x-amz-date:{amz_date}\n")
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = "\n".join([
            "PUT", canonical_uri, "", canonical_headers, signed_headers, payload_hash])
        scope = f"{date_stamp}/{self.c.region}/s3/aws4_request"
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256", amz_date, scope,
            _sha256_hex(canonical_request.encode("utf-8"))])
        signing_key = _sigv4_signing_key(
            self.c.secret_access_key, date_stamp, self.c.region, "s3")
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        auth = (f"AWS4-HMAC-SHA256 Credential={self.c.access_key_id}/{scope}, "
                f"SignedHeaders={signed_headers}, Signature={signature}")
        return {
            "Host": host,
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
            "Authorization": auth,
        }

    def put(self, key: str, data: bytes, content_type: str = "image/png") -> str | None:
        import time
        amz_date = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        headers = self._build_headers(key, data, content_type, amz_date)
        return _put_object(self._host(), f"/{self.c.bucket}/{key}", data, headers,
                           True, self.c.timeout_s, key, self.object_url(key))


class FakeMediaUploader(MediaUploader):
    """离线桩:写内存(可选本地目录),回可预测 URL。用于单测 / 无凭证联调。

    online=False 模拟断网(put 返回 None),用于验证上层存储转发。
    """

    def __init__(self, base_url: str = "https://fake-bucket.oss-cn-test.aliyuncs.com",
                 online: bool = True, save_dir: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.online = online
        self.save_dir = save_dir
        self.puts: list[tuple[str, int, str]] = []   # (key, size, content_type)
        self._objects: dict[str, bytes] = {}

    def object_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"

    def put(self, key: str, data: bytes, content_type: str = "image/png") -> str | None:
        if not self.online:
            return None
        self._objects[key] = data
        self.puts.append((key, len(data), content_type))
        if self.save_dir:
            path = os.path.join(self.save_dir, key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
        return self.object_url(key)

    def set_online(self, online: bool) -> None:
        self.online = online

    def get(self, key: str) -> bytes | None:
        return self._objects.get(key)
