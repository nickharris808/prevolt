"""
Sovereign Physics Engine: Global Hardware Constants
===================================================

This module defines the 'Ground Truth' physics for all Portfolio B simulations.
Every timing and bandwidth parameter must derive from these hardware constants
 to ensure $100M+ strategic acquisition fidelity.

Standard Specs: PCIe Gen5, CXL 2.0/3.0, UEC (Ultra Ethernet).

Author: Neural Harris Architecture Group
License: Proprietary - Patent Pending
"""

import numpy as np

class Physics:
    # --- TIME CONSTANTS (Nanoseconds) ---
    NS = 1.0
    US = 1000.0 * NS
    MS = 1000.0 * US
    
    # CPU/ASIC Clock (3.3 GHz)
    CLOCK_CYCLE_NS = 0.3 * NS
    
    # --- BANDWIDTH CONSTANTS (Gbps - Gigabits per second) ---
    # Unidirectional rates
    ETH_100G = 100.0
    ETH_200G = 200.0
    ETH_400G = 400.0
    ETH_800G = 800.0
    
    # PCIe Gen5 x16 (64 GB/s per direction = 512 Gbps)
    PCIE_GEN5_X16_GBPS = 512.0
    
    # CXL 2.0 (Built on PCIe Gen5 x16)
    CXL_LINK_GBPS = PCIE_GEN5_X16_GBPS
    
    # DDR5-6400 (Single Channel: ~51.2 GB/s = 409.6 Gbps)
    # 8-Channel Server: ~3200 Gbps
    DRAM_BW_GBPS = 3200.0
    
    # --- LATENCY CONSTANTS (Nanoseconds) ---
    # L3 Cache Hit
    L3_HIT_NS = 40.0 * NS
    
    # Local DRAM Access (DDR5)
    DRAM_ACCESS_NS = 100.0 * NS
    
    # CXL.mem Direct (Root Complex to Device)
    CXL_LOCAL_NS = 80.0 * NS
    
    # CXL.mem Switched (1-Hop Fabric)
    CXL_FABRIC_1HOP_NS = 350.0 * NS
    
    # CXL.mem Tunnel (Multi-Hop / UEC Bridge)
    CXL_TUNNEL_NS = 1500.0 * NS
    
    # --- BUFFER CONSTANTS (Bytes) ---
    # Standard 200G NIC Ingress Buffer (16MB)
    NIC_BUFFER_BYTES = 16 * 1024 * 1024
    
    # Switch Shared Buffer (e.g., Tomahawk 5: 160MB shared)
    SWITCH_BUFFER_BYTES = 128 * 1024 * 1024
    
    # --- CONVERSION HELPERS ---
    @staticmethod
    def gbps_to_bytes_per_ns(gbps: float) -> float:
        """Convert Gigabits per second to Bytes per nanosecond."""
        # gbps * 1e9 / 8 (bytes) / 1e9 (ns) = gbps / 8
        return gbps / 8.0

    @staticmethod
    def bytes_to_ns(num_bytes: int, gbps: float) -> float:
        """Calculate time to transfer bytes at a given Gbps."""
        if gbps == 0: return float('inf')
        return num_bytes / Physics.gbps_to_bytes_per_ns(gbps)

    @staticmethod
    def get_stochastic_latency(base_ns: float, rng: np.random.Generator) -> float:
        """
        Models tail latency using a Log-Normal distribution.
        AI clusters fail because of the tail (p99), not the mean.
        """
        # Mean = base_ns, with a heavy tail
        sigma = 0.5 # Shape parameter for tail
        mu = np.log(base_ns) - (sigma**2 / 2)
        return rng.lognormal(mu, sigma)

if __name__ == "__main__":
    # Sanity Check
    print("Sovereign Physics Audit:")
    print(f"200G Packet (1500B) Time: {Physics.bytes_to_ns(1500, Physics.ETH_200G):.2f} ns")
    print(f"CXL Link Fill Time (16MB): {Physics.bytes_to_ns(Physics.NIC_BUFFER_BYTES, Physics.CXL_LINK_GBPS) / Physics.US:.2f} us")
    print(f"DRAM Bandwidth vs CXL: {Physics.DRAM_BW_GBPS / Physics.CXL_LINK_GBPS:.1f}x surplus")










