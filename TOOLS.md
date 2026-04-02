# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Delivery Gotchas

- **HTML to iPhone/iPad via Telegram**: ALWAYS use zero-JavaScript static HTML. iOS Safari blocks `<script>` execution on `file://` URLs. If a JS version shows blank content, switch to pure static HTML immediately. (See: LRN-20260331-007)
- **Composio OpenClaw Plugin**: Plugin `@composio/openclaw-plugin` cannot load persistently due to OpenClaw 2026.3.24 plugin ID mismatch bug. Don't waste time re-installing. Use Google Apps Script for Sheets automation instead. (See: ERR-20260331-001)

