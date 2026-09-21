from errors import format_user_error


def test_value_error_is_safe_to_show():
    assert format_user_error(ValueError("业务规则错误")) == "业务规则错误"


def test_unknown_error_points_to_log():
    message = format_user_error(RuntimeError("secret technical detail"))
    assert "logs/app.log" in message
    assert "secret technical detail" not in message
