# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

CLK_HZ = 10_000_000
BAUD = 9600
CLKS_PER_BIT = 1042  # must match CLKS_PER_BIT in src/project.v


def tx(dut):
    return int(dut.uo_out.value) & 1


def busy(dut):
    return (int(dut.uo_out.value) >> 1) & 1


def ready(dut):
    return (int(dut.uo_out.value) >> 2) & 1


async def reset(dut):
    clock = Clock(dut.clk, 100, unit="ns")  # 10 MHz
    cocotb.start_soon(clock.start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)


async def uart_receive(dut):
    """Software UART receiver: waits for a start bit, samples each bit mid-period."""
    while tx(dut) == 1:
        await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, CLKS_PER_BIT // 2)
    assert tx(dut) == 0, "start bit not held low"
    value = 0
    for i in range(8):
        await ClockCycles(dut.clk, CLKS_PER_BIT)
        value |= tx(dut) << i
    await ClockCycles(dut.clk, CLKS_PER_BIT)
    assert tx(dut) == 1, "stop bit not high"
    return value


async def send_byte(dut, value):
    dut.ui_in.value = value
    dut.uio_in.value = 1  # SEND pulse
    await ClockCycles(dut.clk, 5)
    dut.uio_in.value = 0


async def wait_idle(dut):
    while busy(dut):
        await RisingEdge(dut.clk)


@cocotb.test()
async def test_idle_state(dut):
    await reset(dut)
    assert tx(dut) == 1, "TX must idle high"
    assert busy(dut) == 0 and ready(dut) == 1
    # Changing data without SEND must not start a frame
    dut.ui_in.value = 0xA5
    await ClockCycles(dut.clk, 3 * CLKS_PER_BIT)
    assert tx(dut) == 1 and busy(dut) == 0


@cocotb.test()
async def test_send_bytes(dut):
    await reset(dut)
    for value in [0x55, 0xA5, 0x00, 0xFF, 0x3C, ord("H"), ord("i")]:
        rx = cocotb.start_soon(uart_receive(dut))
        await send_byte(dut, value)
        await ClockCycles(dut.clk, 5)
        assert busy(dut) == 1 and ready(dut) == 0
        got = await rx
        dut._log.info(f"sent 0x{value:02X} received 0x{got:02X}")
        assert got == value
        await wait_idle(dut)
        assert tx(dut) == 1


@cocotb.test()
async def test_frame_timing(dut):
    """A full 8N1 frame must take 10 bit periods."""
    await reset(dut)
    await send_byte(dut, 0x00)
    while not busy(dut):
        await RisingEdge(dut.clk)
    cycles = 0
    while busy(dut):
        await RisingEdge(dut.clk)
        cycles += 1
    assert abs(cycles - 10 * CLKS_PER_BIT) <= 2, f"frame took {cycles} cycles"


@cocotb.test()
async def test_send_ignored_while_busy(dut):
    await reset(dut)
    rx = cocotb.start_soon(uart_receive(dut))
    await send_byte(dut, 0x81)
    await ClockCycles(dut.clk, 3 * CLKS_PER_BIT)
    # New data + SEND in the middle of a frame must not corrupt it
    await send_byte(dut, 0x7E)
    assert await rx == 0x81
    await wait_idle(dut)
    await ClockCycles(dut.clk, 2 * CLKS_PER_BIT)
    assert tx(dut) == 1 and busy(dut) == 0
