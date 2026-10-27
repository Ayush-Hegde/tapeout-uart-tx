# Run the cocotb tests without `make` (handy on Windows).
# Usage (from the test folder):  python run_local.py
from pathlib import Path

from cocotb_tools.runner import get_runner

here = Path(__file__).resolve().parent
src = here.parent / "src"

runner = get_runner("icarus")
runner.build(
    sources=[src / "project.v", here / "tb.v"],
    hdl_toplevel="tb",
    includes=[src],
    build_dir=here / "sim_build" / "rtl",
    always=True,
)
runner.test(hdl_toplevel="tb", test_module="test", test_dir=here, waves=True)
