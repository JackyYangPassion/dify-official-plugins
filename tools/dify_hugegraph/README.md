# HugeGraph Dify Tool Plugin

这是一个用于 Dify 的 HugeGraph 图数据库集成插件，提供了完整的图数据库操作功能。

## 功能特性

- **顶点管理**: 添加、查询、删除顶点
- **边管理**: 添加、查询、删除边
- **图查询**: 支持 Gremlin 和 Cypher 查询语言
- **模式管理**: 获取图模式信息
- **批量操作**: 列出顶点和边
- **身份验证**: 支持用户名/密码认证

## 支持的操作

### 顶点操作
- `add_vertex`: 添加新顶点
- `get_vertex`: 根据ID获取顶点
- `list_vertices`: 列出图中的顶点
- `delete_vertex`: 删除顶点

### 边操作
- `add_edge`: 在两个顶点间添加边
- `get_edge`: 根据ID获取边
- `list_edges`: 列出图中的边
- `delete_edge`: 删除边

### 查询操作
- `gremlin_query`: 执行Gremlin查询
- `cypher_query`: 执行Cypher查询
- `get_schema`: 获取图模式信息

## 配置参数

- **host**: HugeGraph服务器主机地址 (默认: localhost)
- **port**: HugeGraph服务器端口 (默认: 8080)
- **graph**: 图数据库名称 (默认: hugegraph)
- **username**: 认证用户名 (可选)
- **password**: 认证密码 (可选)

## 使用示例

### 添加顶点
```json
{
  "label": "person",
  "properties": {
    "name": "张三",
    "age": 30
  }
}
```

### 添加边
```json
{
  "label": "knows",
  "source_id": "person:zhangsan",
  "target_id": "person:lisi",
  "properties": {
    "since": "2020"
 }
}
```

### Gremlin查询
```
g.V().has('person', 'name', '张三').out('knows')
```

### Cypher查询
```cypher
MATCH (p:person {name: '张三'})-[:knows]->(friend)
RETURN friend
```

## 安装

1. 将插件文件夹复制到 Dify 插件目录
2. 安装依赖：`pip install -r requirements.txt`
3. 在 Dify 中启用插件

## 注意事项

- 确保 HugeGraph 服务正在运行且可访问
- 检查防火墙设置，确保端口开放
- 如使用认证，请提供正确的用户名和密码
- 建议在生产环境中启用 HTTPS
