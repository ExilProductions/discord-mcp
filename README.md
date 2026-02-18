# Discord MCP Server

A production-grade MCP (Model Context Protocol) server for Discord using FastMCP and discord.py.

## Features

- Per-token bot sessions with automatic session management
- Channel management (create, edit, delete, organize)
- Role management (create, edit, delete, manage)
- Permission configuration for channels, categories, and roles
- Message operations (send, edit, delete, bulk delete)
- Moderation actions (timeout, kick, ban, role policy enforcement)
- Guild/server settings management

## Installation

```bash
uv sync
```

## Configuration

Copy `.env.template` to `.env` and configure:

```bash
cp .env.template .env
```

## Usage

```bash
uv run python -m discord_mcp.main
```

## MCP Tools

### Channel Management
- `create_channel` - Create a text, voice, news, stage, forum, media, or category channel
- `edit_channel` - Edit a channel's settings
- `delete_channel` - Delete a channel
- `move_channel` - Move channel to new position/category
- `get_channel` - Get channel information
- `get_channels` - List all channels in guild

### Role Management
- `create_role` - Create a new role
- `edit_role` - Edit a role
- `delete_role` - Delete a role
- `assign_role` - Assign role to member
- `remove_role` - Remove role from member
- `get_role` - Get role information
- `get_roles` - List all roles in guild

### Permission Management
- `set_channel_permissions` - Set channel permissions
- `set_category_permissions` - Set category permissions
- `set_role_permissions` - Update role permissions
- `get_channel_permissions` - Get channel permission overwrites
- `get_category_permissions` - Get category permission overwrites
- `remove_channel_permissions` - Remove permission overwrites

### Message Operations
- `send_message` - Send a message (supports embeds, TTS, mentions, references)
- `edit_message` - Edit a message
- `delete_message` - Delete a message
- `bulk_delete_messages` - Bulk delete messages
- `get_message` - Get a message
- `get_channel_messages` - Get channel message history

### Moderation
- `timeout_user` - Timeout a member
- `remove_timeout` - Remove timeout from member
- `kick_user` - Kick a member
- `ban_user` - Ban a member
- `unban_user` - Unban a member
- `enforce_role_policy` - Enforce role policy (kick/ban members missing required roles)
- `get_guild_bans` - List guild bans
- `get_member_timeout_status` - Check timeout status

### Guild Management
- `get_guild_settings` - Get server settings (name, description, verification level, etc.)
- `edit_guild_settings` - Edit server settings

### Status
- `get_bot_status` - Get bot status and session info
