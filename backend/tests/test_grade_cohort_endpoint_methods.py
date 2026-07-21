from fastapi import FastAPI

from app.modules.ai.routes import router


def test_grade_cohort_endpoint_supports_get_only() -> None:
    app = FastAPI()
    app.include_router(router)
    matching = [
        route
        for route in app.routes
        if getattr(route, "path", None) == "/ai/grade-cohorts"
    ]

    assert len(matching) == 1
    assert getattr(matching[0], "methods", set()) == {"GET"}
