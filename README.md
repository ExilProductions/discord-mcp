# Discord MCP Server

A production-grade **Model Context Protocol (MCP)** server for Discord built with **FastMCP** and **discord.py**.
Provides a complete API surface for managing channels, roles, permissions, messages, moderation, and server settings via MCP.

---

# Features

* Per-token bot sessions with automatic session management
* Channel management: create, edit, delete, organize
* Role management: create, edit, delete, assign, remove
* Permission configuration for channels, categories, and roles
* Message operations: send, edit, delete, bulk delete, retrieve
* Moderation actions: timeout, kick, ban, enforce role policies
* Guild/server settings management
* Polls: create, end, and get results
* Scheduled events: create, edit, delete, list, get attendees
* Threads & forums: create, edit, delete, manage members, forum posts
* Webhooks: create, send messages, list, delete
* Invites: create, list, delete
* Emoji & stickers: create, delete, list
* Reactions: add, remove, list users, clear
* AutoMod: create, edit, delete, list rules
* Audit log: query with filters
* Member info: get details, list members, edit nicknames/mute/deafen
* Status endpoints for bot sessions

---

# Installation

```bash
uv sync
```

---

# Configuration

Copy the template `.env` file and modify it as needed:

```bash
cp .env.template .env
```

---

# Usage

Run the MCP server locally:

```bash
uv run python -m discord_mcp.main
```

Or use it without a local setup:

```bash
uv run --with git+https://github.com/ExilProductions/discord-mcp discord-mcp
```

---

# MCP Client Configuration Example

Example configuration for **OpenCode** using a remote MCP server:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "discord-mcp": {
      "type": "remote",
      "url": "http://localhost:8000/mcp",
      "enabled": true,
      "headers": {
        "Authorization": "YOUR_DISCORD_BOT_TOKEN"
      }
    }
  }
}
```

This can be used by any client that supports MCP.

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

### Polls
- `create_poll` - Create a poll in a channel
- `end_poll` - End an active poll
- `get_poll_results` - Get poll vote counts and results

### Scheduled Events
- `create_scheduled_event` - Create a scheduled event (voice, stage, or external)
- `edit_scheduled_event` - Edit a scheduled event
- `delete_scheduled_event` - Delete a scheduled event
- `list_scheduled_events` - List all scheduled events in a guild
- `get_scheduled_event_users` - Get users interested in an event

### Threads & Forums
- `create_thread` - Create a thread (optionally from a message)
- `edit_thread` - Edit thread settings (name, archive, lock, slowmode)
- `delete_thread` - Delete a thread
- `list_threads` - List active and archived threads in a channel
- `add_thread_member` - Add a member to a thread
- `remove_thread_member` - Remove a member from a thread
- `create_forum_post` - Create a forum post with tags

### Webhooks
- `create_webhook` - Create a webhook for a channel
- `send_webhook_message` - Send a message via webhook
- `list_webhooks` - List webhooks for a guild or channel
- `delete_webhook` - Delete a webhook

### Invites
- `create_invite` - Create a channel invite
- `list_invites` - List all guild invites
- `delete_invite` - Delete an invite

### Emoji & Stickers
- `create_emoji` - Create a custom emoji
- `delete_emoji` - Delete a custom emoji
- `list_emojis` - List all custom emojis in a guild
- `list_stickers` - List all stickers in a guild

### Reactions
- `add_reaction` - Add a reaction to a message
- `remove_reaction` - Remove a reaction from a message
- `get_reaction_users` - Get users who reacted with a specific emoji
- `clear_reactions` - Clear all or specific reactions from a message

### AutoMod
- `create_automod_rule` - Create an automod rule (keyword, spam, preset, mention spam)
- `edit_automod_rule` - Edit an automod rule
- `delete_automod_rule` - Delete an automod rule
- `list_automod_rules` - List all automod rules in a guild

### Audit Log
- `get_audit_log` - Query audit log with filters (user, action type, limit)

### Members
- `get_member_info` - Get detailed member profile info
- `list_members` - List guild members
- `edit_member` - Edit member (nickname, mute, deafen)

### Status
- `get_bot_status` - Get bot status and session info
