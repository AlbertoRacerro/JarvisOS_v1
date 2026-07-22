from pathlib import Path

path = Path("backend/tests/test_bluerev_process_topology_m1.py")
text = path.read_text(encoding="utf-8")
old = '''    assert outputs["branch_major_pressure_loss"]["value"] == pytest.approx(major)
    assert outputs["branch_misc_pressure_loss"]["value"] == pytest.approx(minor)
    assert outputs["total_pressure_loss"]["value"] == pytest.approx(total_loss)
'''
new = '''    assert outputs["branch_major_pressure_loss"]["value"] == pytest.approx(major)
    branch_minor = 0.03 * dynamic_pressure
    common_minor = 0.07 * dynamic_pressure
    assert outputs["branch_misc_pressure_loss"]["value"] == pytest.approx(branch_minor)
    assert outputs["common_supply_minor_pressure_loss"]["value"] == pytest.approx(
        0.01 * dynamic_pressure
    )
    assert outputs["split_manifold_pressure_loss"]["value"] == pytest.approx(
        0.02 * dynamic_pressure
    )
    assert outputs["merge_manifold_pressure_loss"]["value"] == pytest.approx(
        0.02 * dynamic_pressure
    )
    assert outputs["common_return_minor_pressure_loss"]["value"] == pytest.approx(
        0.02 * dynamic_pressure
    )
    assert outputs["common_pressure_loss"]["value"] == pytest.approx(common_minor)
    assert outputs["representative_branch_pressure_loss"]["value"] == pytest.approx(
        major + branch_minor
    )
    assert outputs["total_pressure_loss"]["value"] == pytest.approx(total_loss)
'''
if text.count(old) != 1:
    raise SystemExit(f"expected one aggregate-K assertion block, found {text.count(old)}")
path.write_text(text.replace(old, new), encoding="utf-8")
