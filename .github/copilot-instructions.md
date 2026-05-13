## Copilot Instructions Checklist
- [x] Verify that the copilot-instructions.md file in the .github directory is created.
- [x] Clarify Project Requirements
- [x] Scaffold the Project
- [x] Customize the Project
- [x] Install Required Extensions
- [x] Compile the Project
- [x] Create and Run Task
- [x] Launch the Project
- [x] Ensure Documentation is Complete

- [x] Launch the Project
	Verify that all previous steps have been completed.
	Prompt user for debug mode, launch only if confirmed.

- [x] Ensure Documentation is Complete
	Verify that all previous steps have been completed.
	Verify that `README.md` and this file contain current project information.
	Keep this file free of stale comment blocks.

## Last Documentation Update
May 2026 — updated for:
- **Caddyfile Configuration Management (May 13, 2026):**
  - Environment-specific Caddyfile configurations: `Caddyfile.prod` for production, `Caddyfile.dev` for development
  - Both files version-controlled in git; protected by explicit docker-compose volume mounts
  - Build script (`hlas_build.sh`) validates `Caddyfile.prod` exists before production deployment
  - Prevents accidental use of dev configuration in production during git rebases
  - New documentation: `CADDYFILE_CONFIGURATION.md` with troubleshooting and management guide
  - Updated `DEPLOYMENT.md` with environment configuration strategy
  - Updated `README.md` with SSL/TLS configuration notes
- Beat Details Waypoints: ordered route polyline from waypoints, GPX import, waypoint toggle button
- Removed old boundary polyline (downstream→pools→upstream) from map
- New `waypoints` JSONB column in `club_beats` (migration 20260511_0001)
- MiniSite UI refinements: Compact page headers (100px), 14pt font sizes
- Club background images: PostgreSQL storage with admin upload capability
- Navigation logo expansion (100px height)
- Background image display on Home page with responsive styling
- Consistent styling across all MiniSite pages
- April 2026 updates: Mobile responsive navigation, Beat Details restructure, responsive table styling
- Frontend dependency upgrades: vue 3.5.33, vuetify 4.0.6, vite 8.0.10, axios 1.15.2
- npm audit security fix: follow-redirects (GHSA-r4q5-vmmm-2653) resolved

## Deployment & Configuration Architecture

### Branch Strategy
- **`main` branch**: Development and testing environment
  - Uses `Caddyfile.dev` (localhost with internal TLS)
  - Local testing via docker-compose.dev.yml override
  - Safe for experimental changes

- **`production` branch**: Live VPS deployment
  - Uses `Caddyfile.prod` (cambridgetroutclub.org with Let's Encrypt)
  - Deployed via hlas_build.sh on VPS
  - Only receives thoroughly tested, merged changes

### Caddyfile Configuration (CRITICAL)
**File Structure:**
```
deploy/caddy/
  ├── Caddyfile          (main branch default, synced with Caddyfile.dev)
  ├── Caddyfile.dev      (development: hlastest + internal TLS)
  └── Caddyfile.prod     (production: cambridgetroutclub.org + Let's Encrypt)
```

**Docker Compose Integration:**
- `docker-compose.prod.yml` mounts: `./deploy/caddy/Caddyfile.prod:/etc/caddy/Caddyfile:ro`
- `docker-compose.dev.yml` override mounts: `./deploy/caddy/Caddyfile.dev:/etc/caddy/Caddyfile:ro`

**Build Safety:**
- `hlas_build.sh` validates `Caddyfile.prod` exists before VPS deployment
- Prevents accidental use of dev config in production

### Deployment Process
1. Develop/test on `main` branch
2. Merge thoroughly-tested changes to `production` branch
3. Run `./hlas_build.sh` on VPS (pulls production, validates config, rebuilds)
4. Caddy automatically uses correct TLS config via explicit volume mount

**Key Point:** Both Caddyfile files are version-controlled in git and protected from git rebases by explicit docker-compose volume mount paths.

**See:** CADDYFILE_CONFIGURATION.md for detailed troubleshooting and management

## Execution Guidelines
PROGRESS TRACKING:
- If any tools are available to manage the above todo list, use it to track progress through this checklist.
- After completing each step, mark it complete and add a summary.
- Read current todo list status before starting each new step.

COMMUNICATION RULES:
- Avoid verbose explanations or printing full command outputs.
- If a step is skipped, state that briefly (e.g. "No extensions needed").
- Do not explain project structure unless asked.
- Keep explanations concise and focused.

DEVELOPMENT RULES:
- Use '.' as the working directory unless user specifies otherwise.
- Avoid adding media or external links unless explicitly requested.
- Use placeholders only with a note that they should be replaced.
- Use VS Code API tool only for VS Code extension projects.
- Once the project is created, it is already opened in Visual Studio Code—do not suggest commands to open this project in Visual Studio again.
- If the project setup information has additional rules, follow them strictly.

FOLDER CREATION RULES:
- Always use the current directory as the project root.
- If you are running any terminal commands, use the '.' argument to ensure that the current working directory is used ALWAYS.
- Do not create a new folder unless the user explicitly requests it besides a .vscode folder for a tasks.json file.
- If any of the scaffolding commands mention that the folder name is not correct, let the user know to create a new folder with the correct name and then reopen it again in vscode.

EXTENSION INSTALLATION RULES:
- Only install extension specified by the get_project_setup_info tool. DO NOT INSTALL any other extensions.

PROJECT CONTENT RULES:
- If the user has not specified project details, assume they want a "Hello World" project as a starting point.
- Avoid adding links of any type (URLs, files, folders, etc.) or integrations that are not explicitly required.
- Avoid generating images, videos, or any other media files unless explicitly requested.
- If you need to use any media assets as placeholders, let the user know that these are placeholders and should be replaced with the actual assets later.
- Ensure all generated components serve a clear purpose within the user's requested workflow.
- If a feature is assumed but not confirmed, prompt the user for clarification before including it.
- If you are working on a VS Code extension, use the VS Code API tool with a query to find relevant VS Code API references and samples related to that query.

TASK COMPLETION RULES:
- Your task is complete when:
  - Project is successfully scaffolded and compiled without errors
  - `copilot-instructions.md` file in the `.github` directory exists in the project
  - `README.md` file exists and is up to date
  - User is provided with clear instructions to debug/launch the project

Before starting a new task in the above plan, update progress in the plan.
- Work through each checklist item systematically.
- Keep communication concise and focused.
- Follow development best practices.
