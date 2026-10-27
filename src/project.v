/*
 * Copyright (c) 2026 Ayush Hegde
 * SPDX-License-Identifier: Apache-2.0
 *
 * 8-bit UART transmitter, 8N1 frame (1 start, 8 data LSB-first, 1 stop).
 * Clock 10 MHz, 9600 baud -> 1042 clocks per bit (0.03% baud error).
 *
 *   ui_in[7:0]  : parallel data byte
 *   uio_in[0]   : SEND - rising edge starts a frame (ignored while busy)
 *   uo_out[0]   : TX serial line (idles high)
 *   uo_out[1]   : BUSY - high while a frame is being sent
 *   uo_out[2]   : READY - inverse of BUSY
 */

`default_nettype none

module tt_um_ayush_hegde_uart_tx (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  localparam [10:0] CLKS_PER_BIT = 11'd1042;  // 10_000_000 / 9600

  localparam [1:0] S_IDLE  = 2'd0,
                   S_START = 2'd1,
                   S_DATA  = 2'd2,
                   S_STOP  = 2'd3;

  reg [1:0]  state;
  reg [10:0] baud_cnt;
  reg [2:0]  bit_idx;
  reg [7:0]  shreg;
  reg        tx;

  // Two-flop synchronizer + rising-edge detect for the asynchronous SEND pin
  reg [2:0] send_sync;
  always @(posedge clk) begin
    if (!rst_n) send_sync <= 3'b000;
    else        send_sync <= {send_sync[1:0], uio_in[0]};
  end
  wire send_rise = send_sync[1] & ~send_sync[2];

  wire baud_tick = (baud_cnt == CLKS_PER_BIT - 11'd1);

  always @(posedge clk) begin
    if (!rst_n) begin
      state    <= S_IDLE;
      baud_cnt <= 11'd0;
      bit_idx  <= 3'd0;
      shreg    <= 8'd0;
      tx       <= 1'b1;
    end else begin
      baud_cnt <= (state == S_IDLE || baud_tick) ? 11'd0 : baud_cnt + 11'd1;

      case (state)
        S_IDLE: begin
          tx <= 1'b1;
          if (send_rise) begin
            shreg <= ui_in;
            tx    <= 1'b0;  // start bit
            state <= S_START;
          end
        end

        S_START: if (baud_tick) begin
          tx      <= shreg[0];
          shreg   <= {1'b0, shreg[7:1]};
          bit_idx <= 3'd0;
          state   <= S_DATA;
        end

        S_DATA: if (baud_tick) begin
          if (bit_idx == 3'd7) begin
            tx    <= 1'b1;  // stop bit
            state <= S_STOP;
          end else begin
            tx      <= shreg[0];
            shreg   <= {1'b0, shreg[7:1]};
            bit_idx <= bit_idx + 3'd1;
          end
        end

        S_STOP: if (baud_tick) state <= S_IDLE;
      endcase
    end
  end

  wire busy = (state != S_IDLE);

  assign uo_out  = {5'b0, ~busy, busy, tx};
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in[7:1], 1'b0};

endmodule
