import type { AdminBoard, AdminBoardSaveRequest, BoardType } from "~/entities/board/types";

export interface BoardFormState {
  board_code: string;
  board_name: string;
  board_desc: string;
  board_group: string;
  board_type: BoardType;
  guest_read_yn: boolean;
  write_yn: boolean;
  comment_yn: boolean;
  category_yn: boolean;
  attach_yn: boolean;
  attach_ext: string;
  auto_reply_enabled: boolean;
  use_yn: boolean;
  sort_order: number;
}

export const emptyBoardForm: BoardFormState = {
  board_code: "",
  board_name: "",
  board_desc: "",
  board_group: "",
  board_type: "LIST",
  guest_read_yn: true,
  write_yn: true,
  comment_yn: false,
  category_yn: false,
  attach_yn: true,
  attach_ext: "",
  auto_reply_enabled: false,
  use_yn: true,
  sort_order: 0,
};

export function boardToForm(board: AdminBoard): BoardFormState {
  return {
    board_code: board.board_code,
    board_name: board.board_name,
    board_desc: board.board_desc ?? "",
    board_group: board.board_group ?? "",
    board_type: board.board_type,
    guest_read_yn: board.guest_read_yn,
    write_yn: board.write_yn,
    comment_yn: board.comment_yn,
    category_yn: board.category_yn,
    attach_yn: board.attach_yn,
    attach_ext: board.attach_ext ?? "",
    auto_reply_enabled: board.auto_reply_enabled,
    use_yn: board.use_yn,
    sort_order: board.sort_order,
  };
}

export function formToRequest(form: BoardFormState, mode: "create" | "edit"): AdminBoardSaveRequest {
  const request: AdminBoardSaveRequest = {
    board_name: form.board_name.trim(),
    board_desc: form.board_desc.trim() || null,
    board_group: form.board_group.trim() || null,
    board_type: form.board_type,
    guest_read_yn: form.guest_read_yn,
    write_yn: form.write_yn,
    comment_yn: form.comment_yn,
    category_yn: form.category_yn,
    attach_yn: form.attach_yn,
    attach_ext: form.attach_yn ? form.attach_ext.trim() : null,
    auto_reply_enabled: form.auto_reply_enabled,
    sort_order: form.sort_order,
    use_yn: form.use_yn,
  };

  if (mode === "create") {
    request.board_code = form.board_code.trim();
  }

  return request;
}
