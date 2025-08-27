#!/usr/bin/env bash
set -Eeuo pipefail

# ========= Styling =========
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "${BLUE}==>${NC} $*"; }
ok()  { echo -e "${GREEN}✔${NC} $*"; }
warn(){ echo -e "${YELLOW}⚠${NC} $*"; }
err() { echo -e "${RED}✖${NC} $*"; }

# ========= Args =========
ORG="sangcheol-games"
REPO=""              # 자동 감지 (git remote) 시도
PY_VER="3.12"
SKIP_DOCKER=0
SKIP_LABELS=0
SKIP_MIGRATE=0

usage() {
  cat <<USAGE
Usage: bash scripts/bootstrap.sh [options]

Options:
  --org <org>           GitHub org (default: ${ORG})
  --repo <repo>         Target repo name (default: auto-detect from git remote)
  --skip-docker         Skip docker compose up (db/redis)
  --skip-labels         Skip label setup via Hub
  --skip-migrate        Skip "alembic upgrade head"
  -h, --help            Show this help
USAGE
}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --org) ORG="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --skip-docker) SKIP_DOCKER=1; shift ;;
    --skip-labels) SKIP_LABELS=1; shift ;;
    --skip-migrate) SKIP_MIGRATE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) warn "Unknown arg: $1"; shift ;;
  esac
done

# ========= OS Detect =========
OSTYPE_LC="$(echo "${OSTYPE:-}" | tr '[:upper:]' '[:lower:]')"
IS_DARWIN=0; IS_LINUX=0; IS_WSL=0
if [[ "$OSTYPE_LC" == darwin* ]]; then IS_DARWIN=1
elif [[ "$OSTYPE_LC" == linux* ]]; then
  IS_LINUX=1
  if grep -qi microsoft /proc/version 2>/dev/null; then IS_WSL=1; fi
fi

log "Bootstrap for Sangcheol Odyssey API (uv + FastAPI)"
log "OS: $([[ $IS_DARWIN -eq 1 ]] && echo macOS || ([[ $IS_WSL -eq 1 ]] && echo WSL || echo Linux))"

# ========= Pre-checks =========
require() { command -v "$1" >/dev/null 2>&1 || { err "Missing dependency: $1"; return 1; }; }

if ! command -v git >/dev/null 2>&1; then
  if [[ $IS_DARWIN -eq 1 ]]; then
    warn "git not found. Installing via Homebrew..."
    command -v brew >/dev/null 2>&1 || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install git
  else
    warn "git not found. Installing via apt..."
    sudo apt-get update -y && sudo apt-get install -y git
  fi
fi
ok "git ready"

# ========= Install uv =========
if ! command -v uv >/dev/null 2>&1; then
  log "Installing uv..."
  if [[ $IS_DARWIN -eq 1 ]]; then
    if command -v brew >/dev/null 2>&1; then brew install uv || true; fi
    if ! command -v uv >/dev/null 2>&1; then
      curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  # Ensure PATH picks up uv (common install path)
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
ok "uv $(uv --version | head -n1)"

# ========= Python via uv =========
log "Ensuring Python ${PY_VER} via uv..."
uv python install "${PY_VER}" || true
ok "Python $(uv run python -V)"

# ========= Dependencies =========
if [[ -f "uv.lock" ]]; then
  log "Installing deps from uv.lock..."
  uv sync --all-groups
else
  log "No uv.lock found. Syncing current pyproject..."
  uv sync
fi
ok "Dependencies installed"

# ========= .env =========
if [[ -f ".env" ]]; then
  ok ".env exists"
elif [[ -f ".env.example" ]]; then
  cp .env.example .env
  ok "Created .env from .env.example"
else
  warn "No .env or .env.example found. Skipping."
fi

# ========= Docker =========
if [[ $SKIP_DOCKER -eq 0 ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    if [[ $IS_DARWIN -eq 1 || $IS_WSL -eq 1 ]]; then
      warn "Docker not found. Please install Docker Desktop and enable WSL integration (if WSL). Skipping docker step."
    else
      log "Installing Docker (Ubuntu/apt)..."
      sudo apt-get update -y
      sudo apt-get install -y ca-certificates curl gnupg lsb-release
      sudo install -m 0755 -d /etc/apt/keyrings
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
      echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
      sudo apt-get update -y
      sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
      sudo usermod -aG docker "$USER" || true
      warn "You may need to log out/in for docker group to take effect."
    fi
  fi
  if command -v docker >/dev/null 2>&1; then
    if [[ -f "docker-compose.yml" || -f "compose.yaml" ]]; then
      log "Starting db/redis via docker compose..."
      if command -v docker compose >/dev/null 2>&1; then
        docker compose up -d db redis || warn "compose up failed (check compose file/services)"
      else
        docker-compose up -d db redis || warn "docker-compose up failed (install plugin or Docker Desktop)"
      fi
      ok "Docker services attempted"
    else
      warn "No docker-compose.yml found. Skipping Docker."
    fi
  fi
else
  warn "Skip Docker requested"
fi

# ========= Alembic migrate =========
if [[ $SKIP_MIGRATE -eq 0 ]]; then
  if uv run python -c "import alembic" >/dev/null 2>&1; then
    log "Running alembic upgrade head..."
    uv run alembic upgrade head || warn "alembic upgrade failed. Check DB connection."
  else
    warn "Alembic not installed. Skipping migration."
  fi
else
  warn "Skip migrate requested"
fi

# ========= GitHub CLI & Labels via Hub =========
if [[ $SKIP_LABELS -eq 0 ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    log "Installing GitHub CLI (gh)..."
    if [[ $IS_DARWIN -eq 1 ]]; then
      command -v brew >/dev/null 2>&1 || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      brew install gh
    else
      # Install gh via apt repo
      type -p curl >/dev/null || (sudo apt-get update -y && sudo apt-get install -y curl)
      curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
      sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
        sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
      sudo apt-get update -y && sudo apt-get install -y gh
    fi
  fi
  ok "gh $(gh --version | head -n1)"

  if ! gh auth status >/dev/null 2>&1; then
    warn "GitHub CLI not authenticated. Launching login..."
    gh auth login --scopes "repo" || warn "gh auth login skipped/failed"
  fi

  if [[ -z "${REPO}" ]]; then
    if git remote get-url origin >/dev/null 2>&1; then
      # Parse org/repo from remote
      REMOTE_URL="$(git remote get-url origin)"
      if [[ "$REMOTE_URL" =~ github.com[:/]+([^/]+)/([^/.]+) ]]; then
        ORG="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
      fi
    fi
  fi
  if [[ -z "${REPO}" ]]; then
    REPO="$(basename "$(pwd)")"
    warn "Repo not provided. Falling back to current dir name: ${REPO}"
  fi
  log "Label setup target: ${ORG}/${REPO}"

  HUB_TMP="$(mktemp -d -t sc-hub-XXXXXX)"
  trap 'rm -rf "$HUB_TMP"' EXIT
  git clone --depth 1 https://github.com/sangcheol-games/sangcheol-odyssey-hub.git "$HUB_TMP"

  if [[ -x "$HUB_TMP/scripts/setup-labels.sh" ]]; then
    bash "$HUB_TMP/scripts/setup-labels.sh" "${ORG}" "${REPO}" || warn "Label setup script reported an error."
    ok "Label setup attempted via Hub (temp clone removed on exit)"
  else
    warn "Hub label script not found or not executable: $HUB_TMP/scripts/setup-labels.sh"
  fi
else
  warn "Skip labels requested"
fi

# ========= Done =========
ok "Bootstrap complete."

if grep -qi microsoft /proc/version 2>/dev/null; then
  WSL_IP="$(hostname -I | awk '{print $1}')"
  echo -e "${GREEN}Next steps:${NC}
  - Run server:  ${BLUE}uv run dev${NC}
  - Docs:        http://localhost:5000/docs
  - If WSL:      Detected WSL. Open from Windows:
                 ${BLUE}http://${WSL_IP}:5000/docs${NC}
                 (Health: http://${WSL_IP}:5000/health)"
else
  echo -e "${GREEN}Next steps:${NC}
  - Run server:  ${BLUE}uv run dev${NC}
  - Docs:        http://localhost:5000/docs"
fi
