# Privacy Policy for HugeGraph Query Plugin

## Data Collection and Usage

The HugeGraph Query Plugin for Dify collects and processes the following data:

### Data Collected
- **Connection Information**: HugeGraph server host, port, and graph database name
- **Authentication Credentials**: Username and password (when provided)
- **Query Data**: Gremlin queries, Cypher queries, and graph operation parameters
- **Graph Data**: Vertices, edges, properties, and schema information retrieved from your HugeGraph database

### How Data is Used
- **Direct Communication**: All data is transmitted directly between Dify and your specified HugeGraph server
- **Query Execution**: Queries and operations are executed on your HugeGraph instance
- **Result Processing**: Graph data returned from HugeGraph is processed and displayed within Dify workflows

## Data Transmission and Security

### Network Communication
- All communications occur between your Dify instance and your HugeGraph server
- Data transmission follows HTTP/HTTPS protocols as configured in your HugeGraph server
- No data is transmitted to external third-party services beyond your HugeGraph server

### Credential Security
- Authentication credentials are handled securely within the Dify plugin framework
- Passwords are stored as encrypted secrets within Dify's credential management system
- Credentials are only used for authentication with your specified HugeGraph server

## Data Retention and Storage

### Plugin Operation
- The plugin does not store query results or graph data persistently
- Connection credentials are stored securely within Dify's configuration system
- Temporary data exists only during query execution and processing

### Logging
- Standard plugin operation logs may be generated for debugging purposes
- Logs do not contain sensitive credential information or detailed graph data
- Log retention follows your Dify instance's logging policies

## Third-Party Data Sharing

### No External Transmission
- This plugin does not transmit data to any external services beyond your configured HugeGraph server
- No analytics, telemetry, or usage data is sent to plugin developers or external parties
- All graph operations remain within your controlled infrastructure

## User Rights and Control

### Data Access Control
- Users maintain complete control over their HugeGraph server and data
- Plugin access is limited to operations explicitly configured and authorized
- Users can revoke plugin access by removing or modifying credentials at any time

### Configuration Management
- All connection and credential settings are user-configurable
- Users can modify or remove plugin configuration through Dify's interface
- No hidden or automatic data collection occurs

## Contact Information

For questions about this privacy policy or plugin data handling:
- Plugin Repository: [Your repository URL]
- Issues: [Your issues URL]

## Updates to Privacy Policy

This privacy policy may be updated to reflect changes in the plugin's functionality or data handling practices. Users will be notified of significant changes through plugin update notifications.

**Last Updated:** September 26, 2025
**Plugin Version:** 0.0.1