# Company Gateway Model Plugin

A Dify custom model plugin that provides access to multiple AI models through a company internal gateway.

## Overview

This plugin enables Dify to connect to AI models through your company's internal gateway, supporting unified access to GPT-4, Qwen, DeepSeek, and Doubao models via a standardized OpenAI-compatible API.

## Supported Models

- **GPT-4 128K**: Advanced reasoning with 128K context window
- **Qwen Plus**: Alibaba's flagship model with strong Chinese capabilities
- **Qwen Turbo**: Fast and efficient version of Qwen
- **DeepSeek Chat**: General conversation model
- **DeepSeek Coder**: Specialized coding model
- **Doubao Pro**: ByteDance's premium model
- **Doubao Lite**: Lightweight version of Doubao

## Configuration

### Gateway Settings

- **API Base URL**: Your company's gateway URL (default: `http://xyz.cn`)
- **API Key**: Authentication token for the gateway
- **Custom Headers**: Optional additional headers (e.g., `hller: jason.zhang`)

### Model Parameters

- **Temperature**: Controls randomness (0.0-2.0)
- **Top P**: Nucleus sampling parameter
- **Max Tokens**: Maximum tokens to generate
- **Presence Penalty**: Penalize new token appearances (-2.0 to 2.0)
- **Frequency Penalty**: Penalize token frequency (-2.0 to 2.0)
- **Response Format**: Text, JSON object, or JSON schema

## API Format

The plugin expects the gateway to provide OpenAI-compatible endpoints:

```
POST {base_url}/{model_name}
Authorization: Bearer {api_key}
Content-Type: application/json
{custom_header_name}: {custom_header_value}

{
  "messages": [
    {
      "role": "user",
      "content": "Hello, world!"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

## Features

- ✅ OpenAI-compatible API integration
- ✅ Streaming and non-streaming responses
- ✅ Tool calling support
- ✅ Automatic token calculation
- ✅ Error handling and retry logic
- ✅ Custom header support
- ✅ Multiple model support
- ✅ Cost tracking

## Installation

1. Copy the `company_gateway` directory to your Dify plugins models folder
2. Configure the gateway URL and credentials
3. Select and test your desired models

## Usage Example

```bash
# Test the gateway connection
curl --location --request POST 'http://xyz.cn/gpt4-128k' \
--header 'Authorization: Bearer your_api_key' \
--header 'hller: jason.zhang' \
--header 'Content-Type: application/json' \
--data '{
  "messages": [
    {
      "content": "Hello, how can you help me today?",
      "role": "user"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}'
```

## Error Handling

The plugin handles various error scenarios:

- **Authentication errors**: Invalid API key or unauthorized access
- **Network errors**: Connection timeouts, DNS failures
- **Model errors**: Model not available, invalid parameters
- **Gateway errors**: Service unavailable, rate limiting

## Performance

- HTTP connection pooling for efficiency
- Configurable timeout settings
- Request retry with exponential backoff
- Streaming support for real-time responses

## Security

- Encrypted credential storage
- Secure API key handling
- Custom header support for additional authentication
- Request validation and sanitization

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check gateway URL is accessible
   - Verify network connectivity
   - Confirm API key is valid

2. **Authentication Error**
   - Validate API key format
   - Check custom header requirements
   - Verify gateway authentication method

3. **Model Not Found**
   - Confirm model name matches gateway endpoints
   - Check model availability
   - Verify model permissions

### Debug Logging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('company_gateway').setLevel(logging.DEBUG)
```

## Support

For issues and questions:

1. Check the gateway API documentation
2. Verify model endpoint availability
3. Review plugin logs for errors
4. Contact your system administrator

## License

This plugin is provided under your company's internal license terms.

---

**Note**: This plugin requires access to your company's internal AI gateway. Contact your IT department for access credentials and endpoint information.
