/**
 * [Golden File] 상세/폼 Page 예시
 * 실제 위치: pages/{domain}/{Domain}DetailPage.tsx
 *
 * 패턴 포인트:
 * - 이벤트 핸들러 + UI 조합만 (200줄 이하)
 * - useMyForm 훅에서 RHF + Zod 처리
 * - disabled={isSaving || !form.formState.isDirty} — 불필요한 PUT 방지
 * - ConfirmDialog로 삭제 확인
 * - 로딩/에러 상태 분기
 */
import { useParams, useNavigate } from 'react-router-dom';

import { PageTitle } from '@/shared/components/PageTitle';
import { ConfirmDialog } from '@/shared/components/ConfirmDialog';
import { Button } from '@/shared/ui/button';
import { Card, CardContent } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { Skeleton } from '@/shared/ui/skeleton';

import { useSampleForm } from '@/features/sample/hooks/useSampleForm';

export function SampleDetailPage() {
    // 1. Hooks
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const {
        form, isEditMode, isLoading, isSaving, isDeleting,
        handleSubmit, handleDelete,
        showDeleteDialog, setShowDeleteDialog,
    } = useSampleForm(id);

    const { register, formState: { errors }, setValue, watch } = form;

    // 7. Early returns
    if (isLoading) {
        return (
            <div className="content-wrapper">
                <PageTitle title={isEditMode ? '수정' : '등록'} />
                <Card><CardContent className="space-y-4 pt-6">
                    {Array.from({ length: 4 }).map((_, i) => (
                        <Skeleton key={i} className="h-10 w-full" />
                    ))}
                </CardContent></Card>
            </div>
        );
    }

    // 8. JSX
    return (
        <div className="content-wrapper">
            <PageTitle title={isEditMode ? 'Sample 수정' : 'Sample 등록'} />

            <Card>
                <CardContent className="space-y-4 pt-6">
                    <div className="form-grid">
                        <div className="form-row">
                            <Label htmlFor="name">이름 *</Label>
                            <Input id="name" {...register('name')} />
                            {errors.name && (
                                <p role="alert" className="text-destructive text-sm">{errors.name.message}</p>
                            )}
                        </div>

                        <div className="form-row">
                            <Label htmlFor="category">카테고리 *</Label>
                            <Select value={watch('category')} onValueChange={(v) => setValue('category', v)}>
                                <SelectTrigger id="category">
                                    <SelectValue placeholder="선택" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="general">일반</SelectItem>
                                    <SelectItem value="notice">공지</SelectItem>
                                </SelectContent>
                            </Select>
                            {errors.category && (
                                <p role="alert" className="text-destructive text-sm">{errors.category.message}</p>
                            )}
                        </div>
                    </div>

                    <div className="form-row">
                        <Label htmlFor="description">설명</Label>
                        <Input id="description" {...register('description')} />
                    </div>
                </CardContent>
            </Card>

            {/* 액션 버튼 */}
            <div className="detail-actions">
                <Button variant="outline" onClick={() => navigate('/sample')}>
                    목록
                </Button>
                {isEditMode && (
                    <Button
                        variant="destructive"
                        onClick={() => setShowDeleteDialog(true)}
                        disabled={isDeleting}
                    >
                        삭제
                    </Button>
                )}
                <Button
                    onClick={handleSubmit}
                    disabled={isSaving || !form.formState.isDirty}
                >
                    {isEditMode ? '수정' : '등록'}
                </Button>
            </div>

            {/* 삭제 확인 다이얼로그 */}
            <ConfirmDialog
                open={showDeleteDialog}
                onOpenChange={setShowDeleteDialog}
                title="삭제 확인"
                description="정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
                onConfirm={handleDelete}
                confirmLabel="삭제"
                variant="destructive"
            />
        </div>
    );
}
