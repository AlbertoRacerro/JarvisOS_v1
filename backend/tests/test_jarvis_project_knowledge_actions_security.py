from app.modules.memory import jarvis_knowledge_actions as knowledge


def test_secret_screen_reuses_canonical_floor_for_jwt() -> None:
    jwt = (
        "eyJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiJ1c2VyLTEyMyJ9."
        "c2lnbmF0dXJlMTIzNDU2"
    )

    assert knowledge._contains_secret_material([{"intent": f"Use {jwt} to clarify this requirement"}])


def test_secret_screen_blocks_standard_tokens_and_credential_urls() -> None:
    sensitive_values = [
        "xoxb-1234567890-abcdefghijklmnop",
        "github_pat_11AA22BB33CC44DD55EE66FF77GG88HH99",
        "postgresql://jarvis:supersecretpassword@db.internal/jarvis",
        "sk_live_abcdefghijklmnop",
        "glpat-abcdefghijklmnop",
        "npm_abcdefghijklmnop",
        "AIzaabcdefghijklmnopqrstuv",
        "Authorization: Basic YWxhZGRpbjpvcGVuc2VzYW1l",
    ]

    for value in sensitive_values:
        assert knowledge._contains_secret_material([{"content": value}])
