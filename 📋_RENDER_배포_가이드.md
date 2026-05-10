# 🚀 Render 배포 완벽 가이드 (5단계, 15분)

**작성일**: 2026-05-10  
**목표**: 웹사이트를 완전히 정상 작동 상태로 만들기  
**소요시간**: 약 15분  
**난이도**: ⭐⭐ (매우 쉬움)

---

## 📝 사전 확인사항

✅ **이미 완료된 것**:
- frontend/script.js 수정됨 (API_BASE_URL 동적 설정)
- Procfile 생성됨 (Render 실행 명령어)
- requirements.txt 확인됨 (모든 의존성 명시)

❌ **수동으로 해야 할 것**:
- GitHub에 코드 push (Step 1-2)
- Render 가입 & 배포 (Step 3-5)

---

## 🎯 Step 1: GitHub에 변경사항 Commit & Push

### 1.1 로컬 컴퓨터에서 실행

**Window 명령 프롬프트 (cmd) 또는 PowerShell을 열고 다음 명령 실행:**

```bash
# 프로젝트 폴더로 이동
cd D:\CDR_SynologyDrive\00_AI_AGENT\01_EDU\도구\수학 그래프 PPT 변환

# git 설정 (처음 한 번만)
git config user.email "cdrhy219@gmail.com"
git config user.name "ChoiGPT Corp"

# 변경사항 스테이징
git add frontend/script.js Procfile "20260510_웹사이트_현황분석_및_개선계획.md"

# Commit
git commit -m "✨ Render 배포 준비: API_BASE_URL 동적 설정 + Procfile 추가"

# GitHub에 Push
git push origin main
```

**결과**: ✅ GitHub 리포지토리에 반영됨

---

## 🌐 Step 2: Render 가입 & 연결

### 2.1 Render 계정 생성

1. **https://render.com** 방문
2. **"Sign Up" 클릭**
3. **GitHub로 로그인** (권장)
   - GitHub 계정으로 인증
   - Render에 리포지토리 접근 권한 부여

### 2.2 리포지토리 선택

- Render 대시보드 → **"New +"** → **"Web Service"**
- **GitHub** 선택
- **Math_Chart_to_PPT** 리포지토리 선택

---

## ⚙️ Step 3: 배포 설정 (중요!)

**다음 값들을 정확하게 입력하세요:**

| 설정 항목 | 값 | 비고 |
|----------|-----|------|
| **Service Name** | `math-chart-to-ppt` | (자동 제시될 수 있음) |
| **Runtime** | `Python 3` | 자동 선택됨 |
| **Build Command** | `pip install -r requirements.txt` | |
| **Start Command** | `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000` | 또는 Procfile 자동 사용 |
| **Environment** | **Free** | (월 $0) |

### 3.1 환경 변수 설정 (매우 중요!)

**Render 대시보드 → "Environment"**

**다음 환경 변수를 추가하세요:**

```
GEMINI_API_KEY = [당신의 Gemini API 키]
```

❓ **API 키는 어디서?**
- `D:\CDR_SynologyDrive\...\수학 그래프 PPT 변환\.env` 파일 확인
- `GEMINI_API_KEY=xxxx...` 값을 복사

---

## 🚀 Step 4: 배포 시작

1. **Render 대시보드에서 "Create Web Service" 클릭**
2. **배포 시작** (자동으로 시작됨)
3. **진행 상황 확인**:
   - 대시보드 → "Logs" 탭
   - "Building..." → "Build succeeded" 대기

**예상 소요시간**: 2-3분

---

## ✅ Step 5: 배포 확인 & 테스트

### 5.1 배포 완료 확인

Render 대시배쉬에서:
- 상태: **"Live"** (초록색) ✅
- URL: `https://math-chart-to-ppt-xxxxx.onrender.com` 생성됨

### 5.2 API 직접 테스트

**브라우저에서 다음 URL 방문:**

```
https://math-chart-to-ppt-xxxxx.onrender.com/docs
```

- FastAPI Swagger 문서가 나타나면 ✅ **성공!**

### 5.3 웹사이트 테스트 (최종 확인)

**GitHub Pages에서 테스트:**

1. https://alexchoi21.github.io/Math_Chart_to_PPT/ 방문
2. 이미지 업로드
3. PPT 다운로드

**결과**:
- ✅ "결과 데이터를 불러오는 중..." → "그래프 분석 완료"로 변경
- ✅ 다운로드 버튼 활성화
- ✅ PPT 파일 다운로드 가능

---

## 🔗 Step 6: GitHub Pages에서 API URL 업데이트 (선택사항)

현재 script.js는 자동으로 `https://math-chart-to-ppt.onrender.com`으로 설정되어 있습니다.

**만약 다른 도메인을 사용하려면:**

```javascript
// frontend/script.js 라인 13
return 'https://math-chart-to-ppt.onrender.com';
// ↓ 이 부분을 Render에서 제시된 실제 URL로 변경
return 'https://math-chart-to-ppt-xxxxx.onrender.com';
```

---

## 🐛 트러블슈팅

### Q1: "Build failed" 오류가 나왔어요

**원인**: requirements.txt에 누락된 라이브러리

**해결**:
```bash
# 로컬에서 확인
cat backend/requirements.txt
```

**필수 라이브러리 (확인 후 추가)**:
```
fastapi
uvicorn
python-pptx
google-generativeai
python-multipart
python-dotenv
pillow
```

### Q2: "CORS 에러" 또는 "API 연결 실패"

**원인**: main.py의 CORS 설정 미흡

**확인**:
```python
# backend/main.py 라인 10-17
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ 이미 설정됨
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**해결**: 이미 설정되어 있으므로 문제없음 ✅

### Q3: 15분 후 "502 Bad Gateway" 나옴

**원인**: Free 플랜의 자동 슬립 (15분 유휴 후 자동 절전)

**해결**:
- 모니터링 서비스 연동 (Uptime Robot 무료 사용)
- 또는 Pro 플랜으로 업그레이드 ($7/월)

---

## 📊 배포 후 예상 결과

| 항목 | 이전 | 이후 |
|------|------|------|
| 웹사이트 상태 | ❌ 미작동 | ✅ 정상 |
| 업로드 가능 | ❌ 불가 | ✅ 가능 |
| PPT 생성 | ❌ 불가 | ✅ 가능 |
| 다운로드 | ❌ 불가 | ✅ 가능 |
| 사용자 접근 | 0명 | 월 1000+ 명 예상 |
| 월 비용 | N/A | $0 (Free 플랜) |

---

## ✨ 최종 체크리스트

- [ ] **Step 1**: GitHub에 코드 push 완료
- [ ] **Step 2**: Render 계정 생성 & GitHub 연결 완료
- [ ] **Step 3**: 배포 설정 입력 (환경 변수 포함)
- [ ] **Step 4**: 배포 시작 & "Live" 상태 확인
- [ ] **Step 5**: API Swagger 문서 (/docs) 확인
- [ ] **Step 6**: 웹사이트에서 이미지 업로드 & PPT 다운로드 테스트

---

## 💬 문제 발생 시

**Render 배포 로그 확인:**
1. Render 대시보드 → "Logs" 탭
2. 마지막 배포 로그 확인
3. 오류 메시지 복사 & 검색

**일반적인 오류:**
- `ModuleNotFoundError`: requirements.txt 누락
- `GEMINI_API_KEY not found`: 환경 변수 미설정
- `Connection refused`: 포트 설정 오류 (이미 자동 설정됨)

---

## 🎉 배포 완료!

이 모든 단계를 완료하면:

✅ **웹사이트 정상 작동**  
✅ **사용자가 PPT를 실제로 다운로드 가능**  
✅ **24시간 운영 (Free 플랜 기준 15분 슬립)**  
✅ **향후 수익화 가능**

---

**다음 단계 (Phase 2):**
- 모바일 반응형 개선 (3-5일)
- 사용자 계정 시스템 (1-2주)
- 결제 시스템 (1-2주)

---

**📞 도움이 필요하면?**

Render 공식 문서: https://render.com/docs  
FastAPI 배포 가이드: https://fastapi.tiangolo.com/deployment/
