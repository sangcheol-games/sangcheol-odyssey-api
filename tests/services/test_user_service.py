import pytest

from app.services.user_service import (
    _gen_numeric_uid,
    UID_MIN,
    UID_MAX,
    UserService,
)
from app.core.error import SCDomainError, DomainErrorCode


def test_gen_numeric_uid_in_range():
    for _ in range(100):
        uid = _gen_numeric_uid()
        assert uid.isdigit()
        num = int(uid)
        assert UID_MIN <= num <= UID_MAX
        assert 9 <= len(uid) <= 10


def test_validate_nickname_strips_and_returns():
    assert UserService._validate_nickname("  Nick_123  ") == "Nick_123"


@pytest.mark.parametrize(
    "good_nickname",
    [
        "하츠네미쿠",          # 한글
        "みく",               # 히라가나
        "ミク",               # 가타카나
        "初音ミク",           # 한자 + 가타카나
        "Ｍｉｋｕ".replace("Ｍ","M").replace("ｉ","i").replace("ｋ","k").replace("ｕ","u"),  # 반각 처리 가정 X → 영문만 테스트
        "Miku_39",           # 영문 + 숫자 + _
        "miku.39",           # .
        "miku-39",           # -
        "みく_39",           # 일+기호
        "初音ミク39",         # 일+숫자
        "가나カナkana123._-", # 혼합 + 허용기호
        "一二三四五六七八九十",  # CJK 한자 10자
        "ミクミクミクミクミク",  # 10자
        "ab",                # 경계: 최소 길이 2
        "x" * 16,            # 경계: 최대 길이 16
    ],
)
def test_validate_nickname_valid_cases(good_nickname):
    assert UserService._validate_nickname(good_nickname) == good_nickname


@pytest.mark.parametrize(
    "bad_nickname",
    [
        "",
        " ",
        "a",                 # 1자(최소 미만)
        "ミ",                 # 1자(최소 미만, 일본어)
        "x" * 17,            # 17자(최대 초과)
        "bad nickname",      # 공백 포함
        "nick!",             # 허용되지 않는 특수문자
        "　",                # 전각 공백(스페이스)만
        ".",
        "-",
        "_",                 # 길이 미달(기호만 1자)
    ],
)
def test_validate_nickname_invalid(bad_nickname):
    with pytest.raises(SCDomainError) as exc:
        UserService._validate_nickname(bad_nickname)
    assert exc.value.code == DomainErrorCode.INVALID_NICKNAME
