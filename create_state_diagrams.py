#!/usr/bin/env python3
"""
PySCFabSim State Diagram 시각화
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.font_manager as fm

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def create_machine_state_diagram():
    """Machine (장비) State Diagram"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 색상 정의
    color_idle = '#90EE90'      # 연한 녹색
    color_processing = '#87CEEB'  # 하늘색
    color_breakdown = '#FFB6C1'   # 연한 빨강
    color_pm = '#FFD700'          # 금색

    # 상태 박스 정의 (x, y, width, height, label, color)
    states = {
        'start': (1, 8.5, 0.3, 0.3, 'Start', 'black'),
        'idle': (2, 7, 1.8, 1.2, 'IDLE\n(Usable)', color_idle),
        'processing': (6, 7, 1.8, 1.2, 'PROCESSING\n(Busy)', color_processing),
        'breakdown': (6, 4, 1.8, 1.2, 'BREAKDOWN\n(Down)', color_breakdown),
        'pm': (6, 1, 1.8, 1.2, 'PM\n(Maintenance)', color_pm),
    }

    # 상태 박스 그리기
    for key, (x, y, w, h, label, color) in states.items():
        if key == 'start':
            circle = Circle((x + w/2, y + h/2), w/2, color=color, zorder=2)
            ax.add_patch(circle)
        else:
            box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                edgecolor='black', facecolor=color, linewidth=2, zorder=2)
            ax.add_patch(box)
            ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                   fontsize=13, fontweight='bold', zorder=3)

    # 화살표 정의 (from_state, to_state, label, curve)
    arrows = [
        # (from_x, from_y, to_x, to_y, label, connectionstyle)
        (1.3, 8.5, 2.5, 8.2, 'Simulation\nStart', 'arc3,rad=0'),
        (3.8, 7.6, 6, 7.6, 'dispatch()\nLot Assigned', 'arc3,rad=0.2'),
        (6, 7, 3.8, 7, 'MachineDoneEvent\nWork Complete', 'arc3,rad=-0.2'),
        (6.9, 6.9, 6.9, 5.2, 'BreakdownEvent\nFailure', 'arc3,rad=0'),
        (7.1, 6.9, 7.1, 2.2, 'BreakdownEvent\nPM Schedule', 'arc3,rad=0'),
        (6, 4.6, 3.8, 7.4, 'Repair Complete\n(length time)', 'arc3,rad=-0.3'),
        (6, 1.6, 3.8, 7, 'PM Complete\n(length time)', 'arc3,rad=-0.4'),
        (2.9, 6.9, 2.9, 8.3, 'Waiting Lots\nAdded', 'arc3,rad=0.3'),
    ]

    for from_x, from_y, to_x, to_y, label, style in arrows:
        arrow = FancyArrowPatch((from_x, from_y), (to_x, to_y),
                               arrowstyle='->', mutation_scale=20, linewidth=2,
                               color='darkblue', connectionstyle=style, zorder=1)
        ax.add_patch(arrow)

        # 라벨 위치 (화살표 중간)
        mid_x, mid_y = (from_x + to_x) / 2, (from_y + to_y) / 2
        ax.text(mid_x, mid_y, label, fontsize=9, ha='center',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

    # 설명 박스
    descriptions = [
        (0.5, 5.5, "IDLE: Machine ready\n- waiting_lots available\n- Can dispatch"),
        (0.5, 3.5, "PROCESSING: Working\n- Processing specific lot\n- MachineDoneEvent scheduled"),
        (0.5, 2, "BREAKDOWN: Failed\n- bred_time increases\n- All events delayed"),
        (0.5, 0.5, "PM: Maintenance\n- pmed_time increases\n- All events delayed"),
    ]

    for x, y, text in descriptions:
        ax.text(x, y, text, fontsize=8, style='italic',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.7))

    ax.set_title('Machine State Diagram', fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('machine_state_diagram.png', dpi=300, bbox_inches='tight')
    print("✅ machine_state_diagram.png saved!")
    plt.close()


def create_lot_state_diagram():
    """Lot (로트) State Diagram"""
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 색상
    color_dispatchable = '#E6E6FA'  # 라벤더
    color_active = '#98FB98'        # 연한 녹색
    color_waiting = '#FFE4B5'       # 모카신
    color_processing = '#87CEEB'    # 하늘색
    color_done = '#FFD700'          # 금색

    # 상태 박스
    states = {
        'start': (1, 8.5, 0.3, 0.3, 'Start', 'black'),
        'dispatchable': (2.5, 7.5, 1.8, 1, 'DISPATCHABLE\n(Waiting Release)', color_dispatchable),
        'active': (5.5, 7.5, 1.8, 1, 'ACTIVE\n(In Factory)', color_active),
        'waiting': (8.5, 7.5, 1.8, 1, 'WAITING\n(For Machine)', color_waiting),
        'processing': (8.5, 5, 1.8, 1, 'PROCESSING\n(In Machine)', color_processing),
        'step_done': (8.5, 2.5, 1.8, 1, 'STEP DONE\n(Step Complete)', color_active),
        'done': (5.5, 2.5, 1.8, 1, 'DONE\n(All Complete)', color_done),
        'end': (2.5, 2.5, 0.3, 0.3, 'End', 'black'),
    }

    # 상태 박스 그리기
    for key, (x, y, w, h, label, color) in states.items():
        if key in ['start', 'end']:
            if key == 'start':
                circle = Circle((x + w/2, y + h/2), w/2, color=color, zorder=2)
            else:
                circle = Circle((x + w/2, y + h/2), w/2, color=color, zorder=2,
                              edgecolor='black', linewidth=2)
                inner_circle = Circle((x + w/2, y + h/2), w/3, color=color, zorder=3,
                                    edgecolor='black', linewidth=2)
                ax.add_patch(inner_circle)
            ax.add_patch(circle)
        else:
            box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                edgecolor='black', facecolor=color, linewidth=2, zorder=2)
            ax.add_patch(box)
            ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                   fontsize=11, fontweight='bold', zorder=3)

    # 화살표
    arrows = [
        (1.3, 8.5, 2.5, 8, 'Order Created', 'arc3,rad=0'),
        (4.3, 8, 5.5, 8, 'ReleaseEvent\n(release_at)', 'arc3,rad=0'),
        (7.3, 8, 8.5, 8, 'free_up_lots()\nFind Machine', 'arc3,rad=0'),
        (9.4, 7.4, 9.4, 6, 'dispatch()\nAssigned', 'arc3,rad=0'),
        (9.4, 5, 9.4, 3.5, 'LotDoneEvent\nStep Complete', 'arc3,rad=0'),
        (8.5, 3, 7.3, 3, 'remaining_steps\nexist', 'arc3,rad=0.2'),
        (7.3, 8, 7.3, 3.2, 'Next Step', 'arc3,rad=-0.5'),
        (8.5, 3, 7.3, 3, 'remaining_steps\nempty', 'arc3,rad=-0.2'),
        (5.5, 3, 2.8, 3, 'All Steps\nComplete', 'arc3,rad=0'),
        (8.5, 8, 10.3, 8, 'All Machines\nBusy', 'arc3,rad=0.5'),
        (10.3, 8, 10.3, 8, '', 'arc3,rad=0.5'),
    ]

    for from_x, from_y, to_x, to_y, label, style in arrows:
        arrow = FancyArrowPatch((from_x, from_y), (to_x, to_y),
                               arrowstyle='->', mutation_scale=20, linewidth=2,
                               color='darkblue', connectionstyle=style, zorder=1)
        ax.add_patch(arrow)

        if label:
            mid_x, mid_y = (from_x + to_x) / 2, (from_y + to_y) / 2
            ax.text(mid_x, mid_y + 0.2, label, fontsize=9, ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

    # 설명 박스
    descriptions = [
        (0.5, 6, "DISPATCHABLE:\n- In dispatchable_lots\n- Waiting for release_at"),
        (0.5, 4.5, "ACTIVE:\n- In active_lots\n- actual_step set"),
        (0.5, 3, "WAITING:\n- In Machine.waiting_lots\n- free_since recorded"),
        (0.5, 1.5, "PROCESSING:\n- Being processed\n- LotDoneEvent scheduled"),
        (0.5, 0.2, "DONE:\n- In done_lots\n- done_at recorded\n- ACT calculated"),
    ]

    for x, y, text in descriptions:
        ax.text(x, y, text, fontsize=8, style='italic',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.7))

    ax.set_title('Lot State Diagram', fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('lot_state_diagram.png', dpi=300, bbox_inches='tight')
    print("✅ lot_state_diagram.png saved!")
    plt.close()


def create_event_flow_diagram():
    """전체 이벤트 흐름 Diagram"""
    fig, ax = plt.subplots(figsize=(14, 16))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 18)
    ax.axis('off')

    # 색상
    color_init = '#E6E6FA'
    color_check = '#FFE4B5'
    color_event = '#87CEEB'
    color_dispatch = '#98FB98'
    color_decision = '#FFD700'

    # 상태 박스 (x, y, w, h, label, color)
    states = {
        'start': (4.5, 16.5, 1, 0.8, 'START', 'black'),
        'init': (3.5, 14.5, 3, 1, 'INITIALIZE\nLoad Dataset', color_init),
        'event_loop': (3.5, 12.5, 3, 1, 'EVENT LOOP\nnext_step()', color_check),
        'check_release': (3.5, 10.5, 3, 1, 'Check Release\nDispatchable?', color_check),
        'process_release': (0.5, 8.5, 2.5, 1, 'ReleaseEvent\nAdd to active', color_event),
        'process_event': (7, 8.5, 2.5, 1, 'Process Event\nfrom Queue', color_event),
        'machine_done': (0.5, 6.5, 2.5, 1, 'MachineDone\nfree_up_machines', color_event),
        'lot_done': (3.5, 6.5, 2.5, 1, 'LotDone\nfree_up_lots', color_event),
        'breakdown': (6.5, 6.5, 2.5, 1, 'Breakdown\nDelay Events', color_event),
        'dispatching': (2, 4.5, 3, 1, 'DISPATCHING\nSelect Lot', color_dispatch),
        'dispatch_check': (2, 2.5, 3, 1, 'usable_machines\n& usable_lots?', color_decision),
        'make_decision': (0.5, 0.5, 2.5, 1, 'Dispatcher\nStrategy', color_dispatch),
        'create_events': (3.5, 0.5, 2.5, 1, 'Create Events\nMachine & Lot', color_event),
        'done': (7, 12.5, 2.5, 1, 'DONE\nStats Output', color_done),
    }

    # 박스 그리기
    for key, (x, y, w, h, label, color) in states.items():
        if key == 'start':
            circle = Circle((x + w/2, y + h/2), 0.4, color='black', zorder=2)
            ax.add_patch(circle)
            ax.text(x + w/2, y + h/2, 'START', ha='center', va='center',
                   fontsize=10, fontweight='bold', color='white', zorder=3)
        else:
            if key in ['check_release', 'dispatch_check']:
                # 다이아몬드 형태
                points = [(x + w/2, y + h), (x + w, y + h/2), (x + w/2, y), (x, y + h/2)]
                diamond = mpatches.Polygon(points, closed=True,
                                          edgecolor='black', facecolor=color, linewidth=2, zorder=2)
                ax.add_patch(diamond)
            else:
                box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                    edgecolor='black', facecolor=color, linewidth=2, zorder=2)
                ax.add_patch(box)
            ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                   fontsize=9, fontweight='bold', zorder=3)

    # 화살표 (단순화)
    arrows = [
        (5, 16.5, 5, 15.5, ''),
        (5, 14.5, 5, 13.5, ''),
        (5, 12.5, 5, 11.5, ''),
        (3.5, 11, 2, 9.5, 'Yes'),
        (6.5, 11, 8, 9.5, 'No'),
        (2, 8.5, 3.5, 5.5, ''),
        (8, 8.5, 2, 7.5, 'MachineDone'),
        (8.2, 8.3, 5, 7.5, 'LotDone'),
        (8.5, 8.3, 8, 7.5, 'Breakdown'),
        (2, 6.5, 3.5, 5.5, ''),
        (5, 6.5, 3.5, 5.5, ''),
        (3.5, 4.5, 3.5, 3.5, ''),
        (2, 2.5, 1.75, 1.5, 'Yes'),
        (5, 2.5, 5, 13.3, 'No'),
        (1.75, 0.5, 3.5, 0.5, ''),
        (4.75, 1, 5, 12.3, ''),
        (6.5, 13, 7, 13, ''),
    ]

    for from_x, from_y, to_x, to_y, label in arrows:
        arrow = FancyArrowPatch((from_x, from_y), (to_x, to_y),
                               arrowstyle='->', mutation_scale=15, linewidth=2,
                               color='darkblue', zorder=1)
        ax.add_patch(arrow)
        if label:
            mid_x, mid_y = (from_x + to_x) / 2, (from_y + to_y) / 2
            ax.text(mid_x + 0.3, mid_y, label, fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

    ax.set_title('Event Flow Diagram', fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('event_flow_diagram.png', dpi=300, bbox_inches='tight')
    print("✅ event_flow_diagram.png saved!")
    plt.close()


def create_simple_comparison_diagram():
    """MachineDoneEvent vs LotDoneEvent 비교"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    for ax in [ax1, ax2]:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')

    # MachineDoneEvent
    ax1.text(5, 9, 'MachineDoneEvent', ha='center', fontsize=16, fontweight='bold')
    ax1.text(5, 8.2, '(Machine Perspective)', ha='center', fontsize=12, style='italic')

    # 타임라인
    timeline_y = 6.5
    ax1.plot([1, 9], [timeline_y, timeline_y], 'k-', linewidth=2)

    # 시간 포인트
    times = [(2, '10:00\nStart'), (5, '10:30\nMachineDone'), (8, '10:31\nNext Dispatch')]
    for x, label in times:
        ax1.plot([x, x], [timeline_y-0.2, timeline_y+0.2], 'ko-', markersize=10)
        ax1.text(x, timeline_y-0.8, label, ha='center', fontsize=10)

    # 머신 상태
    machine_box1 = FancyBboxPatch((1.5, 4), 2, 1.2, boxstyle="round,pad=0.1",
                                 edgecolor='black', facecolor='#87CEEB', linewidth=2)
    ax1.add_patch(machine_box1)
    ax1.text(2.5, 4.6, 'Machine #42\nPROCESSING\nLot_3', ha='center', fontsize=10, fontweight='bold')

    machine_box2 = FancyBboxPatch((4.5, 4), 2, 1.2, boxstyle="round,pad=0.1",
                                 edgecolor='black', facecolor='#90EE90', linewidth=2)
    ax1.add_patch(machine_box2)
    ax1.text(5.5, 4.6, 'Machine #42\nIDLE\nReady!', ha='center', fontsize=10, fontweight='bold')

    machine_box3 = FancyBboxPatch((7, 4), 2, 1.2, boxstyle="round,pad=0.1",
                                 edgecolor='black', facecolor='#87CEEB', linewidth=2)
    ax1.add_patch(machine_box3)
    ax1.text(8, 4.6, 'Machine #42\nPROCESSING\nLot_15', ha='center', fontsize=10, fontweight='bold')

    # 설명
    ax1.text(5, 2.5, 'Key Point:', ha='center', fontsize=12, fontweight='bold')
    ax1.text(5, 1.8, 'Machine becomes IDLE', ha='center', fontsize=11)
    ax1.text(5, 1.3, 'Ready for next lot', ha='center', fontsize=11)
    ax1.text(5, 0.8, 'Dispatching triggered', ha='center', fontsize=11, color='red')

    # LotDoneEvent
    ax2.text(5, 9, 'LotDoneEvent', ha='center', fontsize=16, fontweight='bold')
    ax2.text(5, 8.2, '(Lot Perspective)', ha='center', fontsize=12, style='italic')

    # 타임라인
    ax2.plot([1, 9], [timeline_y, timeline_y], 'k-', linewidth=2)

    # 시간 포인트
    for x, label in times:
        ax2.plot([x, x], [timeline_y-0.2, timeline_y+0.2], 'ko-', markersize=10)
        ax2.text(x, timeline_y-0.8, label, ha='center', fontsize=10)

    # 로트 상태
    lot_box1 = FancyBboxPatch((1.5, 4), 2, 1.2, boxstyle="round,pad=0.1",
                             edgecolor='black', facecolor='#87CEEB', linewidth=2)
    ax2.add_patch(lot_box1)
    ax2.text(2.5, 4.6, 'Lot_3\nStep 17\nImplant', ha='center', fontsize=10, fontweight='bold')

    lot_box2 = FancyBboxPatch((4.5, 4), 2, 1.2, boxstyle="round,pad=0.1",
                             edgecolor='black', facecolor='#FFE4B5', linewidth=2)
    ax2.add_patch(lot_box2)
    ax2.text(5.5, 4.6, 'Lot_3\nStep 18\nDry_Etch', ha='center', fontsize=10, fontweight='bold')

    lot_box3 = FancyBboxPatch((7, 4), 2, 1.2, boxstyle="round,pad=0.1",
                             edgecolor='black', facecolor='#87CEEB', linewidth=2)
    ax2.add_patch(lot_box3)
    ax2.text(8, 4.6, 'Lot_3\nStep 18\nProcessing', ha='center', fontsize=10, fontweight='bold')

    # 설명
    ax2.text(5, 2.5, 'Key Point:', ha='center', fontsize=12, fontweight='bold')
    ax2.text(5, 1.8, 'Lot moves to next step', ha='center', fontsize=11)
    ax2.text(5, 1.3, 'From Implant → Dry_Etch', ha='center', fontsize=11)
    ax2.text(5, 0.8, 'Added to new machine queue', ha='center', fontsize=11, color='red')

    plt.tight_layout()
    plt.savefig('machine_vs_lot_event.png', dpi=300, bbox_inches='tight')
    print("✅ machine_vs_lot_event.png saved!")
    plt.close()


if __name__ == '__main__':
    print("🎨 Creating State Diagrams...")
    create_machine_state_diagram()
    create_lot_state_diagram()
    create_event_flow_diagram()
    create_simple_comparison_diagram()
    print("\n✅ All diagrams created successfully!")
    print("\nGenerated files:")
    print("  - machine_state_diagram.png")
    print("  - lot_state_diagram.png")
    print("  - event_flow_diagram.png")
    print("  - machine_vs_lot_event.png")
