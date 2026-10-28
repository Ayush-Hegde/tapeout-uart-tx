![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# 8-Bit UART Transmitter (8N1, 9600 baud)

A small [Tiny Tapeout](https://tinytapeout.com) ASIC for the SKY130 process (TTSKY26d shuttle). It takes an 8-bit
parallel byte and sends it out as a standard UART serial frame, so any USB-to-UART adapter or Arduino can receive it.

- **Frame:** 8N1 (1 start bit, 8 data bits LSB first, no parity, 1 stop bit)
- **Clock:** 10 MHz
- **Baud rate:** 9600 (10 MHz / 1042, 0.03% error)
- **Size:** 1x1 tile
- **Layout viewer:** https://ayush-hegde.github.io/tapeout-uart-tx/
- **Datasheet:** [docs/info.md](docs/info.md)

## How it works

| Block | Description |
|---|---|
| Baud counter | 11-bit counter producing a tick every 1042 clocks (one bit period) |
| Control FSM | 4 states: IDLE, START, DATA, STOP |
| Shift register | 8-bit register loaded from `ui_in`, shifted out one bit per baud tick |
| Bit counter | 3-bit counter for the 8 data bits |
| SEND synchronizer | 2-flop synchronizer plus rising-edge detect on the asynchronous SEND pin |

A rising edge on SEND loads the byte and starts a frame. A SEND that arrives during a frame is ignored. Each frame
takes 10 bit periods, about 1.04 ms. The source is in [src/project.v](src/project.v).

## Pinout

| Pin | Direction | Function |
|---|---|---|
| `ui[7:0]` | in | DATA, the byte to send |
| `uio[0]` | in | SEND, a rising edge starts a frame |
| `uo[0]` | out | TX serial line (idles high) |
| `uo[1]` | out | BUSY, high while a frame is being sent |
| `uo[2]` | out | READY, the inverse of BUSY |

All other pins are unused.

## Testing

### Simulation

The cocotb testbench in [test/](test) contains a software UART receiver. It checks the idle level, several bytes
(0x55, 0xA5, 0x00, 0xFF, 0x3C, "Hi"), the frame length, and that SEND is ignored while busy.

```sh
cd test
make -B              # Linux / macOS
python run_local.py  # Windows, no make needed
```

The GitHub Actions workflows run the same tests on the RTL and on the gate-level netlist after hardening.

### On the chip

1. On the Tiny Tapeout demo board, select this project and set the clock to 10 MHz.
2. Connect `uo[0]` (TX) and GND to the RX pin of a 3.3 V USB-UART adapter.
3. Open a serial terminal at 9600 baud, 8N1.
4. Set `ui[7:0]` to a character (for example `0x41` for `A`), then pulse `uio[0]` high and low.
5. The character appears in the terminal.

## Open-source flow

| Step | Tool |
|---|---|
| Simulation | Icarus Verilog + cocotb |
| Synthesis | Yosys + ABC |
| Floorplan, place, CTS, route | OpenROAD (via LibreLane) |
| Static timing | OpenSTA |
| DRC / LVS | Magic / Netgen |
| PDK | SkyWater SKY130 |

## Author

Ayush Hegde, [@Ayush-Hegde](https://github.com/Ayush-Hegde)

Licensed under [Apache 2.0](LICENSE).
