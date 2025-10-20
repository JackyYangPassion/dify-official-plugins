# 公司网关模型插件部署指南

## 快速开始

### 1. 插件安装

将 `company_gateway` 目录复制到 Dify 的 models 目录下：

```bash
# 方式1：直接复制
cp -r company_gateway /path/to/dify/models/

# 方式2：使用软链接（开发模式）
ln -s /path/to/company_gateway /path/to/dify/models/
```

### 2. 重启 Dify 服务

```bash
# Docker 部署
docker-compose restart

# 源码部署
supervisorctl restart dify-api
supervisorctl restart dify-worker
```

### 3. 配置插件

1. 登录 Dify 管理界面
2. 进入 **设置 > 模型供应商**
3. 找到 **Company Gateway** 并点击配置
4. 填入以下信息：
   - **API Base URL**: `http://xyz.cn`
   - **API Key**: 您的网关API密钥
   - **Custom Header Name**: `hller`（可选）
   - **Custom Header Value**: `jason.zhang`（可选）

## 详细配置说明

### 网关配置参数

| 参数 | 必填 | 描述 | 示例 |
|------|------|------|------|
| API Base URL | ✅ | 网关基础URL | `http://xyz.cn` |
| API Key | ✅ | API认证密钥 | `your-api-key-here` |
| Custom Header Name | ❌ | 自定义请求头名称 | `hller` |
| Custom Header Value | ❌ | 自定义请求头值 | `jason.zhang` |

### 支持的模型列表

配置完成后，您可以使用以下模型：

| 模型名称 | 端点 | 上下文长度 | 适用场景 |
|----------|------|------------|----------|
| GPT-4 128K | `gpt4-128k` | 131,072 | 复杂推理、长文档处理 |
| Qwen Plus | `qwen-plus` | 32,768 | 中文对话、通用任务 |
| Qwen Turbo | `qwen-turbo` | 8,192 | 快速响应、简单任务 |
| DeepSeek Chat | `deepseek-chat` | 32,768 | 对话、文本生成 |
| DeepSeek Coder | `deepseek-coder` | 16,384 | 代码生成、编程辅助 |
| Doubao Pro | `doubao-pro` | 32,768 | 高质量对话 |
| Doubao Lite | `doubao-lite` | 8,192 | 轻量级任务 |

## 连接测试

### 命令行测试

```bash
# 测试 GPT-4 模型
curl --location --request POST 'http://xyz.cn/gpt4-128k' \
--header 'Authorization: Bearer YOUR_API_KEY' \
--header 'hller: jason.zhang' \
--header 'Content-Type: application/json' \
--data '{
  "messages": [
    {
      "content": "你好，请介绍一下你自己",
      "role": "user"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}'
```

### Dify 界面测试

1. 创建新的应用
2. 在模型设置中选择 **Company Gateway** 提供商
3. 选择任一支持的模型
4. 发送测试消息验证连接

## 故障排除

### 常见问题

#### 1. 连接失败
```
错误: Connection failed to gateway
```
**解决方案:**
- 检查网关URL是否正确且可访问
- 验证网络连接
- 确认防火墙设置

#### 2. 认证失败
```
错误: Authentication failed
```
**解决方案:**
- 检查API密钥是否正确
- 验证自定义请求头设置
- 确认密钥权限

#### 3. 模型不可用
```
错误: Model not found or unavailable
```
**解决方案:**
- 确认模型名称拼写正确
- 检查模型在网关中是否可用
- 验证模型访问权限

#### 4. 请求超时
```
错误: Request timeout
```
**解决方案:**
- 增加超时时间设置
- 检查网络延迟
- 减少请求内容长度

### 日志调试

启用详细日志记录：

```python
import logging
logging.getLogger('company_gateway').setLevel(logging.DEBUG)
```

日志文件位置：
- Docker: `/app/logs/`
- 源码: `./logs/`

### 性能优化

#### 1. 连接池配置
```python
# 在 common_gateway.py 中调整
retry_strategy = Retry(
    total=5,  # 增加重试次数
    backoff_factor=2  # 调整退避因子
)
```

#### 2. 超时设置
```python
# 调整请求超时
timeout=300  # 5分钟超时
```

#### 3. 并发限制
- 根据网关限制调整并发请求数
- 使用适当的请求间隔

## 监控与维护

### 健康检查

创建定期健康检查脚本：

```python
#!/usr/bin/env python3
import requests
import json

def health_check():
    url = "http://xyz.cn/gpt4-128k"
    headers = {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            print("✅ Gateway healthy")
            return True
        else:
            print(f"❌ Gateway error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    health_check()
```

### 使用统计

监控以下指标：
- 请求成功率
- 平均响应时间
- 错误类型分布
- 模型使用频率
- 成本统计

### 更新维护

#### 插件更新
1. 备份当前配置
2. 更新插件文件
3. 重启服务
4. 验证功能正常

#### 模型配置更新
- 新增模型：添加对应的 YAML 配置文件
- 修改参数：更新模型配置文件
- 删除模型：移除或重命名配置文件

## 安全注意事项

### 1. API密钥管理
- 使用强密钥
- 定期轮换密钥
- 限制密钥权限
- 避免在日志中记录密钥

### 2. 网络安全
- 使用HTTPS（如果网关支持）
- 配置适当的防火墙规则
- 限制访问来源IP

### 3. 数据保护
- 不在请求中包含敏感信息
- 定期清理日志文件
- 遵守数据保护法规

## 技术支持

如需技术支持，请提供以下信息：
1. 错误日志片段
2. 网关配置信息（隐藏敏感信息）
3. 问题重现步骤
4. Dify版本信息

---

## 附录

### A. 完整配置示例

```yaml
# Dify 配置示例
model_providers:
  company_gateway:
    api_base_url: "http://xyz.cn"
    api_key: "your-secret-api-key"
    custom_header_name: "hller"
    custom_header_value: "jason.zhang"
    enabled: true
```

### B. 环境变量配置

```bash
# .env 文件
COMPANY_GATEWAY_API_URL=http://xyz.cn
COMPANY_GATEWAY_API_KEY=your-secret-api-key
COMPANY_GATEWAY_HEADER_NAME=hller
COMPANY_GATEWAY_HEADER_VALUE=jason.zhang
```

### C. 批量测试脚本

```bash
#!/bin/bash
# test_all_models.sh

models=("gpt4-128k" "qwen-plus" "qwen-turbo" "deepseek-chat" "deepseek-coder" "doubao-pro" "doubao-lite")

for model in "${models[@]}"
do
    echo "Testing $model..."
    curl -s --location --request POST "http://xyz.cn/$model" \
    --header "Authorization: Bearer $API_KEY" \
    --header "Content-Type: application/json" \
    --data '{"messages":[{"role":"user","content":"hello"}],"max_tokens":10}' \
    | jq '.choices[0].message.content' || echo "❌ $model failed"
done
```
