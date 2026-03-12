---
status: published
repo: https://github.com/spinnakergit/a0-discord
index_status: in index
published_date: 2026-03-10
version: 1.0.0
---

# Release Status

## Publication
- **GitHub**: https://github.com/spinnakergit/a0-discord
- **Plugin Index**: Already in [agent0ai/a0-plugins](https://github.com/agent0ai/a0-plugins) index
- **Published**: 2026-03-10

## Verification Completed
- **Automated Tests**: 52/52 PASS
- **Human Verification**: Completed (red-team exercise, pre-framework)
- **Security Assessment**: Red-team pentest completed 2026-03-09 (report committed as redacted pentest report)

## Commit History
| Hash | Date | Description |
|------|------|-------------|
| `5a29b75` | 2026-03-10 | Add required name field and update settings store docs |
| `d2f4f9f` | 2026-03-09 | Add redacted pentest report from red team exercise |
| `c887150` | 2026-03-09 | Security hardening: CSRF protection, auth key masking, regression test suite |
| `69c18b7` | 2026-03-09 | Chat bridge security overhaul: thread-safe lifecycle, user allowlist, elevated mode |
| `f3e50bc` | 2026-03-09 | Security hardening: architectural privilege isolation and input validation |
| `7827ffc` | 2026-03-08 | Initial commit: Discord integration plugin for Agent Zero |

## Notes
- Discord was the first chat-bridge plugin built and served as the reference implementation for Signal, Telegram, and Slack.
- Verification was conducted before the formal HUMAN_VERIFICATION_FRAMEWORK was established; the red-team exercise served as both human verification and security assessment.
