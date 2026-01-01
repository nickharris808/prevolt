"""
Generate Figure 7: Verilog Code Rendering
"""
import matplotlib.pyplot as plt

def generate_fig_7_verilog():
    code = """
module aipp_fpga_trigger (
    input wire clk,
    input wire rst_n,
    input wire packet_detect,
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
                vrm_trigger <= 1'b1; // IMMEDIATE TRIGGER
                counter <= delay_ns;
                active <= 1'b1;
            end else if (active) begin
                if (counter > 1) begin
                    counter <= counter - 1;
                    vrm_trigger <= 1'b0;
                end else begin
                    data_release <= 1'b1; // DELAYED RELEASE
                    active <= 1'b0;
                end
            end
        end
    end
endmodule
"""
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.axis('off')
    ax.text(0.05, 0.95, code, family='monospace', fontsize=12, va='top')
    ax.set_title("Figure 7: FPGA Trigger Logic (Verilog RTL)")
    
    plt.savefig('patents/figures/FIG_7_VERILOG_RTL.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_7_VERILOG_RTL.png")

if __name__ == "__main__":
    generate_fig_7_verilog()
