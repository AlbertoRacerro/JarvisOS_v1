from __future__ import annotations

import re
from dataclasses import dataclass
from math import isfinite

from pydantic import BaseModel

Dimension = tuple[int, int, int, int, int]
_ZERO_DIMENSION: Dimension = (0, 0, 0, 0, 0)


class UnitConversionResult(BaseModel):
    compatible: bool
    converted_value: float | None = None
    source_dimension: list[int] | None = None
    target_dimension: list[int] | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class _UnitDefinition:
    scale: float
    dimension: Dimension
    offset: float = 0.0


@dataclass(frozen=True)
class _ParsedUnit:
    scale: float
    dimension: Dimension
    offset: float = 0.0
    offset_atomic: bool = False


class UnitParseError(ValueError):
    pass


_MASS: Dimension = (1, 0, 0, 0, 0)
_LENGTH: Dimension = (0, 1, 0, 0, 0)
_TIME: Dimension = (0, 0, 1, 0, 0)
_AMOUNT: Dimension = (0, 0, 0, 1, 0)
_TEMPERATURE: Dimension = (0, 0, 0, 0, 1)
_PRESSURE: Dimension = (1, -1, -2, 0, 0)
_ENERGY: Dimension = (1, 2, -2, 0, 0)
_POWER: Dimension = (1, 2, -3, 0, 0)
_VOLUME: Dimension = (0, 3, 0, 0, 0)

_UNITS = {
    "1": _UnitDefinition(1.0, _ZERO_DIMENSION),
    "kg": _UnitDefinition(1.0, _MASS),
    "g": _UnitDefinition(1e-3, _MASS),
    "mg": _UnitDefinition(1e-6, _MASS),
    "m": _UnitDefinition(1.0, _LENGTH),
    "cm": _UnitDefinition(1e-2, _LENGTH),
    "mm": _UnitDefinition(1e-3, _LENGTH),
    "um": _UnitDefinition(1e-6, _LENGTH),
    "s": _UnitDefinition(1.0, _TIME),
    "min": _UnitDefinition(60.0, _TIME),
    "h": _UnitDefinition(3600.0, _TIME),
    "mol": _UnitDefinition(1.0, _AMOUNT),
    "mmol": _UnitDefinition(1e-3, _AMOUNT),
    "kmol": _UnitDefinition(1e3, _AMOUNT),
    "K": _UnitDefinition(1.0, _TEMPERATURE),
    "degC": _UnitDefinition(1.0, _TEMPERATURE, 273.15),
    "Pa": _UnitDefinition(1.0, _PRESSURE),
    "kPa": _UnitDefinition(1e3, _PRESSURE),
    "MPa": _UnitDefinition(1e6, _PRESSURE),
    "bar": _UnitDefinition(1e5, _PRESSURE),
    "atm": _UnitDefinition(101325.0, _PRESSURE),
    "mmHg": _UnitDefinition(133.322387415, _PRESSURE),
    "J": _UnitDefinition(1.0, _ENERGY),
    "kJ": _UnitDefinition(1e3, _ENERGY),
    "W": _UnitDefinition(1.0, _POWER),
    "kW": _UnitDefinition(1e3, _POWER),
    "L": _UnitDefinition(1e-3, _VOLUME),
    "mL": _UnitDefinition(1e-6, _VOLUME),
}

_ALIASES = {
    "°C": "degC",
    "celsius": "degC",
    "hour": "h",
    "hours": "h",
    "hr": "h",
    "liter": "L",
    "litre": "L",
    "l": "L",
    "sec": "s",
    "µm": "um",
    "μm": "um",
}
_TOKEN_RE = re.compile(r"\s*([A-Za-zµμ°]+|1|\*|/|\^|\(|\)|[+-]?\d+)\s*")


def _add_dimensions(left: Dimension, right: Dimension) -> Dimension:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _multiply_dimension(dimension: Dimension, exponent: int) -> Dimension:
    return tuple(value * exponent for value in dimension)  # type: ignore[return-value]


def _normalize_expression(expression: str) -> str:
    return (
        expression.strip()
        .replace("·", "*")
        .replace("⋅", "*")
        .replace("²", "^2")
        .replace("³", "^3")
        .replace("⁻¹", "^-1")
    )


def _tokenize(expression: str) -> list[str]:
    normalized = _normalize_expression(expression)
    if not normalized:
        raise UnitParseError("empty_unit")
    tokens: list[str] = []
    position = 0
    while position < len(normalized):
        match = _TOKEN_RE.match(normalized, position)
        if match is None:
            raise UnitParseError("invalid_unit_syntax")
        token = match.group(1)
        tokens.append(_ALIASES.get(token, token))
        position = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens
        self._index = 0

    def parse(self) -> _ParsedUnit:
        parsed = self._parse_expression()
        if self._peek() is not None:
            raise UnitParseError("unexpected_unit_token")
        return parsed

    def _parse_expression(self) -> _ParsedUnit:
        value = self._parse_factor()
        while self._peek() in {"*", "/"}:
            operator = self._consume()
            right = self._parse_factor()
            if value.offset_atomic or right.offset_atomic:
                raise UnitParseError("offset_unit_in_composite")
            if operator == "*":
                value = _ParsedUnit(
                    scale=value.scale * right.scale,
                    dimension=_add_dimensions(value.dimension, right.dimension),
                )
            else:
                value = _ParsedUnit(
                    scale=value.scale / right.scale,
                    dimension=_add_dimensions(
                        value.dimension, _multiply_dimension(right.dimension, -1)
                    ),
                )
        return value

    def _parse_factor(self) -> _ParsedUnit:
        token = self._consume()
        if token == "(":
            value = self._parse_expression()
            if self._consume() != ")":
                raise UnitParseError("unclosed_unit_group")
        else:
            definition = _UNITS.get(token)
            if definition is None:
                raise UnitParseError("unknown_unit")
            value = _ParsedUnit(
                scale=definition.scale,
                dimension=definition.dimension,
                offset=definition.offset,
                offset_atomic=definition.offset != 0.0,
            )

        if self._peek() == "^":
            self._consume()
            exponent_token = self._consume()
            try:
                exponent = int(exponent_token)
            except ValueError as exc:
                raise UnitParseError("invalid_unit_exponent") from exc
            if value.offset_atomic and exponent != 1:
                raise UnitParseError("offset_unit_power")
            value = _ParsedUnit(
                scale=value.scale**exponent,
                dimension=_multiply_dimension(value.dimension, exponent),
                offset=value.offset if exponent == 1 else 0.0,
                offset_atomic=value.offset_atomic and exponent == 1,
            )
        return value

    def _peek(self) -> str | None:
        if self._index >= len(self._tokens):
            return None
        return self._tokens[self._index]

    def _consume(self) -> str:
        token = self._peek()
        if token is None:
            raise UnitParseError("unexpected_end_of_unit")
        self._index += 1
        return token


def _parse_unit(expression: str) -> _ParsedUnit:
    return _Parser(_tokenize(expression)).parse()


def convert_unit(
    value: float, source_unit: str, target_unit: str
) -> UnitConversionResult:
    if not isfinite(value):
        return UnitConversionResult(compatible=False, error_code="non_finite_value")
    try:
        source = _parse_unit(source_unit)
        target = _parse_unit(target_unit)
    except UnitParseError as exc:
        return UnitConversionResult(compatible=False, error_code=str(exc))

    if source.dimension != target.dimension:
        return UnitConversionResult(
            compatible=False,
            source_dimension=list(source.dimension),
            target_dimension=list(target.dimension),
            error_code="incompatible_dimensions",
        )
    if (source.offset_atomic or target.offset_atomic) and not (
        source.dimension == _TEMPERATURE and target.dimension == _TEMPERATURE
    ):
        return UnitConversionResult(
            compatible=False,
            source_dimension=list(source.dimension),
            target_dimension=list(target.dimension),
            error_code="unsupported_offset_conversion",
        )

    si_value = value * source.scale + source.offset
    converted = (si_value - target.offset) / target.scale
    return UnitConversionResult(
        compatible=True,
        converted_value=converted,
        source_dimension=list(source.dimension),
        target_dimension=list(target.dimension),
    )
