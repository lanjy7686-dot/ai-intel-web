# AI情报雷达｜网页端

这是一个可以部署到 **GitHub Pages** 的网页端AI资讯雷达。

## 网页功能

- 聚合全球新闻、X、arXiv、Hacker News、RSS、微信公众号公开文章链接
- 自动去重、分类、相关度评分
- 支持关键词、分类、来源、时间筛选
- 手机和电脑自适应
- GitHub Actions 每30分钟自动抓取并更新网页
- 不需要本地安装，不需要常开电脑

## 直接预览

双击 `index.html` 可以打开离线预览。离线状态显示示例数据；部署上线后读取 `data/articles.json` 的实时数据。

## 上线步骤

1. 在 GitHub 新建一个公开仓库，例如 `ai-intel-web`。
2. 把本项目全部文件上传到仓库根目录。
3. 进入仓库 `Settings → Pages`。
4. 在 `Build and deployment → Source` 选择 `GitHub Actions`。
5. 进入 `Actions`，运行“更新并部署AI情报雷达”。
6. 部署成功后，Pages页面会显示网页地址。

## X配置

进入：

`Settings → Secrets and variables → Actions → New repository secret`

新增：

- Name：`X_BEARER_TOKEN`
- Secret：你的X官方API Bearer Token

没有配置时，系统自动跳过X，不影响其他来源。

## 微信公众号

编辑：

`config/wechat_urls.txt`

每行加入一个公开公众号文章链接。系统不绕过登录、验证码或访问控制。

也可以在 `config/sources.json` 中添加RSSHub生成的订阅地址，作为普通RSS来源。

## 修改资讯来源

编辑 `config/sources.json`。

RSS格式：

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

- GitHub定时任务通常接近每30分钟运行，但高峰期可能延迟。
- X需要官方开发者权限与API配额。
- 网站、RSS、公众号内容应遵守平台条款、版权与合理使用要求。
- 投资资讯只作信息整理，不构成投资建议。
