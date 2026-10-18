# 成章公众号草稿技能：安装后的连接步骤

## 当前交付版本

**v0.1.6 · 2026-10-18**

- GitHub 安装入口：`npx skills add lee-mie/chengzhang-skills --skill chengzhang`；手动完整包见 [Releases](https://github.com/lee-mie/chengzhang-skills/releases)。
- 网页可自定义排版并保存默认模板，Agent 预览和上传时复用；个人模板权益以网站说明为准。
- 支持从生成图片、编写标题文案到保存贴图草稿的工作流；[正式站贴图页面](https://chengzhang.page/pictures) 已开放，支持多图拖入和编号调序。
- 新增贴图草稿：准确保留图片顺序、标题和纯文本文案；使用 `examples/publish_pictures.py` 准备并提交请求。
- 默认连接成章，支持 Mac／Windows 自动读取本机配置；首次使用由 Agent 创建空配置并协助连接。
- 自定义封面统一使用 `cover_image`，提交前拒绝错误字段及空封面对象。
- 支持本地正文配图、预览后固定模板、复用账号默认作者与评论设置，以及幂等发布和不确定结果处理。
- 包含公众号凭证获取、连接检测和 IP 白名单操作指南。

技能名称为 `chengzhang`，展示名称为“成章 Chengzhang”。

更新安装：旧版用户先将已安装的 `wechat-publisher/` 技能目录重命名为 `chengzhang/`，再用新包内文件更新；不要同时保留两个可加载的同功能技能目录。保留完整目录结构。本机连接配置位于技能目录之外，更新时保留已有口令。

技能已安装后，成章网址 `https://chengzhang.page` 已设置好。你只需创建一次自己的连接口令（网页上叫 API Token），保存在电脑上。后续 Agent 自动读取它，帮你排版和上传草稿。

上传草稿不会向粉丝群发。客户端仅需 Python 3，无需安装后端依赖。

## 1. 在网页创建口令

1. 打开 [创建口令页面](https://chengzhang.page/tokens)，登录你的成章账号。也可以从 [文章编辑页](https://chengzhang.page/edit) 顶部右侧点击 **API Token**。
2. 在“创建新 token”区域的“名称”输入 `WorkBuddy`（换用其他 Agent 时可填写它的名称）。
3. 点击旁边的“创建”。新口令会显示在下方提示框中，以 `wp_` 开头。
4. 点击口令右侧的复制按钮。完整口令只显示一次，先保留这个页面。

口令用来让 Agent 访问你的成章账号，不是公众号 AppSecret。不要改变 `wp_` 前缀，也不要将它发到聊天、截图或代码仓库。如果丢失，在此页面重新创建；如果泄露，在“已有 token”列表撤销它。

## 2. 让 Agent 创建并打开配置文件

可以直接对 WorkBuddy 说：

> 请帮我配置成章公众号草稿技能。网址使用默认值，请先检测我的系统并创建本机配置文件，帮我用文本编辑器打开。Token 由我自己在文件里粘贴，请不要读取或显示它；保存后帮我检查连接。

**给 Agent 的操作说明：**定位实际安装的 `examples/publish.py`，先检测 Python 3 可用命令，再运行 `setup`。Mac 常见安装目录为 `~/.workbuddy-ai/skills/chengzhang/`；不要假定 Windows 目录相同。`setup` 输出实际配置路径，文件已存在时保持原样。只有缺配置时才需要引导创建。

新文件内容如下。用户只需将刚复制的完整口令粘贴进 `token` 后面的空双引号，保留其余文字和标点，再保存：

```json
{
  "base_url": "https://chengzhang.page",
  "token": ""
}
```

这个文件会自动读取，用户不需要配置环境变量、执行 `source` 或重启 WorkBuddy。以后改用另一台电脑，需要在那台电脑上重新配置。

### Mac：可直接操作的步骤

优先让 Agent 执行创建和打开操作。如果你想手动操作：

1. 用 Spotlight 搜索“终端”并打开。
2. 如果技能安装在上述 WorkBuddy 默认位置，复制执行以下命令（Python 3 缺失时，让 Agent 帮你从 [Python 官网](https://www.python.org/downloads/) 安装后再检查）：

```bash
python3 "$HOME/.workbuddy-ai/skills/chengzhang/examples/publish.py" setup
open -a TextEdit "$HOME/.config/chengzhangpage/credentials.json"
```

3. 将口令粘贴进 `token` 的空双引号，按 `Command+S` 保存。若 TextEdit 提示格式，选择纯文本，保存为 UTF-8；文件名保持 `credentials.json`，不要追加 `.txt`。
4. 回到 WorkBuddy 说“我已保存，请检查连接”。Agent 执行：

```bash
python3 "$HOME/.workbuddy-ai/skills/chengzhang/examples/publish.py" check
```

用访达查找时：按 `Command+Shift+G`，输入 **文件夹** `~/.config/chengzhangpage/`，回车，再双击 `credentials.json`。必须先执行 `setup` 创建文件夹；“前往文件夹”不能打开不存在的路径，也不要把文件路径当文件夹输入。

### Windows：可直接操作的步骤

1. 让 Agent 查出 Python 3 命令（一般为 `py -3` 或 `python`）与技能脚本的**真实完整路径**。若没有 Python，从 [Python 官网](https://www.python.org/downloads/) 安装后让 Agent 再检查。
2. Agent 在 PowerShell 运行 `py -3 "实际完整路径\examples\publish.py" setup`。这行是给 Agent 的模板；Agent 必须替换为查到的路径后，才把可执行命令交给用户。如果系统只有 `python`，使用它。
3. 创建成功后，在 PowerShell 执行下面命令打开记事本（Agent 也可帮你执行）：

```powershell
notepad.exe "$env:APPDATA\ChengzhangPage\credentials.json"
```

4. 把口令粘贴进 `token` 的空双引号，按 `Ctrl+S`。若出现“另存为”，编码选 UTF-8、文件类型选“所有文件”，文件名保持 `credentials.json`。
5. 回到 WorkBuddy 说“我已保存，请检查连接”。Agent 用同一个 Python 命令和真实脚本路径执行 `check`。

用资源管理器查找时：在地址栏输入 `%APPDATA%\ChengzhangPage`，回车，再打开 `credentials.json`。必须先运行 `setup`。Windows 不要照抄 Mac 的 `~` 路径或 bash 命令。

## 3. 连接通过后开始使用

可以告诉 Agent：

> 请用成章公众号草稿技能写一篇文章，生成合适的正文配图、摘要和封面，预览排版后保存到我的公众号草稿箱。

只想看效果时说“先预览，不上传”。Agent 应复用网页设置的默认模板、作者及评论配置，不为缺省选项反复提问。

若尚未配置公众号，打开 [公众号配置页面](https://chengzhang.page/settings/wechat) 填写 AppID 和 AppSecret，按页面完成连接检测及 IP 白名单设置。不把 AppSecret 发给 Agent。`check` 验证成章账号和已保存的公众号配置；微信连通性另通过网页检测或 `POST /api/config/test` 验证。

## 已有配置与变量名

- 推荐变量为 `CHENGZHANGPAGE_TOKEN`；地址变量为 `CHENGZHANGPAGE_BASE_URL`，默认地址下不用设置它。
- 兼容旧的 `WX_TOKEN`、`WX_BASE_URL`。新名称优先；同名环境变量确实可能被其他工具复用，普通用户使用上面的专用文件即可。
- Token 从新变量、旧变量、专用配置文件依次取值。使用环境变量 Token 时，地址取新地址变量、旧地址变量、内置默认值。使用配置文件 Token 时，使用文件地址；与地址环境变量不一致会停止，避免把口令发往其他服务。
- 不读取通用 `TOKEN`、`BASE` 变量。更换私有服务时要配置匹配的服务地址及其 Token。
- `~/.config/wechat-publisher/env.sh` 是旧说明举例的手动文件，安装不会生成它；`~/.config/wechat-publisher/credentials` 也不是此新版脚本的配置文件。旧文件保持原样，不自动读取或执行；用户可在本机编辑器中把需要的口令复制到新文件。
- Mac 配置位于 `~/.config/chengzhangpage/credentials.json`，新建文件权限为 600。Windows 配置位于 `%APPDATA%\ChengzhangPage\credentials.json`，使用当前用户文件夹的权限。文件为明文，不宣称加密保存。
- 配置必须存在于运行脚本的那台机器上；云端、容器或远程 Agent 不能自动读取本机文件。让 Agent 先说明实际执行环境，再给对应的设置步骤，不为此关闭沙箱。

## 其他宿主与安装

完整 ZIP 包解压后保留 `chengzhang/` 根目录及 `examples/`、`docs/`，不要只复制 SKILL.md。更新时覆盖技能目录中的包内文件；专用配置在技能目录之外，不受更新影响。

Codex、OpenClaw 等本机 Agent 同样可使用上述自动读取配置方式。已有宿主环境变量配置继续兼容，无需迁移；不要求普通用户编辑宿主的 TOML、JSON5 或 shell 启动文件。无法确认 WorkBuddy 当前版本的专用凭据入口时，使用本技能的跨平台文件方案，不编造设置菜单。

## 给 Agent 的执行顺序

以下命令以 `python3` 为例；Windows 使用实际探测到的命令。输入和输出路径使用绝对路径，每篇文章独立命名。

```bash
python3 examples/publish.py check
python3 examples/publish.py prepare article.json --out request.json
python3 examples/publish.py preview request.json --out preview.html --request-out confirmed.json
python3 examples/publish.py publish confirmed.json
```

首次缺配置时运行 `setup` 并耐心引导；`prepare` 不需要凭据，其他三步自动加载凭据。发布使用固定的 `confirmed.json`，不在请求内放 Token。成功需同时有 `data.status=success` 与 `draft_media_id`；超时或 unknown 停止自动重发并核对草稿箱，详见 [SKILL.md](SKILL.md)。

## 遇到问题时

- 没找到配置文件：Agent 先执行 `setup`，提供输出中的真实路径并帮忙打开，不要求用户寻找不存在的文件。
- 文件格式错误：保留双引号、逗号和大括号，保存 UTF-8；Agent 不输出含密钥的解析错误原文或文件全文。
- 401：打开 [Token 页面](https://chengzhang.page/tokens)，重新创建口令，替换本机配置中的旧值。
- 公众号配置缺失：打开 [公众号配置](https://chengzhang.page/settings/wechat) 完成设置。
- 40164：在公众号配置页面检测连接，按返回的实际出口 IP 设置白名单。
- 点数不足：在网页兑换或联系管理员，仍可预览。
- 网络权限或连接失败：Agent 先检查执行环境和网络授权，不把网络失败直接认定为口令无效。

## AppID、AppSecret 从哪里获取？

打开 [微信开发者平台](https://developers.weixin.qq.com/platform) 并登录 → 导航栏 **我的业务与服务** → **选择公众号** → **基础信息**。在这里找到 AppID、AppSecret 和 APP IP白名单。将凭证直接填入 [成章公众号配置页](https://chengzhang.page/settings/wechat)，点击 **保存并测试连接**；不要把 AppSecret 发到聊天中。

具体解释、白名单步骤和常见错误见 [公众号连接 FAQ](docs/FAQ.md)。
