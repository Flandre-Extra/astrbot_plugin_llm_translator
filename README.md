# astrbot_plugin_llm_translator

AstrBot 插件：使用任意 OpenAI 兼容 API 将 LLM 回复翻译到目标语言。

## 安装

1. AstrBot Web 面板 → 插件管理 → 上传插件
2. 启用后进入配置页，API Key 留空则自动使用 AstrBot 当前聊天模型的 Key
3. 设置源语言和目标语言

## 配置项

| 配置 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `source_lang` | string | 中文 | 源语言 |
| `target_lang` | string | 日语 | 目标语言 |
| `send_original` | bool | false | 翻译后追发一条原文消息 |
| `bracket_filter` | bool | false | 翻译前过滤（旁白）、【注】、(stage) 等内容 |
| `api_base` | string | 空 | 留空自动匹配 AstrBot 聊天模型配置 |
| `api_key` | string | 空 | 留空自动使用 AstrBot 聊天模型 Key |
| `api_model` | string | 空 | 留空自动使用 AstrBot 聊天模型配置 |
| `max_tokens` | int | 4096 | 翻译输出上限 |
| `timeout` | int | 30 | 请求超时（秒） |

## 使用场景

### 单纯翻译

设好 source_lang / target_lang 即可，其他保持默认。

### 翻译 + 原文字幕

`send_original` = true，翻译后额外发送原文。原文不受 bracket_filter 影响。

### 翻译 + 括号过滤

`bracket_filter` = true，翻译前移除旁白描述，仅翻译主体对话。
