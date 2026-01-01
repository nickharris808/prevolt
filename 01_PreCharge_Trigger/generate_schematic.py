"""
Generate Figure 4: Circuit Schematic (Fallback)
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_figure_4_schematic():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Source
    ax.add_patch(patches.Circle((1, 3), 0.5, fill=False, lw=2))
    ax.text(1, 3, "VRM", ha='center', va='center')
    ax.plot([1, 1], [0.5, 2.5], 'k-', lw=2) # Line to ground
    ax.plot([1, 1], [3.5, 5], 'k-', lw=2)   # Line up
    
    # Resistor
    ax.plot([1, 3], [5, 5], 'k-', lw=2)
    ax.plot([3, 3.2, 3.4, 3.6, 3.8, 4], [5, 5.2, 4.8, 5.2, 4.8, 5], 'k-', lw=2) # Zigzag
    ax.text(3.5, 5.5, "R_series\n0.4mΩ", ha='center')
    
    # Inductor
    ax.plot([4, 5], [5, 5], 'k-', lw=2)
    for i in range(4):
        ax.add_patch(patches.Arc((5.2 + i*0.4, 5), 0.4, 0.4, theta1=0, theta2=180, lw=2))
    ax.text(6, 5.5, "L_series\n1.2nH", ha='center')
    
    # Capacitor
    ax.plot([6.8, 8], [5, 5], 'k-', lw=2)
    ax.plot([8, 8], [5, 4], 'k-', lw=2)
    ax.plot([7.5, 8.5], [4, 4], 'k-', lw=2) # Top plate
    ax.plot([7.5, 8.5], [3.5, 3.5], 'k-', lw=2) # Bottom plate
    ax.plot([8, 8], [3.5, 0.5], 'k-', lw=2)
    ax.text(8.5, 3.75, "C_out\n15mF", ha='left')
    
    # Load
    ax.plot([8, 10], [5, 5], 'k-', lw=2)
    ax.plot([10, 10], [5, 4], 'k-', lw=2)
    ax.add_patch(patches.Rectangle((9.5, 2), 1, 2, fill=False, lw=2))
    ax.text(10, 3, "GPU\nLoad\n(500A)", ha='center', va='center')
    ax.plot([10, 10], [2, 0.5], 'k-', lw=2)
    
    # Ground
    ax.plot([0.5, 10.5], [0.5, 0.5], 'k-', lw=2)
    ax.text(5.5, 0.2, "GND", ha='center')
    
    ax.set_title("Figure 4: Power Delivery Network Model")
    plt.savefig('patents/figures/FIG_4_CIRCUIT_SCHEMATIC.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_4_CIRCUIT_SCHEMATIC.png")

if __name__ == "__main__":
    generate_figure_4_schematic()
