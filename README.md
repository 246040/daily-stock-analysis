# AI Trade A - 港股/A股智能监控分析平台

基于 AI 大模型的股票监控分析工具，覆盖 A股和港股，每日自动生成分析报告并通过邮件推送。

> ⚠️ 仅供学习研究，不构成投资建议。AI 分析仅作参考，投资有风险，决策需谨慎。

## 功能特性

- 📊 **实时行情**：AkShare 获取 A股/港股实时数据
- 📈 **技术分析**：自动计算 MA/MACD/RSI/KDJ/布林带
- 🤖 **AI 分析**：DeepSeek 大模型生成专业分析报告
- ⚠️ **智能预警**：价格突破、MACD金叉、放量异动、止损触发
- 📧 **邮件推送**：HTML 格式报告自动发送
- ⏰ **定时执行**：支持本地调度和 GitHub Actions

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

```bash
cp config/config.example.yaml config/config.yaml
```

编辑 `config/config.yaml`，填入：
- AI API Key（DeepSeek 免费注册即可）
- 邮箱 SMTP 配置（QQ邮箱需用授权码）
- 收件人列表

编辑 `config/stocks.yaml` 设置你的自选股。

### 3. 测试连接

```bash
python -m src.main --mode test
```

### 4. 运行每日分析

```bash
python -m src.main --mode daily
```

### 5. 仅预警检测

```bash
python -m src.main --mode alert
```

## 运行模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `daily` | 完整分析 + 报告 + 推送 | 每日收盘后运行 |
| `alert` | 仅预警检测 + 通知 | 盘中高频检测 |
| `test` | 验证数据源连接 | 首次配置验证 |

## 项目结构

```
├── config/
│   ├── config.example.yaml  # 配置模板
│   └── stocks.yaml          # 自选股 + 预警规则
├── src/
│   ├── main.py              # 主入口
│   ├── data/
│   │   ├── fetcher.py       # 行情数据抓取
│   │   └── indicators.py    # 技术指标计算
│   ├── analysis/
│   │   ├── ai_engine.py     # AI 分析引擎
│   │   └── report.py        # 报告生成
│   ├── alert/
│   │   └── rules.py         # 预警规则引擎
│   └── notify/
│       └── email_sender.py  # 邮件推送
├── reports/                  # 生成的报告
└── logs/                     # 运行日志
```

## 支持的 AI 模型

- DeepSeek（推荐，免费额度）
- OpenAI GPT
- 本地 Ollama（qwen2.5、llama 等）

## GitHub Actions 自动化部署（推荐）

零成本、无服务器，Fork 后配置 Secrets 即可每日自动运行。

### 1. Fork 或 Clone 本仓库

### 2. 配置 GitHub Secrets

进入 `Settings → Secrets and variables → Actions → New repository secret`：

| Secret 名称 | 必填 | 说明 |
|-------------|------|------|
| `AI_API_KEY` | ✅ | AI 模型 API Key（DeepSeek 免费注册即可） |
| `STOCK_LIST` | ✅ | 自选股列表（见下方格式说明） |
| `EMAIL_SENDER` | 📧 | 发件人邮箱 |
| `EMAIL_PASSWORD` | 📧 | 邮箱授权码 |
| `EMAIL_RECIPIENTS` | 📧 | 收件人，多个用逗号分隔 |
| `WECHAT_WEBHOOK_URL` | 💬 | 企业微信群机器人 Webhook |
| `FEISHU_WEBHOOK_URL` | 💬 | 飞书群机器人 Webhook |

> 📧 和 💬 至少配置一种推送渠道

### 3. 配置 Variables（可选）

进入 `Settings → Secrets and variables → Actions → Variables`：

| Variable 名称 | 默认值 | 说明 |
|---------------|--------|------|
| `AI_PROVIDER` | `deepseek` | AI 提供商 |
| `AI_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `AI_MODEL` | `deepseek-chat` | 模型名称 |
| `EMAIL_ENABLED` | `false` | 是否启用邮件 |

### 4. STOCK_LIST 格式

```
代码:名称:止损价:目标价
```

- 港股代码加 `hk` 前缀
- 止损价和目标价可省略
- 多只股票用逗号分隔

示例：
```
600519:贵州茅台:1400:1800,000001:平安银行,hk00700:腾讯控股:300:500,hk09988:阿里巴巴-W
```

### 5. 启用 Actions

进入 `Actions` 标签页 → 点击 `I understand my workflows, go ahead and enable them`

- 默认每工作日北京时间 18:00 自动运行
- 也可以手动触发：`Actions → Daily Stock Analysis → Run workflow`

## 推送渠道

| 渠道 | 配置方式 | 消息格式 |
|------|---------|---------|
| 📧 邮件 | SMTP 配置 | HTML（带样式） |
| 💬 企业微信 | Webhook URL | Markdown |
| 💬 飞书 | Webhook URL | 富文本 Post |

## License

MIT
