// AIPP FPGA Implementation Proof
// Target: Xilinx UltraScale+ / Intel Stratix 10
// Objective: Prove cycle-accurate 14us lead-time orchestration

module aipp_fpga_trigger (
    input wire clk,           // 1GHz (1ns period)
    input wire rst_n,
    input wire packet_detect, // From MAC/Parser
    input wire [31:0] delay_ns,
    output reg vrm_trigger,
    output reg data_release
);

    reg [31:0] counter;
    reg active;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 0;
            vrm_trigger <= 0;
            data_release <= 0;
            active <= 0;
        end else begin
            if (packet_detect && !active) begin
                vrm_trigger <= 1'b1; // Trigger VRM IMMEDIATELY
                counter <= delay_ns;
                active <= 1'b1;
            end else if (active) begin
                if (counter > 1) begin
                    counter <= counter - 1;
                    vrm_trigger <= 1'b0; // Pulse duration check
                end else begin
                    data_release <= 1'b1; // Release packet after delay
                    active <= 1'b0;
                end
            end else begin
                data_release <= 1'b0;
            end
        end
    end
endmodule



