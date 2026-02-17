# Cloudflare IPv6 DDNS

这是一个轻量级的 Python 脚本，用于自动更新 Cloudflare 的 DNS AAAA 记录。特别适用于只有公网 IPv6 环境的家庭服务器或虚拟机。

## 特性

- **零依赖**：仅使用 Python 标准库，无需安装任何第三方包。
- **本地优先**：优先通过 `ip addr` 命令获取全球单播 IPv6 地址，快速且准确。
- **自动降级**：若本地获取失败，自动回退到外部 API（ipify/ident.me）探测。
- **自动创建**：如果 Cloudflare 中不存在指定的解析记录，脚本会自动创建。
- **安全**：使用 Cloudflare API Token 认证，支持最小权限原则。

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/xxb/ddns.git
cd ddns
```

### 2. 准备配置文件
复制示例配置文件并修改：
```bash
cp config.json.example config.json
```

#### 获取 Cloudflare 凭据指引：

**A. 获取 Zone ID：**
1. 登录 [Cloudflare 控制台](https://dash.cloudflare.com/)。
2. 点击你的域名。
3. 在“概述 (Overview)”页面右侧栏向下滚动，即可看到 **Zone ID**。

**B. 创建 API Token：**
1. 访问 [API 令牌页面](https://dash.cloudflare.com/profile/api-tokens)。
2. 点击 **创建令牌 (Create Token)**。
3. 选择 **编辑区域 DNS (Edit zone DNS)** 模板。
4. 在“区域资源”部分，选择 `包括 (Include) -> 特定区域 (Specific zone) -> 你的域名`。
5. 点击继续并生成令牌。**请注意：令牌只显示一次，务必妥善保存。**

编辑 `config.json`，填入你的信息：
```json
{
    "api_token": "你的_CLOUDFLARE_API_TOKEN",
    "zone_id": "你的_ZONE_ID",
    "record_name": "ddns.yourdomain.com",
    "proxied": false
}
```
> **提示**：建议为 API Token 仅授予 `Zone.DNS:Edit` 权限。

### 3. 测试运行
```bash
python3 ddns.py
```

## 自动化

推荐使用 `crontab` 设置每 5 分钟自动检查一次：

1. 输入 `crontab -e`
2. 添加以下行（请根据实际情况修改路径）：
```bash
*/5 * * * * /usr/bin/python3 /path/to/ddns/ddns.py >> /path/to/ddns/ddns.log 2>&1
```

## 注意事项
- 脚本默认排除 `fe80` 开头的链路本地地址。
- `.gitignore` 已配置，你的 `config.json` 不会被推送到 Git 仓库，确保了凭据安全。

## License
MIT
