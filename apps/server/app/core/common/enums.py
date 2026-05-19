from enum import Enum


class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class OcrEngine(str, Enum):
    GOOGLE_VISION = "google_vision"
    PADDLE_OCR = "paddle_ocr"


class TranslatorEngine(str, Enum):
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


class FileStorage(str, Enum):
    LOCAL = "local"
    S3 = "s3"


class UserRole(int, Enum):
    GUEST = 0
    USER = 10
    ADMIN = 70
    SYSTEM_ADMIN = 100


class OAuthProvider(str, Enum):
    GOOGLE = "GOOGLE"
    KAKAO = "KAKAO"


class LoginResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


class BoardType(str, Enum):
    LIST = "LIST"
    IMAGE = "IMAGE"
    QNA = "QNA"


class AutoReplyStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class BookType(str, Enum):
    QUICK = "QUICK"
    USER_CREATED = "USER_CREATED"


class SourceType(str, Enum):
    IMAGE = "IMAGE"
    PDF = "PDF"


class BookStatus(str, Enum):
    PENDING = "PENDING"
    OCR_PROCESSING = "OCR_PROCESSING"
    TRANSLATING = "TRANSLATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineTriggerType(str, Enum):
    TRANSLATOR = "TRANSLATOR"
    AUTO_REPLY = "AUTO_REPLY"


class PipelineStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class FileTargetType(str, Enum):
    POST = "POST"
    COMMENT = "COMMENT"
    BOOK = "BOOK"


class FileGroup(str, Enum):
    THUMBNAIL = "thumbnail"
    ATTACHMENT = "attachment"
    ORIGINAL = "original"
