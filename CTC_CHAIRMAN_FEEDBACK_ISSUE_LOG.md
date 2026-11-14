# CTC Chairman Feedback Issue Log

## Purpose

Capture the Chairman's website feedback as a backlog for discussion and planning. This log records requests and open questions; it does not commit to implementation or establish feasibility.

**Tracking:** GitHub issues linked below are the source of truth for current status, decisions and implementation notes. The tables preserve feedback and status when recorded on November 14, 2026, including the historical beta feedback below; update ongoing progress in GitHub rather than maintaining duplicate status here. Owners, priorities (other than the recorded release blocker) and effort estimates still need triage.

**Launch context:** The Chairman hopes the site can go live for the next season in the New Year. The date, scope, and feasibility need to be confirmed.

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
| [NAV-05 / #19](https://github.com/DrProfPatPending/HLaS/issues/19) | Officers and Committee | Follow-up feedback: add a **Term expires** column to the CTC Officers and Committee table. Requested values: Rob and John — **AGM November 2026**; Richard — **AGM November 2027**; Charlie — **N/A**. | Confirm the mapping to existing rows/roles, whether the November 2026 values remain current at publication, values for any other rows, and who maintains the terms after future AGMs. Preserve the existing table audience unless otherwise agreed. | Untriaged |
| [MEM-01 / #10](https://github.com/DrProfPatPending/HLaS/issues/10) | Member Info | Add “(if under 18)” to the Date of Birth and Age labels. | Confirm exact label wording and whether it applies to both fields. | Untriaged |
| [BEAT-01 / #11](https://github.com/DrProfPatPending/HLaS/issues/11) | Beat Details / Fishing Beats | The two pages appear duplicative; combine them into one tab with the information. | Compare the content and functionality on both pages; decide which page/tab is retained and how members reach maps or beat details. | Untriaged |
| [BEAT-02 / #12](https://github.com/DrProfPatPending/HLaS/issues/12) | Beat details / C-Lower | After “can be a tough wade”, add: “, caution is to be taken as the riverbanks are steep for entry and exit and the riverbed very silty”. | Confirm the wording and exact location in the C-Lower description. | Untriaged |
| [CATCH-01 / #13](https://github.com/DrProfPatPending/HLaS/issues/13) | Catch Return | Add trout size categories: **Small Trout < 6 inches**, **Medium Trout 6–12 inches**, and **Large Trout > 12 inches** (or use millimetres). | Choose inches or millimetres and confirm the boundary convention, including how exactly 12 inches is classified. | Untriaged |
| [CATCH-02 / #14](https://github.com/DrProfPatPending/HLaS/issues/14) | Catch Return | Add a Comments box and make it optional. | Confirm whether there should be a length limit and whether comments are visible to administrators only or other members too. | Untriaged |
| [ADMIN-01 / #15](https://github.com/DrProfPatPending/HLaS/issues/15) | Membership Admin / CTC Members | Automatically copy information a member enters under Member Info into the CTC Members spreadsheet. | Identify the spreadsheet and fields, define which edits sync and in which direction, and check access/privacy and duplicate-record handling. | Untriaged |
| [ADMIN-02 / #16](https://github.com/DrProfPatPending/HLaS/issues/16) | Membership Admin / CTC Members | Add a Year of Joining column. Review whether the New Member and Age columns are needed; Age may only be useful for junior members. | Confirm how Year of Joining is determined, whether existing records can be populated, and whether Age should be removed or retained for juniors. | Untriaged |
| [FORM-01 / #17](https://github.com/DrProfPatPending/HLaS/issues/17) | Application forms / member records | Collect car registration number(s) on future application forms. The Chairman directed this request to Richard. | Confirm the form owner, number of vehicles allowed, how existing members can update details, and who may access the data. | Needs owner / requirements |
| [NOTICE-01 / #18](https://github.com/DrProfPatPending/HLaS/issues/18) | News and Notices | Consider a **Notices** or **News and Notices** tab. Publishing a notice should email every member, especially for urgent river closures or pollution. | Decide the section name, who can publish, recipient and consent rules, delivery method, urgent-notice workflow, and handling of failed or bounced emails. | Untriaged |

## Historical beta feedback

The user supplied this earlier beta feedback retrospectively on November 14,
2026; the original email date was not provided. Repeated requests are linked
to existing issues rather than duplicated. The email signature and contact
number are intentionally omitted.

### Additional historical items

| ID / GitHub issue | Area | Historical feedback / requested outcome | Evidence / remaining decisions | Status when recorded |
|---|---|---|---|---|
| [PUBLIC-03 / #20](https://github.com/DrProfPatPending/HLaS/issues/20) | Public Home heading | Correct the beta spelling **Cambridge Troout Club** to **Cambridge Trout Club**. | Current isolated CTC development settings contain the correctly spelled Home headline, which the page component renders. The separate colon/prefix request remains PUBLIC-02. | Complete; issue closed |
| [PUBLIC-04 / #21](https://github.com/DrProfPatPending/HLaS/issues/21) | Public Home introduction | Identify CTC as a small fly fishing club focused on maintaining the wild trout population and enjoying the river. | Current development Home copy includes **small fly-fishing club** and **maintaining the wild trout population**, rendered from configured content/description. | Complete; issue closed |
| [PUBLIC-05 / #22](https://github.com/DrProfPatPending/HLaS/issues/22) | Public About / Sustainability | Refer to protecting **the wild trout population and the River Cam** and maintaining **both** as a legacy. | Current development About fallback only refers to the River Cam. Confirm final wording/punctuation and whether to use CTC-specific content. | Untriaged |
| [PUBLIC-06 / #23](https://github.com/DrProfPatPending/HLaS/issues/23) | Public Contact introduction | Use wording along the lines of **Get in touch with the Cambridge Trout Club by contacting us at;**. | Current fallback omits the requested article/lead-in. Agree final wording and punctuation without publishing additional contact details. | Untriaged |
| [NAV-06 / #24](https://github.com/DrProfPatPending/HLaS/issues/24) | CTC Home / history | Use **Club History and General Information**, matching the document name; present an approved download or inline text, followed by News. | Choose document versus text, confirm approved content and ordering, and verify current member-facing content before changing it. | Untriaged |
| [NAV-07 / #25](https://github.com/DrProfPatPending/HLaS/issues/25) | Member navigation | Make **Health and Safety** a separate second navigation tab immediately after CTC Home. | Current app template places and routes the Health and Safety button in that position. Content/document requirements are tracked separately as NAV-08. | Complete; issue closed |
| [NAV-08 / #26](https://github.com/DrProfPatPending/HLaS/issues/26) | Health and Safety content | Show approved **Rule 7** text first, followed by two Health and Safety documents downloadable through Actions. | The scoped view exists, but approved Rule 7 text, document identity, ordering and download/access behaviour need verification. | Untriaged |
| [MEM-02 / #27](https://github.com/DrProfPatPending/HLaS/issues/27) | Member Info heading | Add **(all required)** to the **Field** heading. | Current member table still says Field. Confirm mandatory fields so optional values and adult DOB/Age are not mislabelled; coordinate with MEM-01. | Untriaged |
| [BEAT-03 / #28](https://github.com/DrProfPatPending/HLaS/issues/28) | Beat maps | The beta maps could be scrolled; consider making them fixed. | Clarify wheel zoom, dragging, page scrolling or fixed positioning. Existing Leaflet controls do not establish this ambiguous request as complete. | Needs clarification |
| [BEAT-04 / #29](https://github.com/DrProfPatPending/HLaS/issues/29) | A Beat description | Use wording such as **runs through the grounds of the Wellcome Genome Campus**. | The requested phrase is not present in current development A Beat descriptions. Confirm exact sentence and summary/detail placement. | Untriaged |
| [ADMIN-03 / #30](https://github.com/DrProfPatPending/HLaS/issues/30) | Membership Admin ordering | Show members alphabetically, ignoring resigned members or those on the holding list. | Current default sort is ID. Agree name ordering and whether inactive/holding members are excluded, grouped or optionally filtered; preserve records. | Needs clarification |
| [ADMIN-04 / #31](https://github.com/DrProfPatPending/HLaS/issues/31) | Membership Admin columns | Use **Email** instead of **E_Mail** and review removing one displayed column if Email and Username duplicate the same information. | Check configured labels and login-identifier semantics. Any display-column change must preserve authentication and stored account data. | Needs clarification |

### Earlier requests already tracked

Historical context was added to each corresponding GitHub issue, including
additional document inventory, interface coverage and differing alternatives.

| Beta request | Existing issue |
|---|---|
| Remove the Home heading colon / fixed prefix; spelling tracked separately above. | [PUBLIC-02 / #5](https://github.com/DrProfPatPending/HLaS/issues/5) |
| Separate CTC Documents / Club Documentation tab after Member Info; include Constitution, Club Rules, Catch & Release Guidelines, River Management Plan, Last AGM Minutes and approved documentation. Reconcile the proposed tab names. | [NAV-01 / #6](https://github.com/DrProfPatPending/HLaS/issues/6) |
| Move Club Information into CTC Home once documentation has its own tab. | [NAV-02 / #7](https://github.com/DrProfPatPending/HLaS/issues/7) |
| Add the Chairman's mobile number to club details, subject to consent and agreed audience. No number is reproduced here. | [NAV-03 / #8](https://github.com/DrProfPatPending/HLaS/issues/8) |
| Place Angling Trust information under CTC Home / Club Information. | [NAV-04 / #9](https://github.com/DrProfPatPending/HLaS/issues/9) |
| Add **(if under 18)** to DOB/Age in both Member Info and Membership Admin columns. | [MEM-01 / #10](https://github.com/DrProfPatPending/HLaS/issues/10) |
| Either separate maps-only **Beat Maps** and text **Beat Details**, or combine maps and details into **Beat Details**. Choose one arrangement. | [BEAT-01 / #11](https://github.com/DrProfPatPending/HLaS/issues/11) |
| Earlier request replaces **can be a tough wade** with **extreme caution is to be taken as the riverbanks are steep for entry and exit and the riverbed very silty**. The later request appends a caution instead; reconcile approved wording before editing. | [BEAT-02 / #12](https://github.com/DrProfPatPending/HLaS/issues/12) |
| Small/Medium/Large Trout size categories in inches or millimetres, with agreed boundaries. | [CATCH-01 / #13](https://github.com/DrProfPatPending/HLaS/issues/13) |
| Optional catch-return Comments box. | [CATCH-02 / #14](https://github.com/DrProfPatPending/HLaS/issues/14) |
| Member Info edits automatically reach the CTC Members spreadsheet/table; confirm the destination and synchronisation semantics. | [ADMIN-01 / #15](https://github.com/DrProfPatPending/HLaS/issues/15) |
| Add Year of Joining. | [ADMIN-02 / #16](https://github.com/DrProfPatPending/HLaS/issues/16) |
| Collect vehicle registration numbers on future application forms with agreed ownership/access. | [FORM-01 / #17](https://github.com/DrProfPatPending/HLaS/issues/17) |

### Verification limits

- Completed historical items above were verified in current development source
  and the restored CTC development settings, not by a fresh production review.
  Relevant sources are [Home](frontend/src/components/MiniSite/MiniSiteHome.vue)
  and [member navigation](frontend/App.vue).
- The public HTTPS check returned HTTP 401. No successful authenticated member
  session or live-production content parity was established by this import.
  Do not infer completion of Rule 7/document ordering, other data-only changes
  or unresolved requirements from the existence of a page or control.
- No application code, stored content, member records or deployment was changed.
  GitHub issues remain the source of truth as verification and decisions proceed.

## Planning notes

- PUBLIC-02 was identified as a release blocker for the mini-site; track its resolution in [#5](https://github.com/DrProfPatPending/HLaS/issues/5).
- Resolve content, placement, and audience decisions before implementation, especially for navigation, documents, and the beat-page consolidation.
- Treat personal/contact and vehicle information changes as requiring an explicit data-access and consent review.
- Notice emails are an operational feature as well as a page: define ownership, delivery expectations, and an urgent alternative before committing to it.
- Assess the New Year launch target against the agreed scope after items have owners, priorities, and estimates.
