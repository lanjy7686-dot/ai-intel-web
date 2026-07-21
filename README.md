# AI情报雷达｜完全免费网页端

这是一个部署在 **GitHub Pages** 上的AI资讯雷达，不需要服务器，不调用付费X API。

## 免费模式功能

- 自动聚合中文和英文AI新闻RSS
- 自动抓取OpenAI、Google AI、MIT Technology Review、TechCrunch、VentureBeat、The Verge、GitHub AI、Hugging Face、机器之心、量子位等公开订阅源
- 自动抓取arXiv最新AI论文
- 自动抓取Hacker News技术社区动态
- 自动聚合Reddit公开AI社区的新帖子，并保留社区、作者和原帖链接
- 提供X和Reddit免费实时搜索入口
- 自动去重、分类、相关度评分
- 支持关键词、分类、来源和时间筛选
- GitHub Actions每2小时自动更新

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

## 微信公众号

编辑 `config/wechat_urls.txt`，每行加入一个公开公众号文章链接。系统不绕过登录、验证码或访问控制。

## 手动更新

进入GitHub仓库的 `Actions` 页面，选择“更新并部署AI情报雷达”，点击 `Run workflow`。

## 注意

- Reddit公开订阅可能偶尔触发访问频率限制；网页同时提供Reddit站内搜索作为备用入口。
- 内容仅作公开信息聚合，不构成投资建议。
- 使用网站、RSS、Reddit和公众号内容时，应遵守平台条款、版权和合理使用要求。
