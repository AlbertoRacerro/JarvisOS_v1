from app.modules.memory import jarvis_knowledge_actions as knowledge


def test_secret_screen_reuses_canonical_floor_for_jwt() -> None:
    jwt = (
        "eyJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiJ1c2VyLTEyMyJ9."
        "c2lnbmF0dXJlMTIzNDU2"
    )

    assert knowledge._contains_secret_material([{"intent": f"Use {jwt} to clarify this requirement"}])
