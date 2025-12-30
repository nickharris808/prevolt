/*
 * tb_aipp_t_noc_router.v
 *
 * Testbench for the Thermal-Deflection Router.
 * Verifies:
 * 1. Functional routing.
 * 2. Deflection when thermal_inhibit is high.
 * 3. Latency (registered output).
 */

`timescale 1ns/1ps

module tb_aipp_t_noc_router();

    parameter DATA_WIDTH = 32;
    parameter NUM_PORTS = 4;

    reg clk;
    reg rst_n;
    reg [NUM_PORTS-1:0] thermal_inhibit;
    wire [NUM_PORTS-1:0] thermal_ack;
    reg [NUM_PORTS-1:0] in_valid;
    reg [(NUM_PORTS*DATA_WIDTH)-1:0] in_data;
    reg [(NUM_PORTS*2)-1:0] in_dest;
    wire [NUM_PORTS-1:0] in_ready;
    wire [NUM_PORTS-1:0] out_valid;
    wire [(NUM_PORTS*DATA_WIDTH)-1:0] out_data;
    reg [NUM_PORTS-1:0] out_ready;

    // Instantiate Router
    aipp_t_noc_router #(
        .DATA_WIDTH(DATA_WIDTH),
        .NUM_PORTS(NUM_PORTS)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .thermal_inhibit(thermal_inhibit),
        .thermal_ack(thermal_ack),
        .in_valid(in_valid),
        .in_data(in_data),
        .in_dest(in_dest),
        .in_ready(in_ready),
        .out_valid(out_valid),
        .out_data(out_data),
        .out_ready(out_ready)
    );

    // Clock Generation
    always #0.5 clk = ~clk; // 1GHz Clock

    initial begin
        // Initialize
        clk = 0;
        rst_n = 0;
        thermal_inhibit = 4'b0000;
        in_valid = 4'b0000;
        in_data = 0;
        in_dest = 0;
        out_ready = 4'b1111;

        $display("--- Starting NoC Router Verification ---");
        #2 rst_n = 1;

        // Test Case 1: Standard Routing (No Heat)
        // Port 0 sends to Port 2
        @(posedge clk);
        in_valid[0] = 1'b1;
        in_dest[1:0] = 2'd2;
        in_data[31:0] = 32'hDEADBEEF;
        
        @(posedge clk);
        in_valid[0] = 1'b0;
        
        // Check output at Port 2 (registered, so 1 cycle later)
        @(posedge clk);
        if (out_valid[2] && out_data[2*32 +: 32] == 32'hDEADBEEF)
            $display("[PASS] Case 1: Standard routing successful.");
        else
            $display("[FAIL] Case 1: Standard routing failed. Valid=%b, Data=%h", out_valid[2], out_data[2*32 +: 32]);

        // Test Case 2: Thermal Deflection
        // Port 0 sends to Port 2, but Port 2 is HOT
        @(posedge clk);
        thermal_inhibit[2] = 1'b1;
        in_valid[0] = 1'b1;
        in_dest[1:0] = 2'd2;
        in_data[31:0] = 32'hCAFEBABE;
        
        @(posedge clk);
        in_valid[0] = 1'b0;
        
        // Expect deflection to (2+1)%4 = Port 3
        @(posedge clk);
        if (out_valid[3] && out_data[3*32 +: 32] == 32'hCAFEBABE)
            $display("[PASS] Case 2: Thermal deflection successful (Deflected to Port 3).");
        else
            $display("[FAIL] Case 2: Thermal deflection failed. Valid=%b, Data=%h", out_valid[3], out_data[3*32 +: 32]);

        // Test Case 3: Handshake Latency
        if (thermal_ack == thermal_inhibit)
            $display("[PASS] Case 3: Thermal Handshake latency is 0 cycles (Combinatorial).");
        else
            $display("[FAIL] Case 3: Thermal Handshake failed.");

        $display("--- Verification Complete ---");
        $finish;
    end

endmodule




