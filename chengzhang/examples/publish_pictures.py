#!/usr/bin/env python3
"""Ordered local picture drafts. Prepare a manifest, then submit exactly that manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

from publish import load_connection, NoRedirect, result_code


def read_images(payload):
    if not isinstance(payload.get("title"), str) or not payload["title"].strip() or len(payload["title"]) > 64:
        raise ValueError("title 必须为 1–64 字标题")
    if not isinstance(payload.get("content", ""), str) or len(payload.get("content", "")) > 1000:
        raise ValueError("content 为最多 1000 字的纯文本文案")
    images = payload.get("images")
    if not isinstance(images, list) or not 1 <= len(images) <= 20:
        raise ValueError("images 必须是按发布顺序排列的 1–20 个本地文件路径，禁止自动排序")
    result = []
    for value in images:
        path = Path(value).expanduser().resolve()
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("图片不能超过 1 MB")
        data = path.read_bytes()
        if not (data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff")):
            raise ValueError("仅支持 JPG / PNG，服务端还会校验图片完整性")
        result.append((path, data))
    return result


def fingerprint(payload, images):
    return hashlib.sha256(json.dumps(["newspic", payload["title"], payload.get("content", ""),
        [hashlib.sha256(data).hexdigest() for _, data in images]], ensure_ascii=False).encode()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description="贴图草稿：先 prepare 核对顺序、标题与文案，再 publish；不自动重试")
    parser.add_argument("action", choices=["prepare", "publish"])
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        allowed = {"title", "content", "images", "idempotency_key", "request_hash"}
        if set(payload) - allowed:
            raise ValueError("存在未知字段；贴图只接受 title、content、images")
        images = read_images(payload)
        digest = fingerprint(payload, images)
        if args.action == "prepare":
            if not args.out or "idempotency_key" in payload or "request_hash" in payload:
                raise ValueError("prepare 需要原始 JSON 和 --out 新文件路径")
            payload.update(images=[str(path) for path, _ in images], idempotency_key=uuid.uuid4().hex, request_hash=digest)
            with args.out.open("x", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        import re
        if not re.fullmatch(r"[0-9a-f]{32}", str(payload.get("idempotency_key", ""))) or payload.get("request_hash") != digest:
            raise ValueError("请先 prepare；标题、文案、顺序或图片变化后必须重新 prepare 并确认")
        base, token = load_connection()
        url = urllib.parse.urlsplit(base)
        if not url.hostname or url.path not in ("", "/") or url.query or url.fragment or url.username or url.password or (url.scheme != "https" and not (url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1", "::1"))):
            raise ValueError("请使用 HTTPS 服务根地址")
        if not token.startswith("wp_"):
            raise ValueError("请先运行 publish.py setup 并填写本机凭据，再 check")
        boundary = "wp" + uuid.uuid4().hex
        chunks = []
        def field(name, data, filename=None):
            header = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
            if filename:
                header += f'; filename="{filename}"'
            chunks.extend([(header + "\r\nContent-Type: application/octet-stream\r\n\r\n").encode(), data, b"\r\n"])
        field("payload", json.dumps({k: payload[k] for k in ("title", "content", "idempotency_key") if k in payload}, ensure_ascii=False).encode())
        for index, (_, data) in enumerate(images):
            field("images", data, f"picture-{index+1}.{'png' if data.startswith(bytes([137])) else 'jpg'}")
        chunks.append(f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(base + "/api/publish/pictures", data=b"".join(chunks), headers={"Authorization": "Bearer " + token, "Content-Type": "multipart/form-data; boundary=" + boundary})
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=120) as response:
                body = json.load(response)
        except urllib.error.HTTPError as error:
            # HTTP errors may contain server detail; never print credential-bearing request URLs.
            print(f"请求被拒绝（HTTP {error.code}），请检查配置、额度和请求内容。", file=sys.stderr)
            return 1
        except Exception:
            print("未确认结果；请先检查公众号草稿箱。保留原请求，不要自动换 key 重发。", file=sys.stderr)
            return 3
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return result_code(body, publish=True)
    except (ValueError, OSError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
