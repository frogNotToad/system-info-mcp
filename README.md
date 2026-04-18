# system-info-mcp

A local MCP (Model Context Protocol) server that gives your agent real-time access to hardware and OS information on your PC.

## What it does

Exposes your system as a set of MCP tools so your agent can query CPU, memory, disks, GPU and general OS details — all without leaving your machine.

## Available tools

| Tool | Description |
|------|-------------|
| `get_system_info` | OS name, version, architecture, processor, hostname |
| `get_cpu_info` | Per-core load %, physical/logical core count, current frequency |
| `get_mem_info` | Total, available, used, free RAM and detailed memory breakdown (bytes) |
| `get_disk_info` | All accessible partitions — mountpoint, filesystem type, total/used/free space |
| `get_gpu_info` | GPU name, driver version, and VRAM — cross-platform (Windows/Linux/macOS) |

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended)

## Installation

```bash
git clone https://github.com/your-username/system-info-mcp
cd system-info-mcp
uv sync
```

## Usage

### Running the server

```bash
uv run python system_info.py
```

The server communicates over stdio and follows the MCP specification.

### Connecting to your agent

Usually you should add something similar to your agent's config:

```json
{
  "mcpServers": {
    "system-info": {
      "command": "uv",
      "args": ["run", "python", "absolute/path/to/system_info.py"]
    }
  }
}
```

## Project structure

```
system-info-mcp/
├── system_info.py   # MCP server and all tools
├── pyproject.toml
└── uv.lock
```

## Known limitations

- On Windows, GPU VRAM reported by `get_gpu_info` may be incorrect. WMI returns the value as a 32-bit integer, which overflows for GPUs with more than ~2 GB of dedicated memory.

## AI usage

AI was used solely to improve docstring and inline comments, and to redact this README. This content was reviewed for correctness.

## License

MIT
