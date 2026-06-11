import { ShieldAlert } from "lucide-react";

import { isSystemAdmin } from "~/features/users/lib/userRole";

interface UserPermissionNoticeProps {
  userLevel: number | undefined;
}

export function UserPermissionNotice({ userLevel }: UserPermissionNoticeProps) {
  const systemAdmin = isSystemAdmin(userLevel);

  return (
    <section className="rounded-md border border-border bg-card p-4">
      <div className="flex items-start gap-3">
        <div className="flex size-9 items-center justify-center rounded-full bg-secondary text-muted-foreground">
          <ShieldAlert className="size-4" />
        </div>
        <div>
          <h2 className="text-sm font-medium">권한 안내</h2>
          <div className="mt-2 space-y-1 text-sm text-muted-foreground">
            {systemAdmin ? (
              <>
                <p>권한 변경과 강제 탈퇴가 가능합니다.</p>
                <p>본인 계정은 보호되어 변경할 수 없습니다.</p>
              </>
            ) : (
              <>
                <p>사용/미사용, 차단/해제만 가능합니다.</p>
                <p>권한 변경과 강제 탈퇴는 슈퍼관리자만 가능합니다.</p>
                <p>본인 계정은 보호되어 변경할 수 없습니다.</p>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
