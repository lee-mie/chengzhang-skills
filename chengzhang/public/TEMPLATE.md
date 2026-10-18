# 技能模板使用说明

最省事的方式是在成章网页调整模板并设为默认；Agent 未指定模板时沿用同一账号的默认模板。

需要选择或修改时，先读取 `GET /api/templates` 或 `GET /api/templates/{id}`，使用真实 ID 和返回的配置。官方模板只读；复制时将其 `config` 与新名称提交到 `POST /api/templates`。

组件主题可以用 `GET /api/templates/components/catalog` 获取当前支持的组件 ID、字段和参数范围，不猜测样式 ID。配置示例：

```json
{
  "name": "我的青绿主题",
  "config": {
    "css": {},
    "builder": {
      "version": 1,
      "primary": "#17867c",
      "light": "#e8f3f2",
      "font_family": "sans",
      "font_size": 16,
      "line_height": 1.8
    }
  }
}
```

只使用目录明确支持的字段和值。保留已有配置中未要求修改的部分；用户只要求发布文章时，不顺带修改模板。

使用 `POST /api/templates/preview`，请求 `{"config":{...},"article_content":"## 示例标题\n\n正文"}`，可以在保存前检查效果。

每篇文章通过 `POST /api/publish/preview` 固定当时的模板，发布携带 `preview_id`。更改正文、模板或排版模式后重新预览。已创建的公众号草稿不会随模板编辑自动改变。
