# 让 Agent 帮你上传公众号草稿

安装完整 `chengzhang` 技能包后，网址已内置为 [成章](https://chengzhang.page)。你只需保存一次自己的连接口令。

## 第一步：创建连接口令

打开 [API Token 页面](https://chengzhang.page/tokens) 并登录。在“创建新 token”的“名称”框输入 `WorkBuddy`，点击“创建”，然后点击新口令右侧的复制按钮。也可从文章编辑页顶部右侧的 **API Token** 进入。

完整口令以 `wp_` 开头，只显示一次。不要将它粘贴到聊天里。

## 第二步：让 Agent 帮你打开配置文件

对 Agent 说：

> 请帮我配置成章公众号草稿技能。使用默认网址，检测我的 Mac 或 Windows 系统，创建本机配置文件并用文本编辑器打开。Token 由我自己粘贴；保存后请帮我检查连接，不要读取或显示 Token。

Agent 会运行 `setup` 创建空文件。你只需把口令粘贴到 `token` 后面的空双引号中并保存，再说“已保存，请检查连接”。不需要自己配置环境变量或执行 `source`。

Mac／Windows 的完整操作、文件路径与排查见 [接入指南](SKILL_README.md)。

## 第三步：完成公众号配置并开始使用

如果尚未配置公众号，打开 [公众号配置](https://chengzhang.page/settings/wechat)，填写 AppID、AppSecret 并完成连接检测。已有配置直接复用。

可以告诉 Agent：

> 请用 chengzhang skill 将这篇文章排版，插入配图并生成摘要和封面，保存到公众号草稿箱。

只想预览时说“先预览，不上传”。上传草稿不会向粉丝群发；最终发布在公众号后台完成。更换电脑需在新电脑上配置一次，更新技能包不影响已保存的配置。

## AppID、AppSecret 从哪里获取？

打开 [微信开发者平台](https://developers.weixin.qq.com/platform) 并登录 → 导航栏 **我的业务与服务** → **选择公众号** → **基础信息**。在这里找到 AppID、AppSecret 和 APP IP白名单。将凭证直接填入 [成章公众号配置页](https://chengzhang.page/settings/wechat)，点击 **保存并测试连接**；不要把 AppSecret 发到聊天中。

具体解释、白名单步骤和常见错误见 [公众号连接 FAQ](docs/FAQ.md)。
