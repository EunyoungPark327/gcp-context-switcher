# GCP Context Switcher

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

**빠른 GCP 계정/프로젝트/GKE 클러스터 전환을 위한 인터랙티브 CLI 도구**

매번 `gcloud auth login`, `gcloud config set project`, `gcloud container clusters get-credentials` 등을 수동으로 입력하는 번거로움을 해결합니다.

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   ██████   ██████  ██████   ██████ ███████       │
│  ██       ██      ██    ██ ██      ██            │
│  ██   ███ ██      ██████   ██     ███████        │
│  ██    ██ ██      ██       ██          ██        │
│   ██████   ██████ ██       ██████ ███████        │
│                                                  │
│           C o n t e x t   S w i t c h e r       │
└──────────────────────────────────────────────────┘
```

## ✨ 주요 기능

- 🔑 **계정 전환** - 인증된 GCP 계정 간 빠른 전환
- 📁 **프로젝트 전환** - 접근 가능한 프로젝트 목록에서 선택
- ☸️ **GKE 클러스터 연결** - 클러스터 선택 후 자동으로 크레덴셜 획득
- 🔄 **kubectl 컨텍스트 전환** - 기존 컨텍스트 간 빠른 전환
- 🚀 **전체 플로우** - 계정 → 프로젝트 → 클러스터를 한 번에 설정
- 🔍 **검색 기능** - `/` 키로 긴 목록에서 빠르게 검색

## 📋 요구사항

- Python 3.12+
- `gcloud` CLI 설치 및 초기화
- `kubectl` 설치 (GKE 사용 시)

## 🚀 설치

### pip 설치 (권장)

```bash
pip install git+https://github.com/EunyoungPark327/gcp-context-switcher.git
```

### 수동 설치

```bash
git clone https://github.com/EunyoungPark327/gcp-context-switcher.git
cd gcp-context-switcher
pip install -e .
```

## 📖 사용법

### 대화형 모드 (기본)

```bash
gcp-switcher
# 또는 단축 명령어
gcps
```

화살표 키로 이동하고 Enter로 선택합니다.

### 직접 명령어

```bash
gcp-switcher account   # 계정 선택/전환
gcp-switcher project   # 프로젝트 선택/전환
gcp-switcher cluster   # GKE 클러스터 선택 및 크레덴셜 획득
gcp-switcher context   # kubectl 컨텍스트 전환
gcp-switcher full      # 전체 플로우 (계정 → 프로젝트 → 클러스터)
gcp-switcher status    # 현재 상태 확인
```

### 키보드 단축키

| 키 | 동작 |
|---|---|
| `↑` / `k` | 위로 이동 |
| `↓` / `j` | 아래로 이동 |
| `Enter` | 선택 |
| `/` | 검색 모드 |
| `q` / `ESC` | 취소/종료 |

## 🎯 일반적인 사용 시나리오

### 1. 다른 프로젝트의 GKE 클러스터로 전환

```bash
gcp-switcher full
```

1. 계정 선택 (또는 현재 계정 유지)
2. 프로젝트 선택
3. GKE 클러스터 선택 → 자동으로 크레덴셜 획득

### 2. 기존 컨텍스트로 빠르게 전환

이미 크레덴셜을 가져온 적 있는 클러스터라면:

```bash
gcp-switcher context
```

### 3. 프로젝트만 변경

```bash
gcp-switcher project
```

## ⚡ 팁: Shell Alias

자주 사용하는 명령어에 별칭 설정:

```bash
# ~/.bashrc 또는 ~/.zshrc
alias gs='gcp-switcher'
alias gss='gcp-switcher status'
alias gsc='gcp-switcher cluster'
alias gsf='gcp-switcher full'
```

## 🔧 작동 원리

이 도구는 내부적으로 다음 gcloud/kubectl 명령어를 실행합니다:

```bash
# 계정 관련
gcloud auth list --format=value(account)
gcloud config set account <account>
gcloud auth login

# 프로젝트 관련
gcloud projects list --format=value(projectId)
gcloud config set project <project>

# GKE 클러스터 관련
gcloud container clusters list --format=json
gcloud container clusters get-credentials <cluster> --zone <zone>

# kubectl 컨텍스트 관련
kubectl config get-contexts -o=name
kubectl config use-context <context>
```

## 🤝 기여하기

버그 리포트, 기능 제안, PR 모두 환영합니다!

## 📝 라이선스

MIT License
