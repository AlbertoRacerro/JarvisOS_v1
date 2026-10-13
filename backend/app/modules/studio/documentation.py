"""Best-effort, parse-only source documentation."""

import ast


def _node(tag: str, *children: dict, text: str | None = None) -> dict:
    return {"tag": tag, "children": list(children)} if children else {"tag": tag, "text": text or ""}


def _math(expression: ast.expr) -> dict:
    if isinstance(expression, ast.Name):
        return _node("mi", text=expression.id)
    if isinstance(expression, ast.Constant) and isinstance(expression.value, (int, float)):
        return _node("mn", text=str(expression.value))
    if isinstance(expression, ast.BinOp):
        symbols = {ast.Add: "+", ast.Sub: "−", ast.Mult: "×", ast.Div: "/", ast.Pow: "^"}
        if type(expression.op) not in symbols:
            raise ValueError("operator is not rendered")
        left, right = _math(expression.left), _math(expression.right)
        if isinstance(expression.op, ast.Div):
            return _node("mfrac", left, right)
        if isinstance(expression.op, ast.Pow):
            return _node("msup", left, right)
        return _node("mrow", left, _node("mo", text=symbols[type(expression.op)]), right)
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.USub):
        return _node("mrow", _node("mo", text="−"), _math(expression.operand))
    raise ValueError("construct is not rendered")


def derive_documentation(source: str, contract: dict) -> dict:
    equations: list[dict] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"equations": [{"function": "source", "target": "syntax", "rendered": False,
                                  "code": source, "reason": f"Syntax error: {exc.msg}"}], **contract}
    for function in (item for item in tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))):
        for statement in function.body:
            target = None
            expression = None
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                target, expression = statement.targets[0].id, statement.value
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                target, expression = statement.target.id, statement.value
            elif isinstance(statement, ast.Return):
                target, expression = "return", statement.value
            elif isinstance(statement, (ast.Expr, ast.Pass)) and (isinstance(statement, ast.Pass) or isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str)):
                continue
            if expression is None:
                continue
            code = ast.get_source_segment(source, statement) or ast.unparse(statement)
            try:
                expression_math = _math(expression)
                math_tree = _node("math", _node("mrow", _node("mi", text=target or "?"),
                                                _node("mo", text="="), expression_math))
                equations.append({"function": function.name, "target": target, "rendered": True,
                                  "math_tree": math_tree, "code": code})
            except ValueError as exc:
                equations.append({"function": function.name, "target": target, "rendered": False,
                                  "code": code, "reason": str(exc)})
    # Import-time statements are inert here, but they must be visible to the operator.
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Import, ast.ImportFrom)):
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
            continue
        equations.append({"function": "module", "target": None, "rendered": False,
                          "code": ast.get_source_segment(source, statement) or ast.unparse(statement),
                          "reason": "module statement is not rendered"})
    return {"equations": equations, **contract}
