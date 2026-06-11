export interface AdminUser {
  user_id: string;
  email: string;
  name: string;
  profile_image_url: string | null;
  user_level: number;
}

export type AdminUserRoleFilter = "all" | "user" | "admin" | "system_admin";

export interface AdminUserListRequest {
  keyword?: string | null;
  role: AdminUserRoleFilter;
  use_yn?: boolean | null;
  block_yn?: boolean | null;
  include_deleted: boolean;
  page: number;
  size: number;
}

export interface AdminUserListItem {
  id: string;
  email: string;
  name: string;
  profile_image_url: string | null;
  user_level: number;
  role_label: string;
  use_yn: boolean;
  block_yn: boolean;
  joined_at: string;
  last_login_at: string | null;
  left_at: string | null;
  del_yn: boolean;
  is_self: boolean;
}

export interface AdminUserDetail extends AdminUserListItem {
  blocked_at: string | null;
  blocked_by: string | null;
  left_reason: string | null;
}

export interface AdminUserUpdateRequest {
  user_level?: 10 | 70 | 100;
  use_yn?: boolean;
  block_yn?: boolean;
}

export interface AdminUserForceWithdrawRequest {
  left_reason: string;
}
