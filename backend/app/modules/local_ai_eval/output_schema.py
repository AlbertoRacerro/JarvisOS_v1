from app.modules.local_ai_eval.models import GemmaEvalOutput


def gemma_eval_output_json_schema() -> dict[str, object]:
    """Return the future local Gemma structured-output schema."""

    return GemmaEvalOutput.model_json_schema()
