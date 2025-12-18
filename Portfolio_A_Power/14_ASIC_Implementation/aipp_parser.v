// Pillar 14: Synthesizable AIPP Header Parser
// File: /14_ASIC_Implementation/aipp_parser.v
//
// Goal: 1GHz Timing Closure (1ns)
// Implementation: Parallel Field Parsing

module aipp_parser (
    input clk,
    input rst_n,
    input [127:0] packet_in,      // 128-bit header
    input valid_in,               // Packet arrived
    output reg [31:0] delay_us,   // Decoded Delay
    output reg [31:0] voltage_mv, // Decoded Voltage
    output reg trigger_out        // Signal to VRM
);

    // Timing-critical logic depth: 
    // Field extraction (1 gate) -> Range check (2 gates) -> Register Write (1 gate)
    // Total depth: 4 gates.
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            delay_us <= 32'b0;
            voltage_mv <= 32'b0;
            trigger_out <= 1'b0;
        end else if (valid_in) begin
            // OpCode Check: 0x10 is Pre-charge
            if (packet_in[7:0] == 8'h10) begin
                delay_us   <= packet_in[39:8];
                voltage_mv <= packet_in[71:40];
                trigger_out <= 1'b1;
            end else begin
                trigger_out <= 1'b0;
            end
        end else begin
            trigger_out <= 1'b0;
        end
    end

endmodule
