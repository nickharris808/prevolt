"""
Generate Figures 5, 6, 8 (Block Diagrams)
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_box(ax, x, y, w, h, text, color='white'):
    rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor='black', facecolor=color)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=10)

def generate_fig_5_limp_mode():
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    draw_box(ax, 4, 7, 2, 2, "NORMAL\n(500A)", 'lightgreen')
    draw_box(ax, 1, 3, 2, 2, "CLAMP\n(Ramp Down)", 'yellow')
    draw_box(ax, 7, 3, 2, 2, "LIMP MODE\n(200A Limit)", 'salmon')
    
    # Arrows
    ax.annotate("", xy=(5, 7), xytext=(2, 5), arrowprops=dict(arrowstyle="<-", lw=2))
    ax.text(3, 6, "No Packet", ha='right')
    
    ax.annotate("", xy=(5, 7), xytext=(8, 5), arrowprops=dict(arrowstyle="<-", lw=2))
    ax.text(7, 6, "No Trigger", ha='left')
    
    ax.set_title("Figure 5: Fail-Safe State Machine")
    plt.savefig('patents/figures/FIG_5_LIMP_MODE.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_5_LIMP_MODE.png")

def generate_fig_6_kalman():
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis('off')
    
    draw_box(ax, 1, 2, 2, 2, "Measurement\n(V_min)", 'lightblue')
    draw_box(ax, 4, 2, 2, 2, "Kalman\nFilter", 'lightgray')
    draw_box(ax, 7, 2, 2, 2, "Lead Time\nUpdate", 'lightyellow')
    draw_box(ax, 10, 2, 1.5, 2, "Switch\nRegister", 'white')
    
    ax.annotate("", xy=(4, 3), xytext=(3, 3), arrowprops=dict(arrowstyle="->", lw=2))
    ax.annotate("", xy=(7, 3), xytext=(6, 3), arrowprops=dict(arrowstyle="->", lw=2))
    ax.annotate("", xy=(10, 3), xytext=(9, 3), arrowprops=dict(arrowstyle="->", lw=2))
    
    ax.set_title("Figure 6: Adaptive Aging Compensation")
    plt.savefig('patents/figures/FIG_6_KALMAN_BLOCK.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_6_KALMAN_BLOCK.png")

def generate_fig_8_hierarchy():
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    draw_box(ax, 4, 8, 2, 1.5, "Facility\nArbiter\n(100MW)", 'gold')
    
    draw_box(ax, 1, 5, 2, 1.5, "Row A\n(10MW)", 'silver')
    draw_box(ax, 7, 5, 2, 1.5, "Row B\n(10MW)", 'silver')
    
    draw_box(ax, 0, 2, 1.5, 1.5, "Rack 1", 'white')
    draw_box(ax, 2, 2, 1.5, 1.5, "Rack 2", 'white')
    draw_box(ax, 6.5, 2, 1.5, 1.5, "Rack 3", 'white')
    draw_box(ax, 8.5, 2, 1.5, 1.5, "Rack 4", 'white')
    
    # Lines
    ax.plot([5, 2], [8, 6.5], 'k-')
    ax.plot([5, 8], [8, 6.5], 'k-')
    
    ax.plot([2, 0.75], [5, 3.5], 'k-')
    ax.plot([2, 2.75], [5, 3.5], 'k-')
    
    ax.plot([8, 7.25], [5, 3.5], 'k-')
    ax.plot([8, 9.25], [5, 3.5], 'k-')
    
    ax.set_title("Figure 8: Facility Power Hierarchy")
    plt.savefig('patents/figures/FIG_8_HIERARCHY.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_8_HIERARCHY.png")

if __name__ == "__main__":
    generate_fig_5_limp_mode()
    generate_fig_6_kalman()
    generate_fig_8_hierarchy()
