# Sangcheol Odyssey — FastAPI API Server

FastAPI backend for Sangcheol Odyssey. Uses **uv** for Python env + deps.

---

## 프로젝트 설정

### 필수 항목
- Python 3.12+
- Docker & Docker Compose
- uv: https://docs.astral.sh/uv/

### 1) Setup
```bash
# 가상환경에 Python 설치
uv python install 3.12

# 의존성 설치
uv sync
````

### 2) Configure

```bash
# sample 복사 후 .env 파일에 필요한 값 수정
cp .env.example .env
```

### 3) Infra (DB, Redis)

```bash
docker compose up -d db redis
```

### 4) DB Migration

```bash
uv run alembic upgrade head
```

### 5) Run

```bash
# 코드 변경사항 있을때마다 리로드
uv run dev
# 리로드 없음(프로덕션 모드)
uv run serve
```

### 6) 테스트(임시)

```bash
curl http://127.0.0.1:8000/health    # {"message":"healthy"}
curl http://127.0.0.1:8000/v1/ping   # {"message":"pong"}
```

> WSL2에서 브라우저가 `localhost:8000`로 안 열리면 Windows `~/.wslconfig`에
> `[wsl2]\nlocalhostForwarding=true` 추가 후 `wsl --shutdown`.

---

## Label Setup (Hub)

라벨은 Hub 레포에서 중앙 관리합니다.

```bash
git clone https://github.com/sangcheol-games/sangcheol-odyssey-hub.git
cd sangcheol-odyssey-hub
./scripts/setup-labels.sh sangcheol-games sangcheol-odyssey-api
```

* Hub: [https://github.com/sangcheol-games/sangcheol-odyssey-hub](https://github.com/sangcheol-games/sangcheol-odyssey-hub)
* Hub Wiki: [https://github.com/sangcheol-games/sangcheol-odyssey-hub/wiki](https://github.com/sangcheol-games/sangcheol-odyssey-hub/wiki)

---

## Scripts

* `uv run dev` → 개발 서버(reload)
* `uv run serve` → 프로덕션 스타일 실행

