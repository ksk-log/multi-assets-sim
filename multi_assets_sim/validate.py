import re

FLOAT_PATTERN = re.compile(r"^[+-]?\d+\.?\d*$")
INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
PERCENTILE_PATTERN = re.compile(r"^(\d+,)+\d$")


def _validate_int_digits(s: str) -> bool:
    """入力が整数値になっているか検証する

    Args:
        s (str): 検証対象の文字列

    Returns:
        bool: 数値ならTrue,そうでなければFalse
    """
    res = INTEGER_PATTERN.match(s)
    if res is None:
        return False
    else:
        True


def textfield_int_changed(e):
    """TextFieldの入力が整数値か確かめてエラーテキストを表示する関数

    Args:
        e (_type_): _description_
    """
    if _validate_int_digits(e.control.value) is False:
        e.control.error_text = "整数値を入力してください!"
        e.control.update()
    else:
        e.control.error_text = None
        e.control.update()


def _validate_float_digits(s: str) -> bool:
    """入力が浮動点小数値になっているか検証する

    Args:
        s (str): 検証対象の文字列

    Returns:
        bool: 数値ならTrue,そうでなければFalse
    """
    res = FLOAT_PATTERN.match(s)
    if res is None:
        return False
    else:
        True


def textfield_float_changed(e):
    """TextFieldの入力が浮動点小数値か確かめてエラーテキストを表示する関数

    Args:
        e (_type_): _description_
    """
    if _validate_float_digits(e.control.value) is False:
        e.control.error_text = "小数値を入力してください!"
        e.control.update()
    else:
        e.control.error_text = None
        e.control.update()


def _validate_percentile_digits(s: str) -> bool:
    """入力がパーセンタイルのリストになっているか検証する

    Args:
        s (str): 検証対象の文字列

    Returns:
        bool: 数値ならTrue,そうでなければFalse
    """
    res = PERCENTILE_PATTERN.match(s)
    if res is None:
        return False
    else:
        True


def textfield_percentile_changed(e):
    """TextFieldの入力がパーセンタイルのリストか確かめてエラーテキストを表示する関数

    Args:
        e (_type_): _description_
    """
    if _validate_percentile_digits(e.control.value) is False:
        e.control.error_text = "整数値のリストを入力してください!"
        e.control.update()
    else:
        e.control.error_text = None
        e.control.update()
