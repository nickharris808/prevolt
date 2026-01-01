"""
Generate Block Diagram (Figure 1)
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_figure_1_block():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Draw Switch
    rect_sw = patches.Rectangle((1, 2), 2, 3, linewidth=2, edgecolor='blue', facecolor='none')
    ax.add_patch(rect_sw)
    ax.text(2, 3.5, "Network\nSwitch", ha='center', va='center', fontsize=12)
    
    # Draw VRM
    rect_vrm = patches.Rectangle((5, 3), 2, 2, linewidth=2, edgecolor='green', facecolor='none')
    ax.add_patch(rect_vrm)
    ax.text(6, 4, "VRM\n(Controller)", ha='center', va='center', fontsize=12)
    
    # Draw GPU
    rect_gpu = patches.Rectangle((9, 2), 2, 3, linewidth=2, edgecolor='red', facecolor='none')
    ax.add_patch(rect_gpu)
    ax.text(10, 3.5, "Compute\nNode\n(GPU)", ha='center', va='center', fontsize=12)
    
    # Draw Power Path
    ax.annotate("", xy=(9, 4), xytext=(7, 4), arrowprops=dict(arrowstyle="->", lw=3, color='k'))
    ax.text(8, 4.2, "Power (V_out)", ha='center')
    
    # Draw Trigger Path
    ax.annotate("", xy=(5, 4.5), xytext=(3, 4.5), arrowprops=dict(arrowstyle="->", lw=2, color='g', linestyle='dashed'))
    ax.text(4, 4.7, "Pre-Charge Trigger", ha='center')
    
    # Draw Packet Path
    ax.annotate("", xy=(9, 2.5), xytext=(3, 2.5), arrowprops=dict(arrowstyle="->", lw=2, color='b'))
    ax.text(6, 2.7, "Packet Data (Delayed)", ha='center')
    
    ax.set_title("Figure 1: System Block Diagram")
    
    plt.savefig('patents/figures/FIG_1_SYSTEM_BLOCK.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_1_SYSTEM_BLOCK.png")

if __name__ == "__main__":
    generate_figure_1_block()
