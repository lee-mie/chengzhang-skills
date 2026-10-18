"""Agent client (Python standard library only); see ../SKILL.md."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


DEFAULT_BASE_URL = "https://chengzhang.page"


def credentials_path():
    if os.name == "nt":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "ChengzhangPage" / "credentials.json"
    return Path.home() / ".config" / "chengzhangpage" / "credentials.json"


def setup_credentials():
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(f"配置文件已存在，保留原内容：{path}")
        return
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump({"base_url": DEFAULT_BASE_URL, "token": ""}, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"已创建配置文件：{path}")
    print("请用文本编辑器打开它，把网页复制的 Token 粘贴到 token 后面的空双引号中，保存后让 Agent 执行 check。不要把 Token 发到聊天中。")


def load_connection():
    env_token = os.environ.get("CHENGZHANGPAGE_TOKEN") or os.environ.get("WX_TOKEN")
    env_base = os.environ.get("CHENGZHANGPAGE_BASE_URL") or os.environ.get("WX_BASE_URL")
    if env_token:
        return (env_base or DEFAULT_BASE_URL).rstrip("/"), env_token
    path = credentials_path()
    if not path.exists():
        raise ValueError(f"还没配置连接口令。请让 Agent 执行 setup 创建配置文件，再打开 {DEFAULT_BASE_URL}/tokens 创建 Token；不要把 Token 发到聊天中")
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        raise ValueError(f"无法读取配置文件 {path}。请保留 JSON 双引号及逗号，保存为 UTF-8；不要把文件内容发到聊天中") from None
    if not isinstance(config, dict) or not isinstance(config.get("token"), str) or not isinstance(config.get("base_url", DEFAULT_BASE_URL), str):
        raise ValueError(f"配置文件格式不正确：{path}；base_url 和 token 应为文本")
    base = config.get("base_url") or DEFAULT_BASE_URL
    if env_base and env_base.rstrip("/") != base.rstrip("/"):
        raise ValueError("环境变量中的服务地址与配置文件地址不一致；请统一地址后重试，避免把 Token 发往另一个服务")
    return base.rstrip("/"), config["token"].strip()


ASSET_RE = re.compile(r"asset://([A-Za-z0-9_-]+)")
MAX_INLINE_IMAGES = 20
MAX_INLINE_IMAGE_BYTES = 1024 * 1024


def validate_inline_images(payload):
    image_paths = payload.get("inline_images") or {}
    if not isinstance(image_paths, dict):
        raise ValueError("inline_images 必须是图片标记到本地绝对路径的对象")
    if len(image_paths) > MAX_INLINE_IMAGES:
        raise ValueError(f"正文图片最多 {MAX_INLINE_IMAGES} 张")

    referenced = set(ASSET_RE.findall(payload.get("article_content") or ""))
    if referenced != set(image_paths):
        raise ValueError("正文中的 asset:// 图片标记与 inline_images 文件映射不一致")

    checked = {}
    for asset_id, raw_path in image_paths.items():
        if not isinstance(asset_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", asset_id):
            raise ValueError(f"图片标记 {asset_id!r} 格式不正确")
        if not isinstance(raw_path, str):
            raise ValueError(f"图片 {asset_id} 的路径必须是字符串")
        image_path = Path(raw_path)
        if not image_path.is_absolute():
            raise ValueError(f"图片 {asset_id} 请使用本地绝对路径")
        try:
            image_data = image_path.read_bytes()
        except OSError as exc:
            raise ValueError(f"无法读取图片 {asset_id}：{image_path}") from exc
        if not image_data or len(image_data) > MAX_INLINE_IMAGE_BYTES:
            raise ValueError(f"正文图片 {image_path.name} 为空或超过 1 MB，请先压缩")
        if not (image_data.startswith(b"\x89PNG\r\n\x1a\n") or image_data.startswith(b"\xff\xd8\xff")):
            raise ValueError(f"正文图片 {image_path.name} 仅支持 JPG 或 PNG")
        checked[asset_id] = (image_path, image_data)
    return checked


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward credentials to a redirected destination.


def validate_cover_field(payload):
    if "cover" in payload:
        raise ValueError("封面字段应为 cover_image，不能使用 cover；服务端会忽略 cover 并使用默认封面。请修正原始文章后重新 prepare 和 preview；已有成功或不确定请求不要直接重发")
    cover = payload.get("cover_image")
    if cover is not None and (not isinstance(cover, dict) or not (cover.get("data") or cover.get("url"))):
        raise ValueError("cover_image 必须包含非空 data 或 url；不指定封面请省略该字段或使用 null")


def prepare(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("article_content"), str) or not payload["article_content"].strip():
        raise ValueError("输入必须包含非空 article_content")
    if "idempotency_key" in payload or "request_hash" in payload:
        raise ValueError("prepare 需要原始文章 JSON；已有请求请直接 preview / publish，不要重新生成 key")
    validate_cover_field(payload)
    validate_inline_images(payload)
    # Match the current web client. Server compares this opaque fingerprint.
    raw = request_fingerprint(payload)
    return {**payload, "idempotency_key": uuid.uuid4().hex,
            "request_hash": hashlib.sha256(raw.encode()).hexdigest()}


def request_fingerprint(payload):
    fields = ("article_content", "title", "digest", "template_id", "preview_id", "author", "need_open_comment", "only_fans_can_comment")
    parts = [str(payload[k]) if payload.get(k) is not None else "" for k in fields]
    for asset_id, (_path, image_data) in sorted(validate_inline_images(payload).items()):
        parts.append(f"{asset_id}:{hashlib.sha256(image_data).hexdigest()}")
    return "\x00".join(parts)


def result_code(body, publish=False):
    if not isinstance(body, dict) or body.get("success") is not True:
        return 1
    if publish:
        data = body.get("data") or {}
        if data.get("status") == "unknown":
            return 3
        return 0 if data.get("status") == "success" and data.get("draft_media_id") else 1
    return 0


def request(base, token, path, payload=None, image_paths=None):
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    if image_paths:
        checked_images = validate_inline_images({**(payload or {}), "inline_images": image_paths})
        boundary = "wp" + uuid.uuid4().hex
        chunks = []
        def field(name, value, filename=None):
            chunks.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"" +
                           (f"; filename=\"{filename}\"" if filename else "") +
                           "\r\nContent-Type: application/octet-stream\r\n\r\n").encode())
            chunks.append(value)
            chunks.append(b"\r\n")
        field("payload", data)
        ids = sorted(image_paths)
        field("image_ids", json.dumps(ids).encode())
        for asset_id in ids:
            image_path, image_data = checked_images[asset_id]
            field("images", image_data, image_path.name)
        chunks.append(f"--{boundary}--\r\n".encode())
        data = b"".join(chunks)
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
        path = "/api/publish/with-images"
    req = urllib.request.Request(base + path, data=data, headers=headers)
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=120) as response:
        return json.load(response)


def main(argv=None):
    parser = argparse.ArgumentParser(description="公众号草稿工具；不自动重试。默认连接成章；Token 从专用环境变量或本机配置读取。")
    parser.add_argument("action", choices=["setup", "check", "prepare", "preview", "publish"])
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--out", type=Path, help="prepare 的请求 JSON 或 preview 的 HTML；不覆盖已有文件")
    parser.add_argument("--request-out", type=Path, help="preview 后保存带 preview_id 的最终发布请求；不覆盖已有文件")
    args = parser.parse_args(argv)
    try:
        if args.action == "setup":
            setup_credentials()
            return 0
        payload = None
        if args.action != "check":
            if args.input is None:
                raise ValueError("请提供文章或请求 JSON 文件路径")
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            validate_cover_field(payload)
        if args.action == "prepare":
            if args.out is None:
                raise ValueError("prepare 必须指定 --out，保存幂等请求供后续重试")
            prepared = prepare(payload)
            with args.out.open("x", encoding="utf-8") as file:
                json.dump(prepared, file, ensure_ascii=False, indent=2)
            print(json.dumps({"request_file": str(args.out), "idempotency_key": prepared["idempotency_key"]}))
            return 0
        base, token = load_connection()
        url = urllib.parse.urlsplit(base)
        if url.scheme not in ("http", "https") or not url.hostname or url.path not in ("", "/") or url.query or url.fragment or url.username or url.password:
            raise ValueError("服务地址应为 HTTPS 根地址，例如 https://chengzhang.page（不带 /api）")
        if url.scheme != "https" and url.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("远程服务请使用 HTTPS；HTTP 仅用于本机开发")
        if not token.startswith("wp_"):
            raise ValueError("连接口令为空或格式不正确。请打开 https://chengzhang.page/tokens 创建 Token，将完整 wp_ 开头的值保存到本机配置文件 token 中，或设置 CHENGZHANGPAGE_TOKEN")
        if args.action == "check":
            for path in ("/api/auth/me", "/api/config"):
                body = request(base, token, path)
                print(json.dumps({"endpoint": path, "response": body}, ensure_ascii=False))
                if result_code(body):
                    return 1
            return 0
        if args.action == "publish":
            for field, length in (("idempotency_key", 32), ("request_hash", 64)):
                if not re.fullmatch(r"[0-9a-f]{%d}" % length, str(payload.get(field, ""))):
                    raise ValueError("请先 prepare，再提交生成的请求文件；缺少或无效字段：" + field)
            if not payload.get("preview_id"):
                raise ValueError("请先 preview --request-out 保存确认过的发布请求")
        if args.action == "publish" and hashlib.sha256(request_fingerprint(payload).encode()).hexdigest() != payload["request_hash"]:
            raise ValueError("文章或本地图片已变化，请重新 prepare 和 preview")
        image_paths = payload.get("inline_images") or {}
        server_payload = {key: value for key, value in payload.items() if key != "inline_images"}
        endpoint = "/api/publish/preview" if args.action == "preview" else "/api/publish"
        if args.action == "publish" and image_paths:
            body = request(base, token, endpoint, server_payload, image_paths)
        else:
            body = request(base, token, endpoint, server_payload)
        code = result_code(body, publish=args.action == "publish")
        if args.action == "preview" and args.out and code == 0:
            with args.out.open("x", encoding="utf-8") as file:
                html = body["data"]["html"]
                for asset_id, image_path in image_paths.items():
                    html = html.replace(f'src="asset://{asset_id}"', f'src="{Path(image_path).resolve().as_uri()}"')
                file.write(html)
        if args.action == "preview" and args.request_out and code == 0:
            confirmed = {**payload, "preview_id": body["data"]["preview_id"]}
            if "request_hash" in confirmed:
                confirmed["request_hash"] = hashlib.sha256(request_fingerprint(confirmed).encode()).hexdigest()
            with args.request_out.open("x", encoding="utf-8") as file:
                json.dump(confirmed, file, ensure_ascii=False, indent=2)
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return code
    except urllib.error.HTTPError as exc:
        print(json.dumps({"http_status": exc.code, "error": exc.read().decode("utf-8", errors="replace")}, ensure_ascii=False), file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        print("网络结果不确定。保留请求文件；发布请求不要换 key 重发，先核对公众号草稿箱。", file=sys.stderr)
        return 3
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
