# AI情报雷达｜完全免费网页端

这是一个部署在 **GitHub Pages** 上的AI资讯雷达，不需要服务器，不调用付费X API。

## 免费模式功能

- 自动聚合中文和英文AI新闻RSS
- 自动抓取OpenAI、Google AI、MIT Technology Review、TechCrunch、VentureBeat等公开订阅源
- 自动抓取arXiv最新AI论文
- 自动抓取Hacker News技术社区动态
- 支持添加公开微信公众号文章链接
- 自动去重、分类、相关度评分
- 支持关键词、分类、来源和时间筛选
- 网页提供X实时搜索入口，点击后直接在X查看结果
- GitHub Actions每2小时自动更新
- 手机和电脑自适应

## X实时搜索

免费模式不调用X API，也不使用 `X_BEARER_TOKEN`，因此不会产生X API credits费用。

网页内预设：

- AI综合
- AI投资融资
- 大模型发布
- AI芯片算力
- AI机器人
- 中文AI动态

点击按钮会直接打开X实时搜索页面，查看内容时可能需要登录X账号。

此前添加的GitHub secret `X_BEARER_TOKEN` 已不再被工作流读取，可保留，也可以在仓库 `Settings → Secrets and variables → Actions` 中删除。

## 微信公众号

编辑：

`config/wechat_urls.txt`

每行加入一个公开公众号文章链接。系统不绕过登录、验证码或访问控制。

## 修改免费资讯来源

编辑 `config/sources.json`。RSS格式：

```json
{
  "name": "某AI网站",
  "url": "https://example.com/feed.xml",
  "source_type": "RSS",
  "language": "zh",
  "enabled": true
}
```

## 手动更新

进入GitHub仓库的 `Actions` 页面，选择“更新并部署AI情报雷达”，点击 `Run workflow`。

## 注意

- GitHub定时任务可能在高峰期延迟。
- 某个免费来源临时限流或无法访问时，其他来源仍会正常更新。
- 网站、RSS和公众号内容应遵守来源平台条款、版权与合理使用要求。
- 投资资讯只作信息整理，不构成投资建议。
