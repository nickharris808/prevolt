/*
 * AIPP Packet Header Parser (RTL Logic)
 * =====================================
 * This module implements the line-rate hardware trigger.
 * It is designed to run at 1GHz (1ns clock cycle).
 */

module aipp_parser (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [63:0] packet_data,
    input  wire        data_valid,
    output reg         gpop_trigger,
    output reg  [7:0]  cycle_count
);

    // OpCode for AIPP 'Heavy Job' is 0xBEFF
    localparam bit [15:0] AIPP_OPCODE = 16'hBEFF;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gpop_trigger <= 1'b0;
            cycle_count  <= 8'd0;
        end else if (data_valid) begin
            // Parse logic (8-cycle pipeline for deep inspection)
            if (packet_data[15:0] == AIPP_OPCODE) begin
                if (cycle_count == 8'd8) begin
                    gpop_trigger <= 1'b1;
                end else begin
                    cycle_count <= cycle_count + 8'd1;
                end
            end else begin
                gpop_trigger <= 1'b0;
                cycle_count  <= 8'd0;
            end
        end else begin
            gpop_trigger <= 1'b0;
            cycle_count  <= 8'd0;
        end
    end

endmodule




