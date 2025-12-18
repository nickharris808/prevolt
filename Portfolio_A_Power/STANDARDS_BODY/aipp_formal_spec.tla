--------------------------- MODULE AIPP_Formal_Spec ---------------------------
EXTENDS Naturals, Reals

VARIABLES 
    Switch_State,    (* IDLE, PRECHARGE, BURST *)
    Network_Buffer,  (* Number of packets in flight *)
    VRM_Voltage,     (* Current rail voltage in Volts *)
    Watchdog_Timer   (* Time since precharge start *)

(* Constants for safety boundaries *)
V_MAX == 1.25
V_MIN == 0.85
T_WATCHDOG_MAX == 0.000005 (* 5us safety limit *)

TypeOK == 
    /\ Switch_State \in {"IDLE", "PRECHARGE", "BURST"}
    /\ Network_Buffer \in 0..10
    /\ VRM_Voltage \in {v \in Real : v >= 0.0}
    /\ Watchdog_Timer \in {t \in Real : t >= 0.0}

Init == 
    /\ Switch_State = "IDLE"
    /\ Network_Buffer = 0
    /\ VRM_Voltage = 0.9
    /\ Watchdog_Timer = 0.0

(* Safety Invariant: Voltage must never exceed OVP limit *)
Safety_Invariant == VRM_Voltage < V_MAX

(* Liveness Invariant: Packets must eventually be processed *)
Liveness_Invariant == (Network_Buffer > 0) ~> (Network_Buffer = 0)

(* Transitions *)
Start_Precharge ==
    /\ Switch_State = "IDLE"
    /\ Switch_State' = "PRECHARGE"
    /\ VRM_Voltage' = 1.15
    /\ Watchdog_Timer' = 0.0
    /\ UNCHANGED Network_Buffer

Packet_Arrival ==
    /\ Switch_State = "PRECHARGE"
    /\ Switch_State' = "BURST"
    /\ Network_Buffer' = Network_Buffer + 1
    /\ VRM_Voltage' = 0.95
    /\ Watchdog_Timer' = 0.0

Watchdog_Failsafe ==
    /\ Switch_State = "PRECHARGE"
    /\ Watchdog_Timer > T_WATCHDOG_MAX
    /\ Switch_State' = "IDLE"
    /\ VRM_Voltage' = 0.9
    /\ Watchdog_Timer' = 0.0
    /\ UNCHANGED Network_Buffer

Next == Start_Precharge \/ Packet_Arrival \/ Watchdog_Failsafe

Spec == Init /\ [][Next]_<<Switch_State, Network_Buffer, VRM_Voltage, Watchdog_Timer>>
=============================================================================

