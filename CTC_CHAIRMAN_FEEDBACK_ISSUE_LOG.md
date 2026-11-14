# CTC Chairman Feedback Issue Log

## Purpose

Capture the Chairman's website feedback as a backlog for discussion and planning. This log records requests and open questions; it does not commit to implementation or establish feasibility.

**Tracking:** GitHub issues linked below are the source of truth for current status, decisions and implementation notes. The table preserves the original feedback and status at import on November 14, 2026; update ongoing progress in GitHub rather than maintaining duplicate status here. Owners, priorities (other than the recorded release blocker) and effort estimates still need triage.

**Launch context:** The Chairman hopes the site can go live for the next season in the New Year. The date, scope, and feasibility need to be confirmed.

**Import follow-up:** CONF-01 ([#3](https://github.com/DrProfPatPending/HLaS/issues/3)) and PUBLIC-01 ([#4](https://github.com/DrProfPatPending/HLaS/issues/4)) were already complete, but remain open in GitHub because an edit request was rejected with HTTP 403. Close those two as completed once edit access is available, or manually using an authorised account; the other fourteen items remain open for planning.

## Feedback

| ID / GitHub issue | Area | Feedback / requested outcome | Open questions for planning | Status at import |
|---|---|---|---|---|
| [CONF-01 / #3](https://github.com/DrProfPatPending/HLaS/issues/3) | Public pages | The three outward-facing mini-site pages are liked and approved to go public. The CTC configuration enables Home, About, and Contact. | None for the approval recorded here. Separate review observations are listed as PUBLIC-01 and PUBLIC-02. | Complete |
| [PUBLIC-01 / #4](https://github.com/DrProfPatPending/HLaS/issues/4) | Public mini-site / mobile | Make CTC's enabled Home, About and Contact pages usable on mobile. Shared implementation is tracked as **CORE-01** in the core issue log. | Deployed to CTC and checked in the browser at 375, 767, 768, 769 and 1024px; direct About access and mobile login form checked. User accepted the result. Physical-device testing was not performed. | Complete |
| [PUBLIC-02 / #5](https://github.com/DrProfPatPending/HLaS/issues/5) | Public mini-site / Home | Before release, correct the Home heading: it prepends “Welcome to:” to the configured headline, so the current heading reads “Welcome to: Cambridge Trout Club”. | Remove the fixed prefix or otherwise adjust the heading so configured headlines read naturally. | Pre-release |
| [NAV-01 / #6](https://github.com/DrProfPatPending/HLaS/issues/6) | Navigation / documents | Add a separate **CTC Documents** navigation tab, with the Club Rules, Catch & Release Guidelines, and CTC River Management Plan. | Are these documents already available in final form? Should this section be member-only, and who will maintain the documents? | Untriaged |
| [NAV-02 / #7](https://github.com/DrProfPatPending/HLaS/issues/7) | Navigation / club information | Move the information currently under **Club Information** into **CTC Home**. If that is not suitable, move Club Information to the second or third navigation position. | Confirm the preferred option and which information should appear on CTC Home. | Untriaged |
| [NAV-03 / #8](https://github.com/DrProfPatPending/HLaS/issues/8) | Committee details | Add the Chairman's mobile number to the Committee box. | Obtain the number and confirm consent, display audience, and preferred formatting before publishing. | Needs information |
| [NAV-04 / #9](https://github.com/DrProfPatPending/HLaS/issues/9) | Health and Safety | Move the Angling Trust Insurance Cover information to **CTC Home / Club Information**. | Confirm the destination based on the outcome of NAV-02 and whether the existing Health and Safety page should retain a link. | Untriaged |
| [MEM-01 / #10](https://github.com/DrProfPatPending/HLaS/issues/10) | Member Info | Add “(if under 18)” to the Date of Birth and Age labels. | Confirm exact label wording and whether it applies to both fields. | Untriaged |
| [BEAT-01 / #11](https://github.com/DrProfPatPending/HLaS/issues/11) | Beat Details / Fishing Beats | The two pages appear duplicative; combine them into one tab with the information. | Compare the content and functionality on both pages; decide which page/tab is retained and how members reach maps or beat details. | Untriaged |
| [BEAT-02 / #12](https://github.com/DrProfPatPending/HLaS/issues/12) | Beat details / C-Lower | After “can be a tough wade”, add: “, caution is to be taken as the riverbanks are steep for entry and exit and the riverbed very silty”. | Confirm the wording and exact location in the C-Lower description. | Untriaged |
| [CATCH-01 / #13](https://github.com/DrProfPatPending/HLaS/issues/13) | Catch Return | Add trout size categories: **Small Trout < 6 inches**, **Medium Trout 6–12 inches**, and **Large Trout > 12 inches** (or use millimetres). | Choose inches or millimetres and confirm the boundary convention, including how exactly 12 inches is classified. | Untriaged |
| [CATCH-02 / #14](https://github.com/DrProfPatPending/HLaS/issues/14) | Catch Return | Add a Comments box and make it optional. | Confirm whether there should be a length limit and whether comments are visible to administrators only or other members too. | Untriaged |
| [ADMIN-01 / #15](https://github.com/DrProfPatPending/HLaS/issues/15) | Membership Admin / CTC Members | Automatically copy information a member enters under Member Info into the CTC Members spreadsheet. | Identify the spreadsheet and fields, define which edits sync and in which direction, and check access/privacy and duplicate-record handling. | Untriaged |
| [ADMIN-02 / #16](https://github.com/DrProfPatPending/HLaS/issues/16) | Membership Admin / CTC Members | Add a Year of Joining column. Review whether the New Member and Age columns are needed; Age may only be useful for junior members. | Confirm how Year of Joining is determined, whether existing records can be populated, and whether Age should be removed or retained for juniors. | Untriaged |
| [FORM-01 / #17](https://github.com/DrProfPatPending/HLaS/issues/17) | Application forms / member records | Collect car registration number(s) on future application forms. The Chairman directed this request to Richard. | Confirm the form owner, number of vehicles allowed, how existing members can update details, and who may access the data. | Needs owner / requirements |
| [NOTICE-01 / #18](https://github.com/DrProfPatPending/HLaS/issues/18) | News and Notices | Consider a **Notices** or **News and Notices** tab. Publishing a notice should email every member, especially for urgent river closures or pollution. | Decide the section name, who can publish, recipient and consent rules, delivery method, urgent-notice workflow, and handling of failed or bounced emails. | Untriaged |

## Planning notes

- PUBLIC-02 was identified as a release blocker for the mini-site; track its resolution in [#5](https://github.com/DrProfPatPending/HLaS/issues/5).
- Resolve content, placement, and audience decisions before implementation, especially for navigation, documents, and the beat-page consolidation.
- Treat personal/contact and vehicle information changes as requiring an explicit data-access and consent review.
- Notice emails are an operational feature as well as a page: define ownership, delivery expectations, and an urgent alternative before committing to it.
- Assess the New Year launch target against the agreed scope after items have owners, priorities, and estimates.
