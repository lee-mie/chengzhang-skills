---
name: chengzhang
description: 使用成章（Chengzhang）服务检查账号、预览 Markdown 排版、按指定顺序上传贴图及标题文案到微信公众号草稿。适用于用户通过此服务发布文章或贴图，或询问公众号 AppID、AppSecret 获取、连接配置及 IP 白名单；不负责群发或部署服务器。
---

# 成章 Chengzhang

公众号文章排版、贴图发布与草稿上传。用户可直接说“用 chengzhang skill 发布这篇文章”或“用成章保存这组贴图到公众号草稿”。

把用户提供的文章上传到公众号草稿箱，并返回可核实的结果。网页和 Agent 使用同一个账号的公众号配置、模板与额度。发布只创建草稿，不向粉丝群发。

## 接入

正式站地址已内置为 `https://chengzhang.page`；普通用户只需配置自己的 Token，不需要填写域名或环境变量。Token 的实际值仍以 `wp_` 开头，不要修改它。

脚本优先使用 `CHENGZHANGPAGE_TOKEN`（兼容 `WX_TOKEN`），否则自动读取本机配置文件。地址可通过 `CHENGZHANGPAGE_BASE_URL`（兼容 `WX_BASE_URL`）或配置文件覆盖，供自托管使用。不读取通用 `TOKEN`／`BASE` 变量，避免误用其他工具凭据。

### 安装后与首次使用时的引导

- 先运行 `check` 复用已有配置；不要读取密钥文件全文到工具输出，不打印 Token。缺少配置时继续帮助用户，不把“自行配置环境变量”当作最终交付。
- 用普通语言说明：“技能已安装。成章网址已设置好，接下来只需在网页创建一次连接口令，并保存在这台电脑上；我会帮你创建文件和检查。”
- 给出可点击的 [Token 页面](https://chengzhang.page/tokens)：登录后，在“创建新 token”区域的“名称”输入 `WorkBuddy` 或当前 Agent 名称，点击“创建”，再点击新口令右侧的复制按钮。也可从 [编辑页](https://chengzhang.page/edit) 顶部右侧的 **API Token** 进入。完整口令只显示一次，丢失可重新创建；不要让用户粘贴到聊天中。
- 检测实际系统和 Python 命令，读取 [接入指南](SKILL_README.md) 的 Mac／Windows 步骤。Agent 执行 `setup` 创建空配置，告诉用户创建结果和实际绝对路径；按可用工具打开本机文本编辑器，让用户只把 Token 粘贴在 `token` 的空双引号中并保存。没有打开编辑器的工具时，提供适用于该系统的完整命令，不给未替换的路径占位符。
- 每次只交代当前需要的少量步骤，解释按钮和文件位置。用户保存后执行 `check`；通过后明确告知已连接及剩余额度。不让普通用户执行 `source`，不要求重启应用来加载这个配置。
- `setup` 保留已有文件，不覆盖已有凭据；本机没有 `env.sh` 是正常现象。旧 `~/.config/wechat-publisher/credentials` 的格式未知，不自动执行或猜测解析，不删除它；新配置路径不同。如果用户要复用旧凭据，让用户在本机编辑器中自行复制 Token。

详细步骤、配置优先级及其他宿主设置见 [接入指南](SKILL_README.md)。配置文件是本机明文文件，不声称加密存储。Token 不写进文章、请求 JSON、代码、日志或版本库，不在回复中复述。公众号配置缺失时引导打开 [公众号配置](https://chengzhang.page/settings/wechat)，已有配置直接复用。

工具只需 Python 3 标准库，不需要安装后端依赖。以下命令相对于本 SKILL.md 所在目录；从其他目录运行时使用脚本绝对路径。

## 公众号获取与配置 FAQ

用户询问 AppID／AppSecret 是什么、在哪里获取、如何配置、IP 白名单或接口权限时，先读取 [公众号连接 FAQ](docs/FAQ.md)，按问题给出简明步骤。缺少公众号配置时也主动用该 FAQ 引导。获取入口为 [微信开发者平台](https://developers.weixin.qq.com/platform) → **我的业务与服务** → **选择公众号** → **基础信息**（AppID、AppSecret、APP IP白名单）；不要回答旧的微信公众平台“基本配置”路径。成章配置页按钮为 **保存并测试连接**。

## 首次检查

```bash
python3 examples/publish.py check
```

读取 `/api/auth/me` 确认账号和 `credit_balance`，读取 `/api/config` 确认公众号 AppID；这个检查不代表微信连接已经验证。

- 401：引导用户在网页重新创建 Token。
- 配置 404：引导用户在网页“公众号配置”填写 AppID、AppSecret 并完成连接检测，避免在聊天收集 AppSecret。已有配置直接复用。
- 需要验证微信连通性时，使用同一 Bearer Token 调用 `POST /api/config/test`；检查 `data.ok`，不能只看外层 `success`。失败时依据 `data.error_code` / `data.message` 处理；40164 应将返回的 `data.server_ip` 加入公众号白名单。如果 IP 缺失或为内网地址，请管理员核实实际出口 IP。
- 余额不足时可继续预览；发布需要额度，提示用户到网页兑换或联系管理员。

## 文章、预览、发布

1. 复用用户给出的标题、正文、摘要、封面和模板。缺省选项交给服务端；不要为了填齐可选字段打断用户。需要选模板时调用 `GET /api/templates`，使用真实模板 ID。官方模板可读取并复制为个人模板；个人模板可用 `PUT /api/templates/{id}` 更新。用户默认模板通过 `/api/templates/default` 读取或设置。模板字段以[模板配置说明](public/TEMPLATE.md)为准，不能自行编造字段。
2. 将文章写入 UTF-8 JSON，参考 [最小示例](examples/in.minimal.json)。正文必填，其余可选。封面必须放在顶层 `cover_image` 字段，例如 `"cover_image":{"data":"<base64>","filename":"cover.jpg"}` 或 `"cover_image":{"url":"https://..."}`。不要使用 `cover`：服务端不读取该字段，会使用默认封面；脚本会拒绝这个错误字段。生成了封面时，prepare 前核对 `cover_image` 中确实包含该图片。`format_content: true` 为排版模式。作者和评论可用 `author`、`need_open_comment`、`only_fans_can_comment` 单次覆盖。

正文中的本地图片写成 `![说明](asset://image1)`，并在输入 JSON 顶层添加 `"inline_images":{"image1":"/本地绝对路径/image1.png"}`。支持 JPG/PNG，每张不超过 1 MB，最多 20 张。预览时脚本用本地文件显示图片；发布时脚本把文件随请求发送，服务端不会按路径读取 Agent 机器的文件。图片文件在确认发布前须保持存在且内容不变。
3. 生成并保存本次请求，再预览：

```bash
python3 examples/publish.py prepare article.json --out request.json
python3 examples/publish.py preview request.json --out preview.html --request-out confirmed.json
```

`prepare` 自动生成幂等键和请求指纹，文件不含 Token。使用每篇文章独立的文件名，工具拒绝覆盖已有文件。预览不扣额度、不创建微信草稿。`confirmed.json` 固定这次预览的模板配置；即使模板之后被修改，发布仍沿用当时的配置。向用户展示生成的 HTML；如果用户只要求预览，到此结束。

4. 用户已要求上传草稿时，完成检查后直接执行；已有发布授权不需要重复确认。仅写作或预览请求不代表发布授权。

```bash
python3 examples/publish.py publish confirmed.json
```

5. 仅当 `data.status == "success"` 且有 `draft_media_id` 时，告知“已存入公众号草稿箱”，附标题、草稿 ID 和剩余额度。请用户到公众号后台预览。HTTP 200 或外层 `success: true` 不等于草稿创建成功。

## 重试与错误处理

请求文件生成后保持不变，包括封面和其他选项。同一次网络重试使用原文件、原 key；禁止每次发送都重新 prepare。内容修改后，先确认旧请求没有产生草稿，再为新的发布意图生成新文件。

| 结果 | Agent 行为 |
| --- | --- |
| `data.status=success` | 完成，不再提交 |
| `data.status=failed` | 展示 `error_message`、`error_code`，检查 `credit_state`；修复明确原因后才发起新尝试。同 key 只返回原结果，不会重新执行 |
| `data.status=unknown` | 草稿可能已创建，先核对公众号草稿箱，停止自动发布；不要换 key 重发 |
| 超时、断连、502/504 | 结果不确定；保留原文件，可用原请求查询式重放一次；仍不确定则停止并核对后台 |
| 402 | 额度不足，提示兑换 |
| 409 | key 冲突，检查是否改了请求或用了其他账号；不要自动换 key 绕过 |
| 400/422 | 检查服务返回的字段错误，修正输入 |
| 40164 / 40001 | 检查后端出口 IP 白名单 / 公众号凭证，通过网页修复 |

脚本不自动重试；退出码 `0` 表示当前操作成功，`1` 表示失败，`3` 表示结果不确定。它们是此脚本的退出码，与后端 CLI 退出码无关。服务错误可能在 `error`、`detail` 或 `data.error_message` 中；保留具体错误供排查，不输出凭证。

## 接口参考

- [REST API](public/API.md)：接口与 HTTP 示例。
- [用户接入指南](ONBOARDING.md)：给用户的最短配置路径。

当前请求指纹实现跟随网页客户端：按正文、标题、摘要、模板、预览 ID、作者、两个评论字段的顺序，以 NUL 分隔（末尾无 NUL），空值按空字符串，计算 UTF-8 SHA256。后端目前比较客户端提交的指纹而不重新计算；因此不要在发送阶段自行改动已准备的请求。使用附带脚本，避免手写摘要与重试逻辑。


## 贴图草稿（独立于 Markdown）

用户要求发布一组贴图时，使用 `examples/publish_pictures.py`，不要转换成 Markdown 文章。
复用 `examples/publish.py setup/check` 的本机连接配置。贴图需所连接服务支持 `POST /api/publish/pictures`；正式站独立入口为 [贴图页面](https://chengzhang.page/pictures)。接口不支持或返回404/405时停止并说明原因，不改用文章接口代替，也不反复提交。

1. 建立 UTF-8 JSON：`{"title":"标题","content":"纯文本文案，可换行","images":["/absolute/01.png","/absolute/02.png"]}`。
   `images` 数组就是最终顺序，第一张为封面；1–20 张 JPG/PNG，每张 ≤1 MB。标题必填，≤64 字；文案可空，≤1000 字。
   按用户指定顺序填写；不能依赖目录遍历、字符串排序或并发上传完成顺序。顺序不明时先明确。
2. 运行 `python3 examples/publish_pictures.py prepare input.json --out pictures-request.json`。
   展示编号图片清单、首图、标题和完整文案供用户核对；有明确发布授权且内容与顺序已确定时可继续。
3. 运行 `python3 examples/publish_pictures.py publish pictures-request.json`。
   不修改生成的请求；图片、顺序、标题或文案变化需重新 prepare 并确认。每次成功保存消耗 1 点。
4. 成功仅表示保存公众号草稿，没有群发。失败按返回原因处理；unknown、退出码3或网络中断先查公众号草稿箱，不自动换 key 重发。保留原请求用于查询同次结果。

接口说明见 [公开 API](public/API.md)。

### 从创作到贴图草稿

用户要求生成图片并发布时，先用当前宿主可用的生图工具完成图片，再编写标题和纯文本文案。检查图片里的文字与编号，保存到稳定的本地目录。生成图超过1MB时保留原稿，另存适合上传的JPG/PNG副本，并核验尺寸、清晰度和文件大小；不得静默丢图或改变顺序。按上述prepare/publish流程提交。用户明确授权这次创作与保存草稿后可直接执行，无需重复询问。返回草稿ID、标题、图片数量及实际结果；如果有只读草稿查询能力，再核验图片列表顺序与文案。网页也可拖入多张图片，按编号调序后保存。
