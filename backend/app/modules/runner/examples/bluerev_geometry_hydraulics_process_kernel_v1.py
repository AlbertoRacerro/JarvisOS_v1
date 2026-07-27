import json
import math

from process_kernel.profile_047 import EXPECTED_UNITS, ProcessKernelError, execute_047_process_kernel


def fail(reason, field_name=None):
    message = "bluerev_calc_error:" + reason
    if field_name is not None:
        message += ":" + field_name
    raise SystemExit(message)


with open("input.json", encoding="utf-8") as handle:
    inputs = json.load(handle)

if not isinstance(inputs, dict) or set(inputs) != set(EXPECTED_UNITS):
    fail("input_contract_invalid")

values = {}
for name, expected_unit in EXPECTED_UNITS.items():
    item = inputs.get(name)
    if not isinstance(item, dict):
        fail("input_contract_invalid", name)
    allowed_keys = {"value", "unit", "source_parameter_id"}
    if "value" not in item or "unit" not in item or not set(item).issubset(allowed_keys):
        fail("input_contract_invalid", name)
    value = item["value"]
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        fail("input_contract_invalid", name)
    if item["unit"] != expected_unit:
        fail("input_unit_invalid", name)
    values[name] = float(value)

try:
    result = execute_047_process_kernel(values)
except ProcessKernelError as exc:
    fail(exc.code)

with open("result.json", "w", encoding="utf-8") as handle:
    json.dump(result, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
