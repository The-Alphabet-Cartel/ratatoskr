---
title: "Fluxer Platform Assessment — MilSim Community Edition"
description: "Research findings and platform recommendation for MilSim and tactical gaming communities evaluating Discord alternatives"
category: Research
tags:
  - fluxer
  - platform
  - migration
  - privacy
  - discord-alternative
  - milsim
  - arma3
version: "v1.0"
last_updated: "2026-02-25"
---
# Fluxer Platform Assessment
## MilSim & Tactical Gaming Community Edition

============================================================================
Platform Decision Briefing for Military Simulation and Tactical Gaming Communities
Research current as of February 25, 2026
============================================================================

**Document Version**: v1.0
**Created**: 2026-02-25
**Status**: ✅ Recommendation Reached
**Audience**: MilSim community leadership evaluating Discord alternatives

---

## Table of Contents

1. [Summary](#1-summary)
2. [What Is Fluxer](#2-what-is-fluxer)
3. [Why Fluxer Fits MilSim Communities](#3-why-fluxer-fits-milsim-communities)
4. [Honest Concerns](#4-honest-concerns)
5. [Hosted vs. Self-Hosted](#5-hosted-vs-self-hosted)
6. [Bot Infrastructure — Keeping Your Automation](#6-bot-infrastructure--keeping-your-automation)
7. [Platform Scorecard](#7-platform-scorecard)
8. [Evaluated Alternatives](#8-evaluated-alternatives)
9. [Sources & References](#9-sources--references)

---

## 1. Summary

Following Discord's February 2026 policy announcements — mandatory age verification, a surveillance-grade vendor pipeline connected to Palantir's ICE infrastructure, and confirmation of DHS subpoenas targeting user accounts — many MilSim communities are evaluating whether Discord remains a viable platform for their operations.

This document assesses **Fluxer** (https://fluxer.app) as the strongest available alternative for MilSim and tactical gaming communities. It covers what Fluxer is, why its specific characteristics are well-suited to this use case, what the genuine limitations are, and what the transition path looks like for communities with existing bot infrastructure.

**The recommendation:** For communities prioritizing jurisdictional protection, operational continuity, and minimal transition friction, the hosted **fluxer.app** instance is the strongest available option today. Communities with more advanced self-hosting capability and infrastructure resources can also evaluate running their own instance, with the tradeoffs documented in Section 5.

---

## 2. What Is Fluxer

Fluxer is a free and open source instant messaging and VoIP platform (AGPLv3 licensed) built by Hampus Kraft, a 22-year-old Swedish computer engineering student at KTH Royal Institute of Technology in Stockholm.

**Company:** Fluxer Platform AB — a Swedish limited liability company (org. no. 559537-3993), registered and publicly verifiable in Sweden's corporate database. This is not an anonymous project.

**Developer background:** Hampus has been building Fluxer since 2020. He has a documented history as a Discord bug hunter, has reported and received bounties for security vulnerabilities in Discord itself, and led web infrastructure for a Minecraft server with 6 million registered players. His KTH thesis focused on distributed systems and was published in September 2025.

**Timeline:** Public beta launched January 2026. Following Discord's age verification announcement on February 9, 2026, approximately 1,000 lifetime "Visionary" supporter licenses sold at $299 each before being paused — generating roughly $300,000 in early funding for a solo developer. This materially improves the project's sustainability outlook.

**License:** AGPLv3 — the strongest copyleft license available. Any modifications to the software, even when served over a network, must be open-sourced. This prevents a proprietary fork from ever taking the project closed. For communities that care about the long-term availability of their platform, this is a significant structural guarantee.

---

## 3. Why Fluxer Fits MilSim Communities

### Legal Jurisdiction — The Most Important Structural Difference

Fluxer Platform AB is a **Swedish company operating under EU law and GDPR**. This is the single most important structural difference from Discord and every other US-based platform evaluated.

The DHS administrative subpoenas documented in the companion Discord Threat Assessment — the ones demanding member data with no judicial oversight — **cannot be served to a Swedish company**. US law enforcement would need to go through EU-US Data Privacy Framework and MLAT (Mutual Legal Assistance Treaty) processes. These are slow, require judicial oversight on both sides, are politically complicated in the current environment, and are publicly visible.

For communities whose members include veterans, active-duty personnel, reservists, law enforcement, defense contractors, or cleared professionals, this jurisdictional difference is not abstract. Discord's subpoena vulnerability is a live threat. Fluxer's Swedish incorporation is a structural protection.

### No Age Verification — No Surveillance Pipeline

Fluxer has no mandatory age verification, no facial scan infrastructure, no identity vendor relationship with Palantir-adjacent investors, and no connection to ICE's targeting infrastructure.

For a MilSim community that already self-enforces age requirements through its own vetting process, Fluxer's approach is simply correct: the platform trusts your community to manage its own membership, as Discord always should have.

### No Adverse Media Screening of Your Members

When Discord users went through Persona's age verification, they were subjected to 269 distinct checks including facial recognition against watchlists and adverse media screening across 14 categories including terrorism and espionage — without their knowledge.

Fluxer performs none of this. Your members join by creating an account. The platform is not running KYC/AML screening on the people discussing tactical scenarios in your channels.

### Discord-Compatible Feature Set

Fluxer is the closest feature-complete Discord alternative currently available. Members will recognize channels, categories, roles, DMs, voice, reactions, and custom emoji. For a community that has invested in training members on Discord's interface, the transition friction is minimal.

**Current feature set:**
- Real-time messaging with typing indicators, reactions, and threaded replies
- Voice and video calls with screen sharing (powered by LiveKit)
- Text and voice channels organized into categories with granular permissions
- Custom emojis and stickers per community
- Rich media: link previews, image/video attachments, GIF search
- Full-text search
- Moderation tooling: roles, audit logs, moderation actions
- Web client + desktop apps + PWA for mobile (native mobile in active development)
- Bot API compatible with Discord's `@discordjs/core` library

For MilSim communities specifically, the channel organization model — nested categories, granular role-based permissions, separate voice channels per element — maps cleanly to how units are already structured on Discord. Your S1 channel, your OpsCenter, your platoon voice channels, your recruit processing pipeline all translate directly.

### Open Source and Auditable

The entire Fluxer codebase is public at https://github.com/fluxerapp/fluxer. The company is publicly registered. The developer is publicly identified. A community with technically capable members can read the code, audit it, and make informed assessments. This is categorically different from closed-source platforms where you are trusting marketing copy.

### Business Model Alignment

No advertising. No data selling. No venture capital with government surveillance entanglements. Revenue comes from optional Plutonium subscriptions on the hosted instance. Fluxer has committed in writing to never paywalling self-hosted features or requiring license key checks.

---

## 4. Honest Concerns

These are presented transparently so leadership can weigh them accurately. None are assessed as dealbreakers for MilSim communities, but each has operational implications.

### Single Developer — Bus Factor

Hampus is currently the primary developer. This is a real risk for any community that depends on the platform operationally.

Mitigating factors:
- AGPLv3 means the code cannot disappear or go closed — a community fork is always possible and already technically feasible
- The February 2026 funding surge (~$300k from Visionary sales) has brought new contributors and financial runway
- Federation features are in active development, which will bring more community investment
- Using the **hosted** fluxer.app instance means community continuity does not depend on the community maintaining server infrastructure

### No Default End-to-End Encryption

Fluxer is not end-to-end encrypted by default. The roadmap includes opt-in "secret chats" — ephemeral, fully E2EE sessions where nothing is stored in the database — but this is not yet shipped.

**What this means for MilSim operations:**

Channel messages and DMs are encrypted in transit (TLS) and at rest on Fluxer's servers in Sweden under GDPR. Fluxer staff could theoretically read messages. This is the same trust model as Discord, Slack, and every other non-E2EE platform — the difference is that the servers are in Sweden, not the United States, and subject to GDPR rather than CLOUD Act jurisdiction.

For routine operational coordination — training schedules, event planning, after-action reviews, recruitment processing — this is an acceptable trust model for most communities. For genuinely sensitive discussions, members should use **Signal**, exactly as they would with any non-E2EE platform.

Communities with members in sensitive positions should treat Fluxer as they would any unclassified coordination platform: appropriate for unclassified, routine, and community content; not appropriate for anything that would require a controlled channel in a professional context.

### Public Beta Status

Fluxer is in public beta. The February 9 influx of Discord users caused stability issues on the hosted instance. These are growing pains from unexpected scale, not structural failures. The platform is actively being refactored to handle the new load.

Communities should plan for occasional instability during the beta period and maintain a fallback communication channel (Signal group, email list) for continuity during outages.

### No Native Mobile App Yet

Mobile access is currently a PWA (progressive web app). It works but lacks the integration depth of a native app — no push notification reliability equivalent to native, no CallKit integration for voice on iOS. Native iOS and Android apps are the developer's stated first priority, with Flutter developers already engaged. Timeline is unclear but actively in motion.

For communities where members primarily coordinate from desktop during gaming sessions, this limitation is minor. For members who need reliable mobile push notifications for alerts, the PWA limitation is worth noting.

---

## 5. Hosted vs. Self-Hosted

Fluxer can be used either as a hosted service at fluxer.app or self-hosted on community-owned infrastructure. The choice has meaningful operational tradeoffs.

### Using the Hosted fluxer.app Instance

**Advantages:**
- Features ship automatically — no update management burden on leadership
- Fluxer Platform AB is the data controller — GDPR compliance and data subject rights are their operational responsibility
- Swedish legal jurisdiction protections apply fully
- Voice (LiveKit) works without special network configuration — no open UDP ports required
- Zero infrastructure overhead for the chat platform itself
- Members' optional Plutonium subscriptions fund Fluxer's development directly

**Tradeoffs:**
- Community data is on Fluxer's servers — you are trusting a third party, albeit a Swedish one under GDPR
- No control over the hosting environment
- Subject to Fluxer's terms of service and content policies

### Self-Hosting

**Advantages:**
- Complete data sovereignty — your infrastructure, your jurisdiction (or your chosen jurisdiction)
- Full control over the platform environment, backups, and update cadence
- No dependence on Fluxer AB's operational continuity for data access

**Tradeoffs:**
- Voice (LiveKit) requires open UDP ports — Cloudflare Tunnel and similar reverse proxies cannot proxy UDP, requiring a separate public IP or port forwarding configuration
- Self-hosting documentation is still maturing; a backend refactor is in progress
- Your community becomes the data controller — GDPR compliance becomes your operational burden if you have EU members
- Requires hardware, maintenance, and technical expertise to operate reliably

**Recommendation for most MilSim communities:** Start with the hosted instance. Self-hosting is viable for communities with existing server infrastructure and technical leadership, but the voice networking requirements are a meaningful barrier that the hosted instance resolves automatically.

---

## 6. Bot Infrastructure — Keeping Your Automation

Bot infrastructure is a meaningful operational concern for MilSim communities. Many units have invested in custom Discord bots for scheduling, attendance tracking, roster management, promotion tracking, and event coordination. The ability to preserve this investment matters.

### Why Existing Bot Code Is Largely Portable

Fluxer's API is **intentionally compatible with Discord's API**, using the same Gateway protocol, REST patterns, and event model — pointed at `https://api.fluxer.app` instead of Discord's endpoints.

This means Discord bot code can in many cases be adapted to work with Fluxer with relatively modest changes — primarily base URL overrides and token replacement. The migration path is not trivial, but it is not a complete rewrite either.

### Bot Libraries and Compatibility

Discord bots written in the following libraries are viable starting points for Fluxer adaptation:

- **discord.py (Python)** — Customizable base URL via HTTP configuration; the dominant Python Discord library
- **discord.js / @discordjs/core (JavaScript/Node.js)** — The official Fluxer quickstart documentation demonstrates a bot using this library directly
- **interactions.py (Python)** — More modern, slash-command focused (note: slash commands not yet implemented on Fluxer — prefix commands like `!command` required for now)
- **hikari (Python)** — Async Python library with clean REST and Gateway separation

**Current limitation:** Fluxer has not yet implemented slash commands or the interactions system. Bots must use prefix-based commands (e.g., `!schedule`, `!attend`, `!roster`) rather than slash commands for now. Slash commands are on the Fluxer roadmap.

### Typical MilSim Bot Use Cases and Feasibility

| Bot Function | Feasibility on Fluxer | Notes |
|---|---|---|
| Scheduling / event creation | ✅ Viable | Message-based commands work fully |
| Attendance tracking | ✅ Viable | Reaction-based attendance works |
| Role assignment / rank tracking | ✅ Viable | Role API is compatible |
| Recruitment pipeline automation | ✅ Viable | Channel and permission management works |
| Welcome / onboarding messages | ✅ Viable | Member join events fire correctly |
| Slash command interfaces | ⚠️ Not yet | Use prefix commands in the interim |
| Integration with external systems | ✅ Viable | Outbound API calls from bot are unrestricted |

### Hosting Bot Infrastructure

Communities choosing to self-host their bots (recommended regardless of whether the chat platform is hosted or self-hosted) should note:

- Docker-based deployment is the cleanest approach for bot infrastructure isolation
- Bot tokens should be managed as secrets (Docker Secrets or equivalent), never in source code or environment files committed to version control
- Each bot should run as its own registered Application in Fluxer's developer settings
- Bots only need outbound network access to `api.fluxer.app` and `gateway.fluxer.app` — no inbound ports required

---

## 7. Platform Scorecard

| Requirement | Status | Notes |
|---|---|---|
| Outside US jurisdiction | ✅ Swedish company | MLAT required for US law enforcement access |
| Open source, auditable | ✅ AGPLv3 | Full codebase public on GitHub |
| No age verification / surveillance pipeline | ✅ | No Persona, no facial scan, no watchlist screening |
| No government entanglement | ✅ | No DoD/IC/DHS contracts or connections |
| No mandatory phone / ID collection | ✅ | Standard account registration only |
| Discord-like UX / minimal retraining | ✅ | Closest feature-complete alternative found |
| Voice and screen sharing | ✅ | LiveKit-powered; works on hosted instance |
| Bot API compatibility | ✅ | Discord-compatible; Python and JS viable |
| Channel/category/role structure | ✅ | Full support; maps to unit organization |
| Open source self-hosting option | ✅ | Full self-host supported |
| E2EE for channels | ⚠️ Not yet | Opt-in secret chats planned; use Signal for sensitive comms |
| Slash commands | ⚠️ Not yet | Prefix commands work; slash commands on roadmap |
| Native mobile app | ⚠️ In progress | PWA works; native iOS/Android in development |
| Production stability | ⚠️ Beta | Growing pains from Discord exodus; improving |
| Single-developer risk | ⚠️ Mitigated | AGPLv3 + new funding + contributors |
| Voice without port forwarding (hosted) | ✅ | LiveKit managed by Fluxer on hosted instance |
| Voice without port forwarding (self-hosted) | ❌ Requires config | Open UDP ports or direct IP required for LiveKit |

---

## 8. Evaluated Alternatives

The following platforms were evaluated and rejected before Fluxer was identified as the recommendation.

| Platform | Rejection Reason |
|---|---|
| **Matrix / Synapse** | Federation replicates all content — including content removed for policy violations — to any federated server. This creates unacceptable risk for community-moderated spaces and cannot be mitigated without going non-federated, at which point the federation benefit disappears. |
| **Rocket.Chat** | Active marketing to DoD, DHS, and intelligence community. Mandatory workspace registration leaks organizational metadata. Government sector positioning is incompatible with the jurisdictional protection goals of this assessment. |
| **Revolt / Stoat** | E2EE not yet implemented. Significant instability under load. Development pace insufficient relative to feature requirements. |
| **TeamSpeak 6** | Voice-only platform. Reliable for voice coordination but lacks text community, channel structure, role management, and bot ecosystem required for full unit operations. Screen sharing unreliable on self-hosted instances. |
| **Mumble** | Voice-only. No text community features. Requires self-hosted server. Better voice codec than TeamSpeak but same fundamental limitation. |
| **Guilded** | US-based, owned by Roblox Corporation. Calendar and scheduling features are strong, but US jurisdiction means the same DHS subpoena exposure as Discord. |

---

## 9. Sources & References

- Fluxer application: https://fluxer.app
- Fluxer source code: https://github.com/fluxerapp/fluxer
- Fluxer developer blog — How I built Fluxer: https://blog.fluxer.app/how-i-built-fluxer-a-discord-like-chat-app/
- Fluxer 2026 Roadmap: https://blog.fluxer.app/roadmap-2026/
- Fluxer bot quickstart: https://docs.fluxer.app/quickstart
- Fluxer Platform AB (Swedish corporate registry): https://www.allabolag.se/foretag/fluxer-platform-ab/brandbergen/datacenters/2KJCA7DI5YDLG
- Fluxer privacy policy: https://fluxer.app/privacy
- Fluxer community guidelines: https://fluxer.app/guidelines
- Discord Threat Assessment (MilSim Edition): discord-threat-assessment-milsim.md
