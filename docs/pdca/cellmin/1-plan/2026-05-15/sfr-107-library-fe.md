# Plan: SFR-107 고서 목록 페이지 FE 구현 (/library)

**Redmine:** #101  
**Date:** 2026-05-15  
**Author:** cellmin

---

## 1. 목표 및 범위

로그인한 사용자가 본인의 고서 번역 이력을 조회하고, 번역 상세 결과를 확인할 수 있는 라이브러리 페이지를 구현한다.

**범위:**
- `/library` — 번역 이력 목록 (페이지네이션 + 상태 필터 탭)
- `/library/:id` — 번역 결과 상세 페이지
- 로그인 필수 (_protected 레이아웃)
- 신규 번역은 /translate 페이지로 이동

**범위 외:**
- BE API 추가 구현 없음 (SFR-106에서 완료)
- 실시간 폴링 (추후 Act 단계에서 검토)

---

## 2. 사용 대상

- 로그인한 일반 사용자 (USER 이상)
- 본인 번역 이력만 조회 가능 (BE에서 user_id 필터링)

---

## 3. 핵심 요구사항

### /library (목록)
1. 번역 이력 목록 표시 (title, status, created_at)
2. 상태 탭 필터: **전체 / 완료 / 대기중 / 실패**
   - 전체: 필터 없음
   - 완료: status=COMPLETED
   - 대기중: status=PENDING (OCR_PROCESSING/TRANSLATING은 전체 탭에서만 노출)
   - 실패: status=FAILED
3. 페이지네이션 (size=10)
4. 새 번역 버튼 → /translate 이동
5. 항목 클릭 → /library/:id 이동

### /library/:id (상세)
1. 번역 제목, 상태, 전체 페이지 수 표시
2. 페이지별 OCR 원문 / 직역 / 의역 3단 표시
3. 뒤로가기 → /library 이동
4. FAILED 상태 시 오류 메시지 표시

---

## 4. API

```
POST /api/v1/translate/list
  Body: { page, size, status? }
  Auth: 필수 (USER+)

GET /api/v1/translate/{book_id}
  Auth: 필수 (USER+)
```

---

## 5. 성공 기준

- [ ] /library 페이지 접근 시 목록 렌더링
- [ ] 탭 전환 시 status 필터 적용되어 목록 갱신
- [ ] 페이지네이션 동작
- [ ] 항목 클릭 시 /library/:id 이동
- [ ] /library/:id에서 번역 상세(OCR/직역/의역) 표시
- [ ] 비로그인 시 로그인 필요 안내 모달 → /login?redirect=... 이동 (_protected 레이아웃 처리)
- [ ] TypeScript 오류 0, lint 오류 0
