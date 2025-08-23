# Sangcheol Odyssey — FastAPI API Server

FastAPI backend for Sangcheol Odyssey. Uses **uv** for Python env + deps.

- Hub: https://github.com/sangcheol-games/sangcheol-odyssey-hub  
- Hub Wiki: https://github.com/sangcheol-games/sangcheol-odyssey-hub/wiki

---

## 🚀 One-Click Setup (권장)

```bash
# 레포 클론 후 프로젝트 루트에서
chmod +x scripts/bootstrap.sh
bash scripts/bootstrap.sh --org sangcheol-games --repo sangcheol-odyssey-api
```

이 스크립트는 아래를 자동으로 수행합니다:
- uv 설치/확인 + Python 3.12 설치
- 의존성 설치 (`uv.lock` 기준)
- `.env.example` → `.env` 생성
- Docker Compose로 `db`(Postgres) / `redis` 기동 (가능한 환경일 때)
- Alembic DB 마이그레이션 적용 (`upgrade head`)
- Hub 레포를 자동 클론하여 **라벨 세팅** 실행  
  (`.tools/sangcheol-odyssey-hub/scripts/setup-labels.sh sangcheol-games sangcheol-odyssey-api`)

---

## 🧩 Manual Setup (대안)

### Requirements
- Python 3.12+
- Docker & Docker Compose
- uv: https://docs.astral.sh/uv/

### 1) Setup
```bash
# 가상환경에 Python 설치
uv python install 3.12
# 의존성 설치
uv sync
```

### 2) Configure
```bash
# sample 파일 복사한 .env파일에서 필요한 값 수정
cp .env.example .env
```

### 3) Infra (DB, Redis)
```bash
# DB(postgres, redis) 시작
docker compose up -d db redis
```

### 4) DB Migration
```bash
# DB 마이그레이션 최신화
uv run alembic upgrade head
```

### 5) Run
```bash
# 파일 변경사항 있을때마다 리로드
uv run dev     
# 리로드 X (프로덕션 모드)
uv run serve
```

### 6) 테스트 & Docs 페이지

- `uv run dev` 후  **http://localhost:8000/docs** 접속 (API docs page)
- 브라우저 접속이 안 되면 터미널에서 확인:
  ```bash
  curl http://localhost:8000/health       # {"message":"healthy"}
  curl http://localhost:8000/v1/ping      # {"message":"pong"}

**WSL 사용 시(예외 처리)**

* WSL 사용시 Windows 브라우저에서 `localhost`가 안 열릴 수 있습니다. 아래처럼 **WSL IP**로 접속하세요.

  ```bash
  # WSL 터미널에서 IP 확인
  hostname -I | awk '{print $1}'
  # 브라우저에서 접속
  http://<WSL_IP>:8000/docs
  ```

---

## 🏷 Label Setup (Hub 중앙 관리)

라벨은 **sangcheol-odyssey-hub**에서 중앙 관리합니다.  
부트스트랩을 실행하면 자동으로 라벨이 동기화됩니다.  
수동으로 실행하려면:

```bash
git clone https://github.com/sangcheol-games/sangcheol-odyssey-hub.git
bash sangcheol-odyssey-hub/scripts/setup-labels.sh sangcheol-games sangcheol-odyssey-api
```

> GitHub CLI로 로그인되어 있어야 합니다:  
> `gh auth login --scopes "repo"`

---

## 🛠 Scripts

- `uv run dev` → 개발 서버(reload)
- `uv run serve` → 프로덕션 스타일 실행
