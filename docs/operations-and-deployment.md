# Operations and deployment

## Audit logs

Every MCP tool call produces a JSON audit record containing the UTC timestamp, tool name, input, and output.

- In a source checkout, records are written to [logs](../logs/).
- In an installed package, records are written to `./logs/` under the directory where the server starts.
- Set `MCP_LOGS_PATH` to choose another location:

  ```bash
  MCP_LOGS_PATH=/path/to/product-search-logs product-search
  ```

A typical filename is:

```text
20260821T123456789000Z_<unique-id>.json
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `MCP_TRANSPORT` | `http` | Set to `http`/`streamable-http` for HTTP or `stdio` for a local stdio client. |
| `MCP_HOST` | `127.0.0.1` | HTTP server host. Set to `0.0.0.0` for a hosted service. |
| `PORT` | `8000` | HTTP server port. |
| `MCP_PATH` | `/mcp` | MCP endpoint path. |
| `MCP_PUBLIC_BASE_URL` | Derived from host and port | Public base URL used in returned image links. |
| `MCP_LOGS_PATH` | Repository `logs/` or `./logs/` | Directory for JSON audit logs. |


