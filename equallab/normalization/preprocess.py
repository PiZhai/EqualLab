import re
import unicodedata


_SPACE_RE = re.compile(r"\s+", re.UNICODE)


def preprocess_text(text: str) -> str:
    """
    文本基础预处理：
    - Unicode NFKC 归一
    - 统一换行与空白压缩
    - 常见全角到半角
    - 替换常见 Unicode 符号为 ASCII: ×→*, ÷→/，“·/•”→·或省略
    """
    if not text:
        return ""

    s = unicodedata.normalize("NFKC", text)

    # 常见符号替换
    replacements = {
        "×": "*",
        "⋅": "*",
        "·": "*",
        "•": "*",
        "÷": "/",
        "−": "-",
        "—": "-",
        "–": "-",
        "，": ",",
        "；": ";",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)

    # 空白规范
    s = _SPACE_RE.sub(" ", s).strip()
    return s


