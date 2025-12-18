/*
 * In-Band Telemetry Switch Logic (P4_16)
 * =======================================
 * 
 * This P4 program implements power-aware traffic throttling based on
 * voltage telemetry embedded in TCP option headers.
 * 
 * The Innovation:
 * - GPU embeds real-time voltage readings in a custom TCP option (0x1A)
 * - Switch parses this option and extracts voltage value
 * - Token bucket meter rate is adjusted based on voltage health
 * - Result: Network throttles traffic when GPU voltage is stressed
 * 
 * TCP Option Format (Option Kind 0x1A):
 * +--------+--------+--------+--------+
 * | Kind   | Length | Voltage (16-bit)|
 * | 0x1A   | 0x04   | V * 1000        |
 * +--------+--------+--------+--------+
 * 
 * Voltage is encoded as: V * 1000 (e.g., 0.85V = 850)
 * 
 * Target: BMv2 (Behavioral Model v2) for simulation
 * Can be adapted for Tofino, barefoot, or other P4 targets
 */

#include <core.p4>
#include <v1model.p4>

/*============================================================================
 * Constants
 *===========================================================================*/

// TCP Option Kind for Voltage Telemetry (experimental range)
const bit<8> TCP_OPTION_VOLTAGE = 0x1A;

// Voltage thresholds (encoded as V * 1000)
const bit<16> VOLTAGE_THRESHOLD_THROTTLE = 820;  // 0.82V - start throttling
const bit<16> VOLTAGE_THRESHOLD_RESUME = 880;    // 0.88V - resume full rate

// Meter indices
const bit<32> METER_INDEX_GPU = 0;

/*============================================================================
 * Headers
 *===========================================================================*/

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<3>  res;
    bit<9>  flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

// Custom TCP Option for Voltage Telemetry
header tcp_option_voltage_t {
    bit<8>  kind;      // 0x1A
    bit<8>  length;    // 0x04 (4 bytes total)
    bit<16> voltage;   // Voltage * 1000 (e.g., 850 = 0.85V)
}

// Metadata for internal processing
struct metadata_t {
    bit<16> gpu_voltage;          // Extracted voltage reading
    bit<1>  voltage_valid;        // Whether voltage was parsed
    bit<1>  should_throttle;      // Whether to apply throttling
    bit<32> meter_result;         // Result from meter check
}

struct headers_t {
    ethernet_t           ethernet;
    ipv4_t               ipv4;
    tcp_t                tcp;
    tcp_option_voltage_t tcp_voltage;
}

/*============================================================================
 * Parser
 *===========================================================================*/

parser MyParser(
    packet_in packet,
    out headers_t hdr,
    inout metadata_t meta,
    inout standard_metadata_t standard_metadata
) {
    state start {
        transition parse_ethernet;
    }
    
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            0x0800: parse_ipv4;
            default: accept;
        }
    }
    
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            6: parse_tcp;  // TCP
            default: accept;
        }
    }
    
    state parse_tcp {
        packet.extract(hdr.tcp);
        // Check if TCP header has options (dataOffset > 5)
        transition select(hdr.tcp.dataOffset) {
            5: accept;  // No options
            default: parse_tcp_options;
        }
    }
    
    state parse_tcp_options {
        // Look for voltage telemetry option
        // In production, this would loop through all options
        // Simplified: assume voltage option is first if present
        packet.extract(hdr.tcp_voltage);
        transition select(hdr.tcp_voltage.kind) {
            TCP_OPTION_VOLTAGE: parse_voltage_option;
            default: accept;
        }
    }
    
    state parse_voltage_option {
        // Voltage option found - extract value
        meta.gpu_voltage = hdr.tcp_voltage.voltage;
        meta.voltage_valid = 1;
        transition accept;
    }
}

/*============================================================================
 * Ingress Processing
 *===========================================================================*/

control MyIngress(
    inout headers_t hdr,
    inout metadata_t meta,
    inout standard_metadata_t standard_metadata
) {
    // Token bucket meter for rate limiting
    // Two rates: full (100 Gbps) and throttled (20 Gbps)
    meter(1, MeterType.bytes) gpu_traffic_meter;
    
    // Register to store current rate mode (0 = full, 1 = throttled)
    register<bit<1>>(1) throttle_mode;
    
    // Counter for telemetry events
    counter(1, CounterType.packets) telemetry_events;
    
    action drop() {
        mark_to_drop(standard_metadata);
    }
    
    action forward(bit<9> port) {
        standard_metadata.egress_spec = port;
    }
    
    action update_throttle_mode(bit<1> mode) {
        throttle_mode.write(0, mode);
    }
    
    action apply_meter() {
        // Apply the traffic meter
        // Result: 0 = GREEN (pass), 1 = YELLOW (pass with warning), 2 = RED (drop)
        gpu_traffic_meter.execute_meter(METER_INDEX_GPU, meta.meter_result);
    }
    
    table voltage_response {
        // Table to determine throttling action based on voltage
        key = {
            meta.voltage_valid: exact;
            meta.gpu_voltage: range;
        }
        actions = {
            update_throttle_mode;
            NoAction;
        }
        const entries = {
            // If voltage < 820 (0.82V), enable throttling
            (1, 0 .. 819): update_throttle_mode(1);
            // If voltage >= 880 (0.88V), disable throttling
            (1, 880 .. 1000): update_throttle_mode(0);
            // In between: maintain current mode (handled by default)
        }
        default_action = NoAction();
    }
    
    table forwarding {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            forward;
            drop;
        }
        default_action = drop();
    }
    
    apply {
        // Step 1: Process voltage telemetry if present
        if (meta.voltage_valid == 1) {
            voltage_response.apply();
            telemetry_events.count(0);
        }
        
        // Step 2: Apply traffic meter based on current throttle mode
        bit<1> current_mode;
        throttle_mode.read(current_mode, 0);
        
        if (current_mode == 1) {
            // Throttled mode - apply stricter meter
            apply_meter();
            
            // If meter says RED, drop the packet
            if (meta.meter_result == 2) {
                drop();
                return;
            }
        }
        
        // Step 3: Forward the packet
        if (hdr.ipv4.isValid()) {
            forwarding.apply();
        }
    }
}

/*============================================================================
 * Egress Processing
 *===========================================================================*/

control MyEgress(
    inout headers_t hdr,
    inout metadata_t meta,
    inout standard_metadata_t standard_metadata
) {
    apply {
        // No egress processing needed for this example
        // In production: could add telemetry response headers
    }
}

/*============================================================================
 * Deparser
 *===========================================================================*/

control MyDeparser(
    packet_out packet,
    in headers_t hdr
) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        // Only emit voltage option if it was present
        packet.emit(hdr.tcp_voltage);
    }
}

/*============================================================================
 * Checksum Verification/Update (Simplified)
 *===========================================================================*/

control MyVerifyChecksum(
    inout headers_t hdr,
    inout metadata_t meta
) {
    apply {
        // Checksum verification would go here
    }
}

control MyComputeChecksum(
    inout headers_t hdr,
    inout metadata_t meta
) {
    apply {
        // Checksum computation would go here
    }
}

/*============================================================================
 * Switch Pipeline
 *===========================================================================*/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;

/*
 * Usage Notes:
 * 
 * 1. Compile with: p4c --target bmv2 --arch v1model switch_logic.p4
 * 
 * 2. Run with BMv2: simple_switch -i 0@eth0 switch_logic.json
 * 
 * 3. GPU client must encode voltage in TCP options:
 *    - Add option kind 0x1A with 4-byte payload
 *    - Encode voltage as integer (V * 1000)
 *    - Example: 0.85V = 850 = 0x0352
 * 
 * 4. Meter configuration (via control plane):
 *    - Full rate: 100 Gbps (12.5 GB/s)
 *    - Throttled rate: 20 Gbps (2.5 GB/s)
 *    - Burst size: 1500 * 100 = 150KB
 * 
 * Patent Claim Coverage:
 * - Parsing voltage from in-band TCP options (lines 100-130)
 * - Throttle decision based on voltage thresholds (lines 175-190)
 * - Token bucket rate adjustment (lines 195-210)
 */

