export const getCommentAuthorName = (c: {
    is_ai_gen: boolean;
    author_name: string | null;
}): string => (c.is_ai_gen ? '해독이(AI)' : c.author_name ?? '익명');
