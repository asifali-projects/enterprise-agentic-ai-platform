from uuid import uuid4

from app.core.security import create_token, decode_token


def test_token():
    u, o = uuid4(), uuid4()
    p = decode_token(create_token(u, o, "owner"))
    assert p["sub"] == str(u) and p["org"] == str(o)
