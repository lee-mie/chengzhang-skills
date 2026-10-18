# 成章技能接口参考

默认服务地址为 `https://chengzhang.page`。请求通过 `Authorization: Bearer <用户自己的Token>` 验证身份；优先使用附带脚本，不把口令放入文章或请求文件。

## 连接检查

- `GET /api/auth/me`：返回当前账号及 `credit_balance`。
- `GET /api/config`：读取当前账号的公众号配置；AppSecret 不返回明文。404 表示尚未配置。
- `POST /api/config/test`：检测微信连接，检查 `data.ok`；失败时根据 `data.error_code`、`data.message` 和 `data.server_ip` 引导用户。

公众号凭证由用户在网页填写，获取与设置步骤见 [FAQ](../docs/FAQ.md)。

## 预览与保存草稿

`POST /api/publish/preview` 接收 `article_content`、可选 `title`、`digest`、`template_id`、`format_content`。返回 `data.html`、`data.preview_id` 及选用的模板 ID。预览不创建微信草稿。

`POST /api/publish` 接收相同文章字段，以及脚本生成的 `idempotency_key`、`request_hash`、预览返回的 `preview_id`。封面字段为 `cover_image`，格式为 `{"data":"<base64>","filename":"cover.jpg"}` 或 `{"url":"https://..."}`。作者与评论可用 `author`、`need_open_comment`、`only_fans_can_comment` 单次覆盖；未指定时复用账号默认值。

本地正文图使用 `![说明](asset://image1)`，输入文件的 `inline_images` 将标记映射到本地绝对路径。每张 JPG／PNG 不超过 1MB，最多 20 张；脚本会自动构造 `POST /api/publish/with-images` multipart 请求。超限时先生成压缩副本，保留原图。

推荐调用：

```bash
python3 examples/publish.py prepare article.json --out request.json
python3 examples/publish.py preview request.json --out preview.html --request-out confirmed.json
python3 examples/publish.py publish confirmed.json
```

只有用户要求上传时才执行最后一步。仅 `data.status="success"` 且有 `draft_media_id` 才表示草稿已保存。`credit_balance_after` 为剩余点数。

- `failed`：明确失败，检查错误信息与点数状态，修复后再处理。
- `unknown` 或网络超时：草稿可能已创建，保留请求，先核对公众号后台；不要换 key 重发。
- HTTP 401：Token 无效；402：点数不足；409：请求冲突；400／422：输入错误。

同次重试保持请求文件和图片内容不变。修改文章后重新准备和预览；先确认旧请求没有产生草稿。详细操作见 [技能说明](../SKILL.md)。

## 模板

- `GET /api/templates`：列出当前账号可用模板；使用返回的真实 ID。
- `GET /api/templates/{id}`：读取配置。
- `GET /api/templates/default`：读取默认模板。
- `PUT /api/templates/default`：请求 `{"template_id":"<真实ID>"}`，设置默认模板。
- `POST /api/templates`：请求 `{"name":"名称","config":{...}}`，创建个人模板。
- `PUT /api/templates/{id}`：同样的字段，修改自己的模板。
- `DELETE /api/templates/{id}`：删除自己的模板；仅在用户要求时调用。

官方模板只读，可复制为个人模板。配置用法见 [模板说明](TEMPLATE.md)。


## 贴图草稿

`POST /api/publish/pictures`，Bearer Token 鉴权，multipart/form-data。
`payload` 是 JSON 字符串：`{"title":"标题","content":"文案","idempotency_key":"32位小写十六进制唯一键"}`；重复 `images` 文件字段，字段出现顺序即展示顺序，首张为封面。
标题必填、最多64字；文案为纯文本、可空、最多1000字；图片1–20张、JPG/PNG、单张≤1MB。无需模板、Markdown或文章预览ID。
服务端对标题、文案及有序图片原始内容计算指纹；同键同内容返回同次结果，同键内容不同返回409。成功消耗1点；失败退点。
响应沿用草稿发布结果的 `status`、`draft_media_id`、`credit_state`、`credit_balance_after`、`error_message`。`unknown` 时先检查公众号后台，禁止自动重新创建。
推荐用 `examples/publish_pictures.py` 保存含指纹的请求；先 prepare 展示顺序、标题和文案，再 publish。
