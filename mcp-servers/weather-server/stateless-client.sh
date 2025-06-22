#!/usr/bin/env bash
set -euo pipefail

S=http://127.0.0.1:3002/mcp/
ACCEPT='application/json, text/event-stream'
CT='application/json'

# tools/list
curl -sS \
  -H "Accept: $ACCEPT" \
  -H "Content-Type: $CT" \
  -X POST "$S" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# tools/call
curl -sS \
  -H "Accept: $ACCEPT" \
  -H "Content-Type: $CT" \
  -X POST "$S" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{
        "name":"get_current_weather",
        "arguments":{"city":"New York"}
      }}'
echo