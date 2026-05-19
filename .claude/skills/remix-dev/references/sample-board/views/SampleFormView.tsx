/**
 * [Golden File] 등록/수정 폼 View 예시
 * 실제 위치: views/{domain}/{Entity}FormView.tsx
 *
 * 패턴 포인트:
 * - defaultValues를 Props로 수신 (수정 시 loader 데이터를 Route에서 주입)
 * - useSampleForm 훅에서 React Hook Form + Zod + useFetcher 처리
 * - 50-80줄 목표
 */

import { useNavigate } from 'react-router';

import { useSampleForm } from '~/features/sample/hooks/useSampleForm';
import { Button } from '~/shared/ui/button';
import { Input } from '~/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/shared/ui/select';
import { PageLayout } from '~/widgets/layout';

interface Props {
    defaultValues?: { title?: string; content?: string; category?: string };
    isEdit?: boolean;
}

export function SampleFormView({ defaultValues, isEdit = false }: Props) {
    const navigate = useNavigate();
    const { form, handleSubmit, isSubmitting } = useSampleForm({ defaultValues, isEdit });
    const { register, formState: { errors }, setValue, watch } = form;

    return (
        <PageLayout pageTitle={isEdit ? '게시글 수정' : '게시글 등록'}>
            <form onSubmit={handleSubmit} className="card-padded space-y-4">
                <div>
                    <label htmlFor="title" className="text-label">제목</label>
                    <Input id="title" {...register('title')} placeholder="제목을 입력하세요" />
                    {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>}
                </div>

                <div>
                    <label htmlFor="category" className="text-label">카테고리</label>
                    <Select value={watch('category')} onValueChange={(v) => setValue('category', v)}>
                        <SelectTrigger>
                            <SelectValue placeholder="카테고리 선택" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="notice">공지</SelectItem>
                            <SelectItem value="general">일반</SelectItem>
                        </SelectContent>
                    </Select>
                    {errors.category && <p className="text-red-500 text-sm mt-1">{errors.category.message}</p>}
                </div>

                <div>
                    <label htmlFor="content" className="text-label">내용</label>
                    <textarea
                        id="content"
                        {...register('content')}
                        className="input min-h-[200px]"
                        placeholder="내용을 입력하세요"
                    />
                    {errors.content && <p className="text-red-500 text-sm mt-1">{errors.content.message}</p>}
                </div>

                <div className="flex gap-2">
                    <Button type="submit" disabled={isSubmitting}>
                        {isEdit ? '수정' : '등록'}
                    </Button>
                    <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                        취소
                    </Button>
                </div>
            </form>
        </PageLayout>
    );
}
