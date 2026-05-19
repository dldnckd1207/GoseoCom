# 구현 패턴 템플릿

---

## Feature 모듈 구조

```
features/{domain}/
├── api/             # API 호출 함수
├── hooks/           # useQuery, useMutation, 폼 상태 훅
├── components/      # 기능 전용 UI 컴포넌트
├── types/           # 타입 정의
├── utils/           # 헬퍼 함수 (변환, 포맷팅)
├── constants/       # 상수 (선택)
└── index.ts         # 배럴 export
```

---

## 1. Hook 종류별 역할

| Hook 유형 | 역할 | 예시 |
|-----------|------|------|
| `use{Entity}List` | 목록 조회 (`useQuery`) | `useBoardList`, `useUserList` |
| `use{Entity}Detail` | 상세 조회 (`useQuery`) | `useBoardDetail`, `useUserDetail` |
| `useCreate{Entity}` / `useUpdate{Entity}` / `useDelete{Entity}` | CUD (`useMutation`) | `useCreateBoard`, `useUpdateBoard` |
| `use{Entity}Form` | 폼 상태 + 비즈니스 로직 통합 | `useBoardForm`, `useUserForm` |

---

## 2. 목록 조회 Hook 패턴

```typescript
import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/shared/lib/queryKeys';

import { getMyList } from '../api';

import type { MySearchParams } from '../types';

export function useMyList(params: MySearchParams) {
    return useQuery({
        queryKey: queryKeys.my.list(params),
        queryFn: () => getMyList(params),
    });
}
```

---

## 3. CUD Mutation Hook 패턴

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { queryKeys } from '@/shared/lib/queryKeys';

import { createMy, updateMy, deleteMy } from '../api';

import type { MyCreateRequest, MyUpdateRequest } from '../types';

export function useCreateMy() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: MyCreateRequest) => createMy(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.my.all });
            toast.success('등록되었습니다.');
        },
        onError: () => {
            toast.error('등록 중 오류가 발생했습니다.');
        },
    });
}

export function useUpdateMy() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: MyUpdateRequest) => updateMy(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.my.all });
            toast.success('수정되었습니다.');
        },
        onError: () => {
            toast.error('수정 중 오류가 발생했습니다.');
        },
    });
}

export function useDeleteMy() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => deleteMy(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.my.all });
            toast.success('삭제되었습니다.');
        },
        onError: () => {
            toast.error('삭제 중 오류가 발생했습니다.');
        },
    });
}
```

---

## 4. 폼 Hook 패턴 (React Hook Form + Zod)

> **신규 폼은 반드시 RHF + Zod로 작성한다.** 수동 `if`문 유효성 검사는 금지.
> 폼 훅 내부에서 `useNavigate`를 직접 사용해도 허용 (페이지 이동이 폼 제출의 일부이므로).

```typescript
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { z } from 'zod';

import { useMyDetail } from './useMyDetail';
import { useCreateMy, useUpdateMy, useDeleteMy } from './useMyMutation';

import { detailToFormData } from '../utils/transform';

// Zod 스키마 — Single Source of Truth
const myFormSchema = z.object({
    name: z.string().min(1, '이름을 입력해주세요'),
    description: z.string().optional(),
    category: z.string().min(1, '카테고리를 선택해주세요'),
});

type MyFormData = z.infer<typeof myFormSchema>;

export function useMyForm(id?: string) {
    const isEditMode = !!id;
    const navigate = useNavigate();

    // React Hook Form
    const form = useForm<MyFormData>({
        resolver: zodResolver(myFormSchema),
        defaultValues: { name: '', description: '', category: '' },
    });

    // API Hooks
    const { data: detailData, isLoading } = useMyDetail(id || '');
    const createMutation = useCreateMy();
    const updateMutation = useUpdateMy();
    const deleteMutation = useDeleteMy();

    // 상세 데이터 로드 시 폼에 반영
    useEffect(() => {
        if (isEditMode && detailData?.header.success && detailData.body.data) {
            form.reset(detailToFormData(detailData.body.data));
        }
    }, [isEditMode, detailData, form]);

    // 저장 (Zod가 자동 검증)
    const handleSubmit = form.handleSubmit(async (data) => {
        try {
            if (isEditMode && id) {
                await updateMutation.mutateAsync({ id, ...data });
            } else {
                await createMutation.mutateAsync(data);
            }
            navigate('/my');
        } catch {
            // onError에서 toast 처리
        }
    });

    // 삭제
    async function handleDelete() {
        if (!id || !confirm('정말 삭제하시겠습니까?')) return;
        try {
            await deleteMutation.mutateAsync(id);
            navigate('/my');
        } catch {
            // onError에서 toast 처리
        }
    }

    return {
        form,
        isLoading,
        isSaving: createMutation.isPending || updateMutation.isPending,
        isDeleting: deleteMutation.isPending,
        handleSubmit,
        handleDelete,
        isEditMode,
    };
}
```

---

## 5. Page 패턴

### Page 크기 기준

| 기준 | 조치 |
|------|------|
| **200줄 이하** | 적정 (목표) |
| **200~300줄** | 분리 검토 (useState 5개 이상이면 `useMyForm` Hook으로 분리) |
| **300줄 이상** | 분리 필수 (비즈니스 로직 → Hook, UI 반복 → Component) |

### useNavigate 위치 규칙

| 방식 | 사용 시점 | 예시 |
|------|----------|------|
| **방법 1 (권장):** Page에서 호출, Hook에 콜백 전달 | 일반 Hook | `useCreateMy({ onSuccess: () => navigate('/my') })` |
| **방법 2 (허용):** 폼 훅 내부에서 직접 사용 | 복합 폼 Hook | `useMyForm` 내부에서 `navigate('/my')` |

> 신규 코드는 **방법 1**을 우선. 폼 훅처럼 페이지 이동이 폼 제출의 일부인 경우에만 방법 2 허용.

### 목록 Page

```typescript
// pages/{domain}/MyListPage.tsx
import { useState } from 'react';

import { usePagination } from '@/shared/hooks';
import { Button } from '@/shared/ui/button';

import { MyFilter, MyTable } from '@/features/my/components';
import { useMyList } from '@/features/my/hooks';

import type { MySearchParams } from '@/features/my/types';

export function MyListPage() {
    const { page, size, setPage } = usePagination({ initialSize: 10 });
    const [searchParams, setSearchParams] = useState<MySearchParams>({});

    const { data, isLoading } = useMyList({ ...searchParams, page, size });

    function handleSearch(params: MySearchParams) {
        setSearchParams(params);
        setPage(1);
    }

    return (
        <div className="content-wrapper">
            <MyFilter onSearch={handleSearch} />
            <div className="list-header">
                <p className="list-count">
                    총 <span className="text-primary font-medium">{data?.total ?? 0}</span>건
                </p>
                <Button>등록</Button>
            </div>
            <MyTable data={data} isLoading={isLoading} />
        </div>
    );
}
```

### 상세/폼 Page

```typescript
// pages/{domain}/MyDetailPage.tsx
import { useParams, useNavigate } from 'react-router-dom';

import { Button } from '@/shared/ui/button';

import { MyForm } from '@/features/my/components';
import { useMyForm } from '@/features/my/hooks';

export function MyDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const {
        form, isLoading, isSaving, isDeleting,
        handleSubmit, handleDelete, isEditMode,
    } = useMyForm(id);

    return (
        <div className="content-wrapper">
            <MyForm form={form} isLoading={isLoading} />
            <div className="flex gap-3">
                <Button variant="outline" onClick={() => navigate('/my')}>목록</Button>
                {isEditMode && (
                    <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
                        삭제
                    </Button>
                )}
                {/* isDirty: 폼 변경이 없으면 비활성화 → 불필요한 PUT 요청 방지 */}
                <Button onClick={handleSubmit} disabled={isSaving || !form.formState.isDirty}>
                    {isEditMode ? '수정' : '등록'}
                </Button>
            </div>
        </div>
    );
}
```

---

## 6. 데이터 변환 함수

> API 응답 ↔ 폼 데이터 변환은 `features/{domain}/utils/transform.ts`에 배치한다.

```typescript
// features/{domain}/utils/transform.ts

import type { MyDetail, MyFormData, MyCreateRequest } from '../types';

// API 응답 → 폼 데이터
export function detailToFormData(detail: MyDetail): MyFormData {
    return {
        name: detail.name,
        description: detail.description ?? '',
        category: detail.category,
    };
}

// 폼 데이터 → API 요청
export function formDataToRequest(formData: MyFormData): MyCreateRequest {
    return {
        name: formData.name,
        description: formData.description || undefined,
        category: formData.category,
    };
}
```

---

## 7. 레퍼런스 구현 (Golden Files)

새 기능을 구현할 때, `references/sample-manage/` 안의 예시 파일을 **실제로 열어서 패턴을 따라** 작성하세요.
CRUD 관리 페이지의 전체 패턴(목록 + 상세/폼 + 생성 + 수정 + 삭제)을 포함합니다.

| 레이어 | 레퍼런스 파일 | 참조 포인트 |
|--------|-------------|------------|
| **타입 정의** | `sample-manage/features/sample/types/index.ts` | Response, Detail, SearchParams, Request, FormData |
| **API 함수** | `sample-manage/features/sample/api/sampleApi.ts` | apiClient, POST/PUT/DELETE, axios.delete body |
| **목록 Hook** | `sample-manage/features/sample/hooks/useSampleList.ts` | useQuery + queryKeys + body.data 추출 |
| **상세 Hook** | `sample-manage/features/sample/hooks/useSampleDetail.ts` | useQuery + enabled: !!id |
| **Mutation Hook** | `sample-manage/features/sample/hooks/useSampleMutation.ts` | useMutation + invalidateQueries + toast |
| **폼 Hook** | `sample-manage/features/sample/hooks/useSampleForm.ts` | RHF + Zod + 다중 Mutation + navigate |
| **데이터 변환** | `sample-manage/features/sample/utils/sampleTransformers.ts` | detailToFormData, formDataToRequest |
| **배럴 export** | `sample-manage/features/sample/index.ts` | components + types만 (hooks/api 제외) |
| **목록 Page** | `sample-manage/pages/SampleListPage.tsx` | usePagination + 검색 + 테이블 + 접근성 |
| **상세/폼 Page** | `sample-manage/pages/SampleDetailPage.tsx` | useSampleForm + isDirty + ConfirmDialog |

> **사용법:** `sample-manage/features/sample/`의 구조를 복사하고 → 도메인명과 타입만 교체
