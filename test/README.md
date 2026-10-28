# Testbench for the 8-bit UART transmitter

This testbench uses [cocotb](https://docs.cocotb.org/en/stable/) to drive `tt_um_ayush_hegde_uart_tx` through
[tb.v](tb.v). [test.py](test.py) contains a software UART receiver that decodes the TX pin (`uo_out[0]`) and checks:

| Test | What it checks |
|---|---|
| `test_idle_state` | TX idles high, BUSY low, READY high, and changing the data without SEND does nothing |
| `test_send_bytes` | 0x55, 0xA5, 0x00, 0xFF, 0x3C, `H` and `i` are received correctly |
| `test_frame_timing` | One 8N1 frame lasts 10 bit periods (10 x 1042 clocks) |
| `test_send_ignored_while_busy` | A SEND during a frame does not corrupt the frame |

The clock is 10 MHz (100 ns period), so one byte takes about 1.04 ms of simulated time.

## Setting up

```sh
pip install -r requirements.txt
```

You also need [Icarus Verilog](https://steveicarus.github.io/iverilog/) on your PATH.

## How to run

To run the RTL simulation on Linux or macOS:

```sh
make -B
```

On Windows, or anywhere without `make`, use the cocotb Python runner instead:

```sh
python run_local.py
```

Both print `TESTS=4 PASS=4 FAIL=0` when everything passes.

## Gate-level simulation

The `gl_test` job in the gds GitHub workflow runs these same tests on the hardened netlist after every push.

To run it locally, you need the SKY130 PDK (set `PDK_ROOT`). Copy the gate-level netlist produced by hardening to
`gate_level_netlist.v` in this folder, then run:

```sh
make -B GATES=yes
```

## How to view the waveform file

Each run writes `tb.fst` in this folder. Add `clk`, `ui_in`, `uio_in` and `uo_out` to see the frames on `uo_out[0]`.

Using GTKWave:

```sh
gtkwave tb.fst tb.gtkw
```

Using Surfer:

```sh
surfer tb.fst
```

You can also drag `tb.fst` onto [app.surfer-project.org](https://app.surfer-project.org) in a browser.

To save VCD instead of FST, edit tb.v to use `$dumpfile("tb.vcd");` and run `make -B FST=`.
