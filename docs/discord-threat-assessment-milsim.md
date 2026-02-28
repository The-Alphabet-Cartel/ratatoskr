# Discord Threat Assessment
## MilSim & Tactical Gaming Community Edition

============================================================================
Platform Risk Briefing for Military Simulation and Tactical Gaming Communities
Based on documented developments through February 25, 2026
============================================================================

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Mandatory Age Verification](#2-mandatory-age-verification)
3. [The Persona Exposure — A Surveillance Stack Hiding in Plain Sight](#3-the-persona-exposure--a-surveillance-stack-hiding-in-plain-sight)
4. [The 2025 Data Breach](#4-the-2025-data-breach)
5. [The Palantir / ICE Connection](#5-the-palantir--ice-connection)
6. [DHS Subpoenas — Discord Named](#6-dhs-subpoenas--discord-named)
7. [Discord's Response — Delay, Not Reversal](#7-discords-response--delay-not-reversal)
8. [Why MilSim Communities Face Specific Exposure](#8-why-milsim-communities-face-specific-exposure)
9. [Summary: The Threat Model](#9-summary-the-threat-model)
10. [Sources](#10-sources)

---

## 1. Purpose

This document summarizes concrete, documented threats that Discord's recent policy changes and government entanglements pose to military simulation and tactical gaming communities — specifically those built around games like ARMA 3, Squad, DCS World, and similar titles.

MilSim communities have a distinct profile that creates specific exposure risks that general gaming communities may not share. This document is intended for community leadership evaluating their platform risk, and for members who want to understand what has changed and why it matters to them specifically.

These are not hypothetical risks. Every threat described below is active, documented, and has developed over the course of February 2026. The situation has materially worsened in the past two weeks.

---

## 2. Mandatory Age Verification

### What Was Announced

In early February 2026, Discord announced that all users would be placed into a "teen-appropriate experience" by default. To escape restrictions — content filtering, limited DMs, no Stage channel access — flagged users would need to submit either a **facial scan** or a **government-issued photo ID** through a third-party verification vendor.

### The March Rollout Is Delayed — Not Cancelled

Following widespread backlash, Discord's co-founder and CTO Stanislav Vishnevskiy published a blog post on February 24, 2026 acknowledging that Discord had "missed the mark" and announcing a delay of the global rollout to the **second half of 2026**. Discord claims approximately 90% of users will not need to verify their age, as the platform's internal signals — account age, payment method on file, server membership patterns — can determine most adult users automatically.

What Discord did not do: reverse the policy. The age verification rollout is still coming. The delay is a response to public pressure, not a change of direction.

### The MilSim Irony

Most MilSim communities already self-enforce age requirements. ARMA 3 units typically require applicants to be 18+, often older, and put new recruits through vetting processes that would embarrass some HR departments. You have already solved the problem Discord claims to be solving — without collecting biometric data from your members.

Now Discord wants to collect government ID from the adults in your community anyway, on its own terms, through a vendor pipeline you have no visibility into, and store that data on servers subject to US government data requests.

The age verification system offers your community nothing it doesn't already have. The surveillance exposure it creates is entirely new.

---

## 3. The Persona Exposure — A Surveillance Stack Hiding in Plain Sight

This is the most significant development of February 2026 and warrants detailed attention from a community with an existing OPSEC culture.

### What Was Found

Security researchers discovered that the frontend code for **Persona Identities, Inc.** — Discord's age verification vendor for a UK test — was **publicly accessible on the open internet**. Approximately **2,456 files** were found sitting on a US government-authorized server endpoint, specifically a **FedRAMP-authorized** (Federal Risk and Authorization Management Program) domain.

The exposure was reported independently by researcher "Celeste" (X: @vmfunc), covered by Malwarebytes, IBTimes UK, and Fortune, and confirmed before the files were removed.

### What the Exposed Code Revealed

Persona is not an age-checking tool. The exposed files showed it is a comprehensive **Know Your Customer (KYC) and Anti-Money Laundering (AML) surveillance platform** performing, among other things:

- **269 distinct verification checks** on each user submitted
- **Facial recognition against watchlists** and lists of politically exposed persons (PEPs)
- **Adverse media screening** across 14 categories, including **terrorism** and **espionage**
- **Risk and similarity scoring** on submitted identities
- Selfie analytics including suspicious-entity detection, pose repeat detection, and age inconsistency flags
- **Data retention of up to three years** for IP addresses, browser fingerprints, device fingerprints, government ID numbers, phone numbers, names, and faces

For a MilSim community, the words **terrorism** and **espionage** in that screening list are worth pausing on. Members discussing weapons systems, unit tactics, historical military operations, or geopolitical scenarios — entirely normal MilSim conversation — may register differently when run through an AML/KYC surveillance system built to screen for national security risk profiles.

Discord had told users that biometric data would not leave their device. UK users discovered a deleted disclaimer stating that their data would in fact leave their device and be stored for up to seven days. The Persona files indicated retention periods of **up to three years**.

### The FedRAMP Endpoint

FedRAMP is a US government program that authorizes cloud services for federal agency use. Persona's CEO Allen Song confirmed in an interview with Fortune that Persona is actively pursuing FedRAMP authorization — building the compliance infrastructure to sell identity verification services directly to federal agencies.

An independent investigation by The Rage (a financial surveillance publication) identified a domain — `withpersona-gov.com` — that may query identity verification requests connected to an OpenAI government database. Persona's leadership denied any current partnership with agencies including ICE or DHS. The presence of the code on a FedRAMP endpoint describes a company actively building toward that relationship.

### Discord Ends Persona Partnership

Facing this exposure, Discord confirmed it ended its "limited test" of Persona. Both companies state the relationship lasted less than a month and involved a small test group in the UK. Discord's CTO described Persona as failing to meet the platform's privacy bar.

That is better than nothing. It does not change what the exposed code revealed about what Persona's system was doing to the users who went through it, and it does not address who Discord will use instead.

---

## 4. The 2025 Data Breach

In late 2024/early 2025, Discord disclosed that attackers accessed a third-party vendor's systems used for age-related appeals, exposing approximately **70,000 users' government-issued ID photos** and associated sensitive personal data. Discord won the Electronic Frontier Foundation's 2025 "We Still Told You So" Breachies Award for this incident.

Discord has since switched to different vendors and states it no longer routes ID uploads through general support infrastructure.

The breach matters here for a straightforward reason: Discord has already demonstrated that the class of data it now wants to collect from your members — government IDs, biometric data — can be compromised through vendor relationships. The current rollout creates the same risk through a new vendor pipeline, with the same reassurances from the same company.

---

## 5. The Palantir / ICE Connection

### The Investment Chain

Persona is backed by **Founders Fund**, the venture capital firm run by **Peter Thiel**. Thiel is also the co-founder and a major stakeholder in **Palantir Technologies** — the data analytics company whose systems form the operational backbone of US Immigration and Customs Enforcement's surveillance and targeting infrastructure.

This is not guilt by association. It is a documented financial relationship between:

```
Discord age verification data
    → Persona (identity vendor)
        → Founders Fund (major investor in both Persona and Palantir)
            → Palantir
                → ImmigrationOS / ELITE (active federal targeting infrastructure)
```

### ImmigrationOS — The Surveillance Platform

In April 2025, ICE awarded Palantir a **$30 million sole-source contract** to build **ImmigrationOS** — an integrated AI-driven surveillance platform for immigration enforcement, with the contract running through September 2027.

The system pulls data from across federal databases: passport records, Social Security files, IRS tax data, Medicaid records, DMV files, utility bills, court records, and license-plate reader data. ICE is simultaneously pursuing social media monitoring contracts with companies including Clearview AI and ShadowDragon.

### ELITE — The Targeting Tool

**ELITE** (Enhanced Leads Identification & Targeting for Enforcement) is a Palantir application ICE agents use in the field. Per its own documentation, it functions like Google Maps populated with people instead of restaurants. Agents draw shapes on a map to select "target-rich areas" for enforcement operations. Each person in the system has a dossier with their photo, address, and a **confidence score** predicting their current location — derived in part from Medicaid address updates and routine government data submissions.

Palantir has received more than **$900 million in federal contracts** since Trump took office.

### Why This Matters for MilSim Specifically

The direct Persona → Palantir investor chain is the reason the identity data your members submit for age verification doesn't stay neatly in a "teen safety" box. It enters an ecosystem where the financial backers are simultaneously building the government's deportation and surveillance infrastructure. That ecosystem now has FedRAMP authorization ambitions.

Members with security clearances, federal employment, or sensitive professional backgrounds have particular reason to care about where their identity data flows and what screening it triggers.

---

## 6. DHS Subpoenas — Discord Named

Multiple reports confirm that Google, Meta, Reddit, and Discord have received **hundreds of administrative subpoenas** from the Department of Homeland Security demanding identifying information about accounts that criticized ICE, reported ICE agent locations, or tracked immigration enforcement activity.

**Administrative subpoenas require no judicial approval.** DHS issues them directly. They were previously used primarily for serious criminal investigations — child trafficking, terrorism. They are now being used against people posting political commentary and neighborhood watch alerts about immigration enforcement.

At least three of the four platforms — Google, Meta, and Reddit — have complied with some of these requests, per reporting from IBTimes and PC Gamer. Discord has declined to publicly comment on whether it has complied.

### Why MilSim Communities Are in the Frame

MilSim communities are not apolitical. Discussions of military tactics, government policy, foreign policy, weapons systems, and geopolitical scenarios are intrinsic to the hobby. Members frequently have strong, publicly expressed views on defense policy, the role of military force, immigration enforcement, and civil liberties.

Beyond that, the technical profile of MilSim server membership — coordinated group activity, use of military terminology, tactical communication patterns — could read differently to an automated surveillance system than the same behavioral patterns in a general gaming community.

More concretely: **if any member of your community has posted criticism of federal enforcement activity on Discord, that account's metadata is potentially accessible to DHS via administrative subpoena without a warrant, without a judge, and without Discord being legally required to notify the user.**

---

## 7. Discord's Response — Delay, Not Reversal

Discord's CTO Stanislav Vishnevskiy published a blog post on February 24, 2026 outlining these commitments:

- Global age verification rollout delayed to **second half of 2026**
- Persona partnership ended ("did not meet that bar")
- Vendor transparency: Discord will publish a list of verification vendors
- Additional verification options in development: credit card verification, on-device facial estimation
- Approximately 90% of users will not be required to verify

Vishnevskiy wrote: *"Many of you are worried that this is just another big tech company finding new ways to collect your personal data. That we're creating a problem to justify invasive solutions. I get that skepticism. It's earned, not just toward us, but toward the entire tech industry. But that's not what we're doing."*

The acknowledgment that the skepticism is earned is accurate. The reassurance that Discord is an exception to it is not something the available evidence supports. A platform that:

- Built a biometric identity pipeline before being legally required to
- Used a vendor (Persona) conducting 269 surveillance checks without disclosing this to users
- Allowed a vendor breach that exposed 70,000 users' government IDs
- Deleted a privacy disclaimer it had published
- Has not publicly addressed compliance with DHS subpoenas

...is asking for trust it has not demonstrated it has earned. The delay changes the timeline. It does not change the structural situation.

---

## 8. Why MilSim Communities Face Specific Exposure

The preceding sections apply to all Discord users. This section addresses the profile specific to MilSim and tactical gaming communities.

### Security Clearances and Federal Employment

MilSim communities disproportionately attract veterans, active-duty service members, reservists, law enforcement, defense contractors, and intelligence community professionals. Many of these members hold or have held **security clearances**.

A security clearance investigation looks at foreign contacts, financial history, personal conduct, and associations. Members in this category have career-ending reasons to be careful about where their biometric data and government ID end up, what those documents get screened against, and whether any flags are generated — even false positive flags — in a surveillance system they cannot audit, correct, or appeal.

Persona's exposed code showed the system runs **watchlist screening** and generates **risk scores**. A false positive flag in a system like this, tied to your real name and government ID, is not something you'd know about or have any ability to contest.

### The Adverse Media Screening Problem

Persona screens submitted identities against "adverse media" across 14 categories. MilSim communities produce and consume content that — out of context — sits in uncomfortable proximity to some of those categories. Discussion of weapons systems, historical atrocities, tactical assault scenarios, government surveillance programs, foreign military operations, and similar topics is entirely routine in ARMA 3 communities and entirely normal in context.

Run through an automated AML/KYC adverse media screening system built to flag financial crime and national security risk, that same content profile looks different. Members who have written publicly about these topics under their own names — on Discord, on forums, on Reddit — may generate flags they are completely unaware of.

### OPSEC Culture Should Inform This Decision

MilSim communities already operate with more operational security awareness than most gaming communities. The instinct to control who has what information about your members, to compartmentalize sensitive discussions, and to vet access to community spaces is already present. Applying that same discipline to the platform question is consistent with the community's existing values, not a departure from them.

The question to ask is the same one you'd ask about any information system: **Who has access to what? Where does it go? Who can compel its disclosure? What are the consequences of a breach?**

On Discord, the answers are: potentially DHS (via administrative subpoena), Persona's vendor ecosystem (via the age verification pipeline), and any future breach victim (via the demonstrated vulnerability of the vendor chain) — with no notification requirement to your members and no meaningful ability to contest or correct what's in those systems.

### Age-Gated Content and Server Restrictions

MilSim communities frequently discuss graphic historical content, real-world weapons systems, and mature tactical scenarios. Channels containing this content may be subject to Discord's age-restricted channel system — meaning members would need to verify their age to access them.

Your community already enforces age requirements through your own vetting process. Discord's system bypasses your vetting entirely and inserts its own vendor pipeline between your members and your community spaces, on terms you don't control.

---

## 9. Summary: The Threat Model

| Threat | Status | MilSim-Specific Impact |
|--------|--------|----------------------|
| Age verification rollout delayed to H2 2026 (not cancelled) | 🔴 Delayed, still coming | Adult MilSim members will face ID/biometric submission to access age-gated content |
| Persona conducted 269 surveillance checks including watchlist + adverse media screening | 🔴 Confirmed via code exposure | Military/tactical content profiles may generate false flags in KYC/AML systems |
| Persona code sat on FedRAMP-authorized US government endpoint | 🔴 Confirmed | Identity data pipeline has structural connection to federal infrastructure |
| 2025 breach of 70,000 users' government IDs | 🔴 Occurred | Clearance holders and federal employees at specific career risk from ID exposure |
| Persona funded by Founders Fund (Peter Thiel / Palantir investors) | 🔴 Confirmed | Financial chain links identity data to ICE surveillance infrastructure |
| Palantir ImmigrationOS: $30M ICE targeting platform, active through 2027 | 🔴 Active | Palantir ecosystem now explicitly weaponized for government targeting operations |
| Palantir ELITE: real-time location targeting used by ICE agents in the field | 🔴 Active | Same investment ecosystem building tools used to locate and arrest people |
| DHS subpoenas targeting political speech on Discord | 🔴 Active | MilSim policy discussion and community content potentially within scope |
| Discord non-disclosure of DHS subpoena compliance | 🟡 Unconfirmed | Members cannot know whether their data has been disclosed to government |
| Discord's response: delay and rebranding, not structural reversal | 🟡 Ongoing | Timeline extended; underlying platform direction unchanged |

### The Bottom Line for MilSim Communities

Discord built a surveillance-grade identity pipeline into a platform your community uses for coordinated tactical gaming. The pipeline connects — through investment relationships and FedRAMP infrastructure — to systems being used for government enforcement operations. The platform has responded to public backlash by delaying the rollout and dropping the most obviously problematic vendor, while keeping the policy intact and declining to address government data requests.

The age verification delay gives communities time to evaluate alternatives without a hard March deadline. It does not change the direction Discord is moving, and it does not address the DHS subpoena exposure that exists right now, today, for any member who has expressed political views on the platform.

For a community with members who hold security clearances, have federal employment, or operate with an existing awareness of information security, the right time to make a platform decision is before the identity collection infrastructure goes live — not after.

---

## 10. Sources

- [Discord Voluntarily Pushes Mandatory Age Verification Despite Recent Data Breach](https://www.eff.org/deeplinks/2026/02/discord-voluntarily-pushes-mandatory-age-verification-despite-recent-data-breach) — Electronic Frontier Foundation, February 12, 2026
- [Age verification vendor Persona left frontend exposed, researchers say](https://www.malwarebytes.com/blog/news/2026/02/age-verification-vendor-persona-left-frontend-exposed) — Malwarebytes, February 20, 2026
- [Hackers Expose Discord Age Verification System Issue After Persona Frontend Code Left Wide Open](https://www.ibtimes.co.uk/discord-age-verification-security-breach-1780591) — IBTimes UK, February 20, 2026
- [Discord distances itself from Peter Thiel–backed verification software after its code was found on a U.S. government server](https://fortune.com/2026/02/24/discord-peter-thiel-backed-persona-identity-verification-breach/) — Fortune, February 24, 2026
- [Discord delays its global age verification after upsetting almost everyone on Earth: 'We've made mistakes'](https://www.pcgamer.com/software/platforms/discord-delays-its-global-age-verification-rollout-and-cuts-ties-with-peter-thiel-backed-verification-vendor-after-upsetting-almost-everyone-on-earth-weve-made-mistakes/) — PC Gamer, February 24, 2026
- [Discord delays global rollout of age verification after backlash](https://techcrunch.com/2026/02/24/discord-delays-global-rollout-of-age-verification-after-backlash/) — TechCrunch, February 24, 2026
- [Discord Severs Persona Links After Peter Thiel-Backed Verification Software's US Surveillance Ties Are Revealed](https://www.ibtimes.co.uk/discord-cuts-ties-persona-surveillance-concerns-1781345) — IBTimes UK, February 24, 2026
- [US Department of Homeland Security has reportedly demanded personal information about ICE's critics from Discord, Reddit, Google, and Meta](https://www.pcgamer.com/software/platforms/us-department-of-homeland-security-has-reportedly-demanded-personal-information-about-ices-critics-from-discord-reddit-google-and-meta-and-at-least-3-of-those-platforms-have-complied/) — PC Gamer, February 17, 2026
- [DHS Sends Subpoenas to Google, Meta, Reddit, and Discord to Identify Americans Who Criticize ICE](https://www.nytimes.com/2026/02/13/technology/dhs-anti-ice-social-media.html) — New York Times, February 13, 2026
- [ICE to Use ImmigrationOS by Palantir, a New AI System, to Track Immigrants' Movements](https://www.americanimmigrationcouncil.org/blog/ice-immigrationos-palantir-ai-track-immigrants/) — American Immigration Council, 2025
- [Palantir's ELITE App: "Kind of Like Google Maps" for Finding Deportation Targets](https://stateofsurveillance.org/news/palantir-elite-ice-targeting-app-confidence-scores-2026/) — State of Surveillance, January 2026
- [Discord faces backlash over age checks after data breach exposed 70,000 IDs](https://arstechnica.com/tech-policy/2026/02/discord-faces-backlash-over-age-checks-after-data-breach-exposed-70000-ids/) — Ars Technica, February 2026
