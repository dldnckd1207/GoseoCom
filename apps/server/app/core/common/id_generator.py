"""ID 채번 — PostgreSQL Sequence 기반"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# PREFIX → 시퀀스명 매핑
_SEQ_MAP = {
    "USR_": "seq_usr",
    "OAUTH_": "seq_oauth",
    "UTKN_": "seq_utkn",
    "FILE_": "seq_file",
    "FMAP_": "seq_fmap",
    "BRD_": "seq_brd",
    "BCAT_": "seq_bcat",
    "POST_": "seq_post",
    "CMT_": "seq_cmt",
    "BOOK_": "seq_book",
    "BPAGE_": "seq_bpage",
}


async def next_id(prefix: str, db: AsyncSession) -> str:
    """
    PREFIX에 해당하는 시퀀스에서 다음 번호를 가져와 ID를 생성한다.
    예) next_id("USR_", db) → "USR_00000001"
    """
    seq_name = _SEQ_MAP.get(prefix)
    if not seq_name:
        raise ValueError(f"알 수 없는 ID PREFIX: {prefix}")

    result = await db.execute(text(f"SELECT nextval('{seq_name}')"))
    next_val: int = result.scalar_one()
    return f"{prefix}{next_val:08d}"
