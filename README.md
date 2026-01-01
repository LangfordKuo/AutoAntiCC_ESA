# 阿里云 ESA 自动开盾脚本

> 基于系统负载自动启用/禁用阿里云 ESA WAF 规则的智能脚本
>
> 超级详细的图文教程链接https://lyew.com/helpcontent/33.html

## 🚀 项目简介

本脚本是一个自动化工具，用于监控服务器系统负载，并在负载超过预设阈值时自动启用阿里云 ESA WAF规则，提供智能防护能力。当系统负载恢复正常后，脚本会自动关闭 WAF 规则，实现按需防护。

## ✨ 功能特性

- 🔄 **智能负载监控**：实时监控系统 CPU 负载（1分钟平均值）
- 🛡️ **自动开盾/关盾**：根据负载阈值自动启用/禁用 WAF 规则
- 📝 **状态记录**：使用本地文件记录开盾时间，避免重复操作
- ⚙️ **灵活配置**：所有参数通过配置文件管理，便于维护
- 🐧 **跨平台支持**：支持 Linux、macOS 等类 Unix 系统
- 🎯 **精确控制**：可配置负载阈值、开盾时间窗口等参数
- 📊 **详细日志**：提供清晰的执行日志，便于问题排查

## 📋 系统要求

- Python 3.7 或更高版本
- 支持 `os.getloadavg()` 的操作系统（Linux、macOS 等）
- 阿里云 ESA 服务权限
- 有效的阿里云 AccessKey

## 🔧 安装步骤

### 1. 克隆或下载项目

```bash
git clone https://github.com/LangfordKuo/AutoAntiCC_ESA
cd AutoAntiCC_ESA
```

### 2. 安装依赖包

```bash
pip3 install -r requirements.txt
```

如果尚未创建 `requirements.txt` 文件，可以手动安装所需依赖：

```bash
pip3 install alibabacloud_esa20240910==2.34.0
pip3 install requests
```

### 3. 配置参数

复制参数并填写您的阿里云信息：
编辑 `esa_config.json` 文件，填入您的实际信息。

## ⚙️ 配置文件详解

配置文件 `esa_config.json` 包含以下参数：

```json
{
    "_comment": "阿里云 ESA 脚本配置文件",
    "access_key_id": "必填，阿里云访问密钥ID",
    "access_key_secret": "必填，阿里云访问密钥Secret",
    "site_id": 必填，ESA站点ID,（这里填写ID不要带双引号，直接在逗号前面写就行）
    "rule_id": 必填，ESA规则ID,（这里填写ID不要带双引号，直接在逗号前面写就行）
    "load_threshold": 80.0,
    "shield_record_window_minutes": 15,
    "endpoint": "esa.cn-hangzhou.aliyuncs.com"
}
```

### 参数说明：

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `access_key_id` | string | 无 | 阿里云 AccessKey ID |
| `access_key_secret` | string | 无 | 阿里云 AccessKey Secret |
| `site_id` | integer | 无 | ESA 站点 ID |
| `rule_id` | integer | 无 | ESA WAF 规则 ID |
| `load_threshold` | float | 80.0 | 负载阈值（百分比），超过此值则开盾 |
| `shield_record_window_minutes` | integer | 15 | 开盾记录有效时间（分钟） |
| `endpoint` | string | "esa.cn-hangzhou.aliyuncs.com" | ESA API 端点 |

## 🚀 使用方法

### 手动运行

直接执行脚本：

```bash
python3 esaanticc.py
```

### 定时任务（推荐）

宝塔面板计划任务中添加即可，建议每一分钟执行一次。

### 运行示例

正常情况（负载未超过阈值）：

```
2025-01-01 10:30:00 检测到CPU负载45.20，未超过阈值80.0
```

负载超过阈值，自动开盾：

```
2025-01-01 10:35:00 检测到CPU负载85.50，超过阈值80.0，执行开盾策略
2025-01-01 10:35:01 调用API开盾成功
2025-01-01 10:35:01 开盾时间已记录: 2025-01-01 10:35:01
```

负载恢复正常，自动关盾：

```
2025-01-01 10:50:00 检测到CPU负载40.30，未超过阈值80.0
2025-01-01 10:50:00 检测到开盾记录已超过15分钟(15.2分钟)，执行关盾策略
2025-01-01 10:50:01 调用API关盾成功
开盾记录已清空
```

## 📁 文件说明

- `esaanticc.py` - 主脚本文件，包含所有核心逻辑
- `esa_config.json` - 配置文件，存储阿里云认证信息和运行参数
- `esa.txt` - 开盾记录文件（自动生成），记录最后一次开盾时间
- `README.md` - 本文档

## 🔍 工作原理

1. **负载检测**：脚本调用 `os.getloadavg()` 获取系统 1 分钟平均负载
2. **阈值比较**：将当前负载与配置的 `load_threshold` 比较
3. **状态判断**：检查是否有最近的开盾记录（避免重复操作）
4. **API 调用**：根据负载情况调用阿里云 ESA API 启用或禁用 WAF 规则
5. **状态记录**：开盾成功后记录时间到 `esa.txt` 文件
6. **自动恢复**：负载恢复正常且开盾时间超过设定窗口后，自动关闭 WAF 规则

## ⚠️ 注意事项

1. **系统兼容性**：脚本仅在支持 `os.getloadavg()` 的系统上运行（Linux、macOS 等）
2. **权限要求**：需要阿里云 ESA 服务的相应操作权限
3. **网络连接**：确保服务器可以访问阿里云 API 端点
4. **配置文件安全**：请妥善保管 `esa_config.json`，避免泄露 AccessKey
5. **阈值设置**：根据实际服务器性能合理设置 `load_threshold` 值
6. **时间窗口**：`shield_record_window_minutes` 控制开盾最小间隔，避免频繁开关

## 🐛 故障排除

### 常见问题

1. **"当前系统不支持 os.getloadavg()"**
   - 原因：脚本在 Windows 或不支持的系统上运行
   - 解决：仅在 Linux/macOS 等系统上使用

2. **"配置文件不存在" 或 "缺少必需字段"**
   - 原因：配置文件未正确创建或字段不完整
   - 解决：检查 `esa_config.json` 文件是否存在且格式正确

3. **"调用API开盾失败"**
   - 原因：阿里云认证失败、权限不足或网络问题
   - 解决：检查 AccessKey、站点ID、规则ID是否正确，确认网络连通性

4. **脚本无输出或立即退出**
   - 原因：可能依赖包未安装
   - 解决：运行 `pip3 install -r requirements.txt` 安装依赖

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个项目。

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 开启一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢阿里云提供 ESA 服务
- 灵感来源于实际运维需求
- 特别感谢AI的帮助，我自己几乎没动手

## 📞 支持与反馈

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 查看项目 README.md 文件获取更多帮助信息
- 高性价比云服务器：https://lyew.com

---

**让安全防护更智能，让运维工作更轻松！** 🚀
