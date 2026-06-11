export const USER_LEVELS = [10, 70, 100] as const;

export type ManagedUserLevel = (typeof USER_LEVELS)[number];

export function isSystemAdmin(userLevel: number | undefined) {
  return (userLevel ?? 0) >= 100;
}

export function roleLabel(userLevel: number) {
  if (userLevel >= 100) return "슈퍼관리자";
  if (userLevel >= 70) return "관리자";
  return "사용자";
}

export function canChangeLevel(sessionLevel: number | undefined, isSelf: boolean, isDeleted: boolean) {
  return isSystemAdmin(sessionLevel) && !isSelf && !isDeleted;
}

export function canChangeStatus(
  sessionLevel: number | undefined,
  targetLevel: number,
  isSelf: boolean,
  isDeleted: boolean,
) {
  if (isSelf || isDeleted) return false;
  if (targetLevel >= 100 && !isSystemAdmin(sessionLevel)) return false;
  return true;
}

export function canForceWithdraw(sessionLevel: number | undefined, isSelf: boolean, isDeleted: boolean) {
  return isSystemAdmin(sessionLevel) && !isSelf && !isDeleted;
}
