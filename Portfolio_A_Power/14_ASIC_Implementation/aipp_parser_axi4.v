// AIPP Parser with AXI4-Stream Interface Wrapper
// File: /14_ASIC_Implementation/aipp_parser_axi4.v
//
// Purpose:
// Industry-standard AXI4-Stream wrapper for AIPP Header Parser.
// Provides plug-and-play integration into Broadcom/Nvidia SoC fabrics.
//
// Interface Compliance:
// - AXI4-Stream (AMBA standard)
// - Ready/Valid handshake for backpressure
// - TDATA/TVALID/TREADY/TLAST signals

module aipp_parser_axi4 (
    input wire aclk,
    input wire aresetn,
    
    // AXI4-Stream Slave (Input from Switch Pipeline)
    input wire [127:0] s_axis_tdata,     // 128-bit AIPP header
    input wire s_axis_tvalid,            // Valid signal
    output reg s_axis_tready,            // Ready (backpressure)
    input wire s_axis_tlast,             // Last beat (packet end)
    
    // Decoded Outputs
    output reg [31:0] delay_us,          // Extracted delay
    output reg [31:0] voltage_mv,        // Extracted voltage
    output reg trigger_out,              // Signal to VRM
    output reg valid_out                 // Output valid
);

    // Internal state
    reg [2:0] state;
    localparam IDLE = 3'b000;
    localparam PARSE = 3'b001;
    localparam OUTPUT = 3'b010;
    
    // Parsed fields
    reg [7:0] opcode;
    reg [31:0] delay_field;
    reg [31:0] voltage_field;
    
    // AXI4-Stream Ready/Valid Handshake
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            s_axis_tready <= 1'b1;   // Ready to accept
            delay_us <= 32'b0;
            voltage_mv <= 32'b0;
            trigger_out <= 1'b0;
            valid_out <= 1'b0;
            state <= IDLE;
        end else begin
            case (state)
                IDLE: begin
                    if (s_axis_tvalid && s_axis_tready) begin
                        // Parse header fields (parallel extraction)
                        opcode <= s_axis_tdata[7:0];
                        delay_field <= s_axis_tdata[39:8];
                        voltage_field <= s_axis_tdata[71:40];
                        state <= PARSE;
                        s_axis_tready <= 1'b0; // Stall while parsing
                    end
                end
                
                PARSE: begin
                    // OpCode Check: 0x10 is Pre-charge
                    if (opcode == 8'h10) begin
                        delay_us <= delay_field;
                        voltage_mv <= voltage_field;
                        trigger_out <= 1'b1;
                        valid_out <= 1'b1;
                    end
                    state <= OUTPUT;
                end
                
                OUTPUT: begin
                    // Hold outputs for 1 cycle, then return to IDLE
                    trigger_out <= 1'b0;
                    valid_out <= 1'b0;
                    s_axis_tready <= 1'b1;
                    state <= IDLE;
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule

// Integration Notes:
// 1. This module is a standard AXI4-Stream slave.
// 2. It can be instantiated in any AMBA-compatible SoC.
// 3. Backpressure (s_axis_tready) prevents packet loss during parse.
// 4. Total latency: 3 clock cycles (IDLE → PARSE → OUTPUT).
//
// Timing: @ 1GHz, 3 cycles = 3ns total latency (still sub-microsecond).




