import { useState } from "react";

import { Pencil, RefreshCcw, Trash2 } from "lucide-react";

import { useBoardCategories } from "~/features/boards/hooks/useBoardCategories";
import {
  useCreateBoardCategory,
  useDeleteBoardCategory,
  useUpdateBoardCategory,
} from "~/features/boards/hooks/useBoardCategoryMutations";

import { openModal } from "~/shared/stores/modalStore";
import { Button } from "~/shared/ui/button";
import { Switch } from "~/shared/ui/switch";

import type { FormEvent } from "react";
import type { AdminBoard, AdminBoardCategory } from "~/entities/board/types";

interface BoardCategoryDialogProps {
  board: AdminBoard | null;
  open: boolean;
  onClose: () => void;
}

interface CategoryFormState {
  category_name: string;
  sort_order: string;
  use_yn: boolean;
}

const emptyCategoryForm: CategoryFormState = {
  category_name: "",
  sort_order: "0",
  use_yn: true,
};

export function BoardCategoryDialog({ board, open, onClose }: BoardCategoryDialogProps) {
  const boardId = board?.id ?? "";
  const [editingCategory, setEditingCategory] = useState<AdminBoardCategory | null>(null);
  const [form, setForm] = useState<CategoryFormState>(emptyCategoryForm);
  const categoriesQuery = useBoardCategories(board?.id ?? null, open);
  const createCategory = useCreateBoardCategory(boardId);
  const updateCategory = useUpdateBoardCategory(boardId);
  const deleteCategory = useDeleteBoardCategory(boardId);
  const isSaving = createCategory.isPending || updateCategory.isPending;

  if (!open || !board) return null;

  function resetForm() {
    setEditingCategory(null);
    setForm(emptyCategoryForm);
  }

  function handleEdit(category: AdminBoardCategory) {
    setEditingCategory(category);
    setForm({
      category_name: category.category_name,
      sort_order: String(category.sort_order),
      use_yn: category.use_yn,
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const categoryName = form.category_name.trim();
    if (!categoryName) {
      openModal({ type: "error", message: "카테고리 이름을 입력해주세요." });
      return;
    }

    const request = {
      category_name: categoryName,
      sort_order: Number(form.sort_order) || 0,
      use_yn: form.use_yn,
    };

    if (editingCategory) {
      updateCategory.mutate(
        { categoryId: editingCategory.id, request },
        {
          onSuccess: resetForm,
          onError: () => openModal({ type: "error", message: "카테고리를 수정하지 못했습니다." }),
        },
      );
      return;
    }

    createCategory.mutate(request, {
      onSuccess: resetForm,
      onError: () => openModal({ type: "error", message: "카테고리를 등록하지 못했습니다." }),
    });
  }

  function handleDelete(category: AdminBoardCategory) {
    openModal({
      type: "confirm",
      title: "카테고리 삭제",
      message: "카테고리가 삭제됩니다.\n계속 진행할까요?",
      buttons: [
        { label: "취소", variant: "outline" },
        {
          label: "삭제",
          variant: "destructive",
          onClick: () => {
            deleteCategory.mutate(category.id, {
              onSuccess: () => {
                if (editingCategory?.id === category.id) resetForm();
              },
              onError: () =>
                openModal({ type: "error", message: "카테고리를 삭제하지 못했습니다." }),
            });
          },
        },
      ],
    });
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 px-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-md border border-border bg-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">카테고리 관리</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {board.board_name} 게시판의 카테고리를 관리합니다.
            </p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>
            닫기
          </Button>
        </div>

        <form className="mt-6 grid gap-3 rounded-md border border-border bg-background p-4 md:grid-cols-[1fr_120px_120px_auto]" onSubmit={handleSubmit}>
          <TextField
            label="카테고리 이름"
            value={form.category_name}
            required
            onChange={(value) => setForm((current) => ({ ...current, category_name: value }))}
          />
          <TextField
            label="정렬 순서"
            type="number"
            value={form.sort_order}
            onChange={(value) => setForm((current) => ({ ...current, sort_order: value }))}
          />
          <SwitchField
            label="사용 여부"
            checked={form.use_yn}
            onChange={(checked) => setForm((current) => ({ ...current, use_yn: checked }))}
          />
          <div className="flex items-end gap-2">
            <Button type="submit" disabled={isSaving}>
              {editingCategory ? "수정" : "등록"}
            </Button>
            {editingCategory ? (
              <Button type="button" variant="outline" onClick={resetForm}>
                취소
              </Button>
            ) : null}
          </div>
        </form>

        <CategoryTable
          categories={categoriesQuery.data ?? []}
          isLoading={categoriesQuery.isLoading}
          isError={categoriesQuery.isError}
          isDeleting={deleteCategory.isPending}
          onRetry={() => void categoriesQuery.refetch()}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>
    </div>
  );
}

interface CategoryTableProps {
  categories: AdminBoardCategory[];
  isLoading: boolean;
  isError: boolean;
  isDeleting: boolean;
  onRetry: () => void;
  onEdit: (category: AdminBoardCategory) => void;
  onDelete: (category: AdminBoardCategory) => void;
}

function CategoryTable({
  categories,
  isLoading,
  isError,
  isDeleting,
  onRetry,
  onEdit,
  onDelete,
}: CategoryTableProps) {
  if (isLoading) {
    return <div className="mt-4 rounded-md border border-border p-6 text-sm text-muted-foreground">카테고리를 불러오는 중입니다.</div>;
  }

  if (isError) {
    return (
      <div className="mt-4 flex items-center justify-between rounded-md border border-border p-5">
        <p className="text-sm text-muted-foreground">카테고리를 불러오지 못했습니다.</p>
        <Button variant="outline" onClick={onRetry}>
          <RefreshCcw />
          다시 시도
        </Button>
      </div>
    );
  }

  if (categories.length === 0) {
    return <div className="mt-4 rounded-md border border-border p-6 text-sm text-muted-foreground">등록된 카테고리가 없습니다.</div>;
  }

  return (
    <div className="mt-4 overflow-hidden rounded-md border border-border">
      <table className="w-full min-w-[520px] text-left text-sm">
        <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-[0.08em] text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">카테고리</th>
            <th className="px-4 py-3 font-medium">정렬</th>
            <th className="px-4 py-3 font-medium">상태</th>
            <th className="w-28 px-4 py-3 font-medium">관리</th>
          </tr>
        </thead>
        <tbody>
          {categories.map((category) => (
            <tr key={category.id} className="border-b border-border last:border-b-0">
              <td className="px-4 py-3 font-medium">{category.category_name}</td>
              <td className="px-4 py-3 tabular-nums">{category.sort_order}</td>
              <td className="px-4 py-3">
                <span className="rounded-full border border-border px-2 py-1 text-xs">
                  {category.use_yn ? "사용" : "미사용"}
                </span>
              </td>
              <td className="px-4 py-3">
                <Button
                  aria-label="카테고리 수정"
                  variant="ghost"
                  size="icon"
                  onClick={() => onEdit(category)}
                >
                  <Pencil />
                </Button>
                <Button
                  aria-label="카테고리 삭제"
                  variant="ghost"
                  size="icon"
                  disabled={isDeleting}
                  onClick={() => onDelete(category)}
                >
                  <Trash2 />
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface TextFieldProps {
  label: string;
  value: string;
  type?: "text" | "number";
  required?: boolean;
  onChange: (value: string) => void;
}

function TextField({ label, value, type = "text", required, onChange }: TextFieldProps) {
  return (
    <label className="space-y-1 text-sm font-medium">
      <span>{label}</span>
      <input
        value={value}
        type={type}
        required={required}
        className="h-10 w-full rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

interface SwitchFieldProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function SwitchField({ label, checked, onChange }: SwitchFieldProps) {
  const currentLabel = checked ? "사용" : "미사용";

  return (
    <div className="space-y-1 text-sm font-medium">
      <div className="flex items-center justify-between gap-2">
        <span>{label}</span>
        <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
          {currentLabel}
        </span>
      </div>
      <div className="flex h-10 w-full items-center justify-between rounded-md border border-border bg-secondary px-3 text-sm">
        <span className="text-muted-foreground">{currentLabel}</span>
        <Switch checked={checked} onCheckedChange={onChange} />
      </div>
    </div>
  );
}
