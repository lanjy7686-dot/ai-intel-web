# AI情报雷达｜完全免费网页端

这是一个部署在 **GitHub Pages** 上的AI资讯雷达，不需要服务器，不调用付费X API。

## 免费模式功能

- 自动聚合中文和英文AI新闻RSS
- 自动抓取OpenAI、Google AI、MIT Technology Review、TechCrunch、VentureBeat、The Verge、GitHub AI、Hugging Face、机器之心、量子位等公开订阅源
- 新增中文AI新闻、AI投资融资、AI技术开源聚合源
- 自动抓取arXiv最新AI论文
- 自动抓取Hacker News技术社区动态
- 自动聚合Reddit公开AI社区的新帖子，并保留社区、作者和原帖链接
- 提供微信公众号、小红书、抖音、X和Reddit免费实时搜索入口
- 支持收藏公开微信公众号文章、小红书笔记和抖音内容链接
- 自动去重、分类、相关度评分
- 支持关键词、分类、来源和时间筛选
- GitHub Actions每小时自动更新

## 最新资讯规则

- 默认只展示近24小时内容，可切换近3天、近7天和近30天。
- 没有可靠发布时间的内容直接剔除，不再把抓取时间误当成发布时间。
- Google新闻专题查询自动加入 `when:1d` 或 `when:3d` 时间条件。
- 官方博客最多保留近7天；新闻聚合和媒体资讯通常保留近24小时至3天。
- 页面会显示“刚刚、几分钟前、几小时前、几天前”，鼠标悬停可查看完整发布时间。

## 国内平台模式

### 微信公众号

编辑 `config/wechat_urls.txt`。支持：

```text
公开文章链接
```

或更稳定的格式：

```text
链接 | 标题 | 公众号名称 | 一句话摘要 | 发布时间
```

网页中的微信公众号按钮会打开搜狗公开文章搜索，并按近24小时、近3天等时间范围筛选。

### 小红书

编辑 `config/xiaohongshu_urls.txt`：

```text
链接 | 标题 | 作者 | 一句话摘要 | 发布时间
```

免费模式不模拟登录、不批量爬取；网页提供小红书站内搜索入口。

### 抖音

编辑 `config/douyin_urls.txt`：

```text
链接 | 标题 | 作者 | 一句话摘要 | 发布时间
```

免费模式不模拟登录、不绕过验证码；网页提供抖音站内搜索入口。官方搜索API需要单独申请应用、权限和访问令牌，本项目默认不启用。

## 当前Reddit社区

- r/MachineLearning
- r/LocalLLaMA
- r/artificial
- r/OpenAI
- r/singularity
- r/robotics
- r/StableDiffusion
- r/LanguageTechnology
- r/MLQuestions
- r/ChatGPT

可在 `config/sources.json` 的 `reddit.communities` 中增加或删除社区。

## X完全免费模式

本项目不调用X API，也不会产生X API费用。网页中的X按钮会直接打开X站内实时搜索。

此前配置的 `X_BEARER_TOKEN` 已不再使用，可以在GitHub仓库的 `Settings → Secrets and variables → Actions` 中删除。

## 手动更新

进入GitHub仓库的 `Actions` 页面，选择“更新并部署AI情报雷达”，点击 `Run workflow`。

## 注意

- Reddit公开订阅可能偶尔触发访问频率限制；网页同时提供Reddit站内搜索作为备用入口。
- 微信公众号、小红书和抖音的免费模式主要依靠站内搜索与公开链接收藏，不能保证全网自动抓取。
- 内容仅作公开信息聚合，不构成投资建议。
- 使用网站、RSS和社交平台内容时，应遵守平台条款、版权和合理使用要求。
