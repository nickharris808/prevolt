/*
 * AIPP Core: AI Power Protocol Control Engine
 * ===========================================
 * Synthesizable RTL for the GPOP/AIPP Silicon Block.
 *
 * This module implements the line-rate telemetry parser and 
 * rate-limiter control logic. It is optimized for 7nm standard cell
 * implementation.
 */

module aipp_core (
    input  wire        clk,
    input  wire        rst_n,
    
    // Telemetry Input (from Header Parser)
    input  wire [3:0]  v_health,      // 4-bit Quantized Voltage Health
    input  wire        telemetry_vld,
    
    // Config Registers
    input  wire [7:0]  throttle_threshold,
    input  wire [7:0]  recovery_target,
    
    // Rate Limiter Control Output
    output reg  [15:0] rate_limit_bps, // Bits-per-cycle limit
    output reg         intr_alert      // Interrupt for OVP/OTP
);

    // Internal State
    reg [1:0] state;
    localparam IDLE     = 2'b00;
    localparam NOMINAL  = 2'b01;
    localparam THROTTLE = 2'b10;
    localparam ALERT    = 2'b11;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            rate_limit_bps <= 16'hFFFF; // Max rate
            intr_alert <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    if (telemetry_vld) state <= NOMINAL;
                end
                
                NOMINAL: begin
                    if (v_health < 4'd8) begin // If health < 50%
                        state <= THROTTLE;
                        rate_limit_bps <= 16'h4000; // 25% Throttle
                    end
                end
                
                THROTTLE: begin
                    if (v_health > 4'd12) begin // Recovered
                        state <= NOMINAL;
                        rate_limit_bps <= 16'hFFFF;
                    end
                    if (v_health < 4'd2) begin // Critical drop
                        state <= ALERT;
                        intr_alert <= 1'b1;
                    end
                end
                
                ALERT: begin
                    rate_limit_bps <= 16'h0000; // Full stop
                    if (v_health > 4'd4) begin
                        state <= THROTTLE;
                        intr_alert <= 1'b0;
                    end
                end
            endcase
        end
    end

endmodule

