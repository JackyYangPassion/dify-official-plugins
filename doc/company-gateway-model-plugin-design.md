# 公司内部网关模型插件设计文档

## 1. 项目概述

本项目旨在为 Dify 创建一个自定义模型插件，支持通过公司内部网关接口访问多种AI模型。该插件将提供统一的接口来访问 GPT-4、Qwen、DeepSeek 和豆包等模型。

## 2. 技术架构

### 2.1 插件类型
- **类型**: Model Provider Plugin
- **支持的模型类型**: LLM (Large Language Model)
- **接口规范**: OpenAI API 兼容格式

### 2.2 系统架构图

```
Dify Application
       ↓
Company Gateway Plugin
       ↓
Internal Gateway API (http://xyz.cn/)
       ↓
Multiple AI Models (GPT-4, Qwen, DeepSeek, 豆包)
```

## 3. 接口规范

### 3.1 网关API格式
- **基础URL**: `http://xyz.cn/`
- **模型端点格式**: `http://xyz.cn/{model_name}`
- **认证方式**: Bearer Token
- **请求格式**: OpenAI Chat Completions API 兼容

### 3.2 请求示例
```bash
curl --location --request POST 'http://xyz.cn/gpt4-128k' \
--header 'Authorization: Bearer xxx' \
--header 'hller: jason.zhang' \
--header 'Content-Type: application/json' \
--data '{
  "messages": [
    {
      "content": "hello",
      "role": "user"
    }
  ]
}'
```

### 3.3 支持的模型列表
1. **GPT-4**: `gpt4-128k`
2. **Qwen**: `qwen-plus`, `qwen-turbo`
3. **DeepSeek**: `deepseek-chat`, `deepseek-coder`
4. **豆包(Doubao)**: `doubao-pro`, `doubao-lite`

## 4. 插件结构设计

### 4.1 目录结构
```
models/company_gateway/
├── _assets/
│   └── icon.svg
├── main.py
├── manifest.yaml
├── requirements.txt
├── models/
│   ├── common_gateway.py
│   └── llm/
│       ├── llm.py
│       ├── gpt4-128k.yaml
│       ├── qwen-plus.yaml
│       ├── qwen-turbo.yaml
│       ├── deepseek-chat.yaml
│       ├── deepseek-coder.yaml
│       ├── doubao-pro.yaml
│       └── doubao-lite.yaml
├── provider/
│   ├── company_gateway.py
│   └── company_gateway.yaml
└── README.md
```

### 4.2 关键组件说明

#### 4.2.1 Provider组件 (`provider/company_gateway.py`)
- 负责认证和连接管理
- 实现凭证验证逻辑
- 管理网关连接配置

#### 4.2.2 LLM组件 (`models/llm/llm.py`)
- 实现OpenAI兼容的API调用
- 处理请求/响应转换
- 支持流式和非流式响应
- 实现token计算逻辑

#### 4.2.3 Common组件 (`models/common_gateway.py`)
- 封装通用的API调用逻辑
- 实现错误处理和重试机制
- 提供基础的HTTP客户端功能

## 5. 配置参数设计

### 5.1 Provider凭证配置
```yaml
provider_credential_schema:
  credential_form_schemas:
    - variable: api_base_url
      label: "网关基础URL"
      type: text-input
      required: true
      default: "http://xyz.cn"
    - variable: api_key
      label: "API密钥"
      type: secret-input
      required: true
    - variable: custom_header
      label: "自定义请求头"
      type: text-input
      required: false
      placeholder: "hller: jason.zhang"
```

### 5.2 模型参数配置
- **temperature**: 控制随机性 (0.0-2.0)
- **max_tokens**: 最大生成token数
- **top_p**: 核采样参数
- **frequency_penalty**: 频率惩罚
- **presence_penalty**: 存在惩罚
- **stream**: 是否开启流式输出

## 6. 实现特性

### 6.1 核心功能
- ✅ 支持Chat Completions API
- ✅ 支持流式和非流式响应
- ✅ 自动token计算
- ✅ 错误处理和异常管理
- ✅ 多模型支持

### 6.2 高级功能
- ✅ 自定义请求头支持
- ✅ 网关健康检查
- ✅ 请求重试机制
- ✅ 响应缓存(可选)
- ✅ 请求日志记录

## 7. 安全考虑

### 7.1 认证安全
- API密钥加密存储
- 支持自定义认证头
- 请求签名验证(如需要)

### 7.2 网络安全
- HTTPS支持(如网关支持)
- 请求超时设置
- 连接池管理
- 防止API密钥泄露

## 8. 性能优化

### 8.1 连接优化
- HTTP连接复用
- 合理的超时设置
- 并发请求限制

### 8.2 响应优化
- 流式响应支持
- 压缩传输
- 响应缓存策略

## 9. 错误处理

### 9.1 网络错误
- 连接超时
- 网络不可达
- DNS解析失败

### 9.2 API错误
- 认证失败
- 模型不存在
- 请求格式错误
- 超出配额限制

### 9.3 业务错误
- 模型服务不可用
- 内容过滤
- 参数验证失败

## 10. 测试计划

### 10.1 单元测试
- Provider凭证验证
- API调用功能
- 错误处理逻辑
- Token计算准确性

### 10.2 集成测试
- 与Dify平台集成
- 多模型调用测试
- 流式响应测试
- 错误场景测试

### 10.3 性能测试
- 并发请求测试
- 大文本处理测试
- 长时间运行稳定性测试

## 11. 部署说明

### 11.1 依赖要求
- Python 3.12+
- requests库用于HTTP请求
- tiktoken库用于token计算
- dify_plugin SDK

### 11.2 配置步骤
1. 将插件目录放置到models/目录下
2. 配置网关API基础URL
3. 设置API密钥和自定义请求头
4. 选择需要使用的模型
5. 测试连接和模型调用

## 12. 维护指南

### 12.1 监控要点
- API调用成功率
- 响应时间
- 错误率统计
- 用量统计

### 12.2 升级策略
- 模型版本更新
- API接口变更适配
- 性能优化迭代
- 安全补丁更新

---

## 附录

### A. API响应格式示例
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt4-128k",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

### B. 错误响应格式示例
```json
{
  "error": {
    "message": "Invalid authentication",
    "type": "invalid_authentication",
    "code": "invalid_api_key"
  }
}
```
