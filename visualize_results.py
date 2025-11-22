"""
체크포인트 평가 결과 시각화

학습 진행에 따른 성능 변화를 그래프로 표시
"""
import json
import os
import matplotlib.pyplot as plt
from pathlib import Path

def extract_metrics(exp_dir):
    """실험 디렉토리에서 모든 JSON 결과 파일을 읽어 메트릭 추출"""
    results = []
    
    # JSON 파일 찾기
    for json_file in Path(exp_dir).glob("*.json"):
        if json_file.name == "config.json":
            continue
            
        with open(json_file) as f:
            data = json.load(f)
            
        # 파일명에서 체크포인트 정보 추출
        filename = json_file.stem
        
        # 메트릭 추출
        lot_stats = data.get("lot_stats", {})
        
        # 전체 평균 ACT 찾기 (마지막 줄)
        act = None
        throughput = None
        ontime = None
        
        for lot_name, stats in lot_stats.items():
            if lot_name == "overall":
                act = stats.get("ACT")
                throughput = stats.get("throughput") 
                ontime = stats.get("on_time_%")
                break
        
        results.append({
            'checkpoint': filename,
            'ACT': act,
            'throughput': throughput,
            'on_time': ontime
        })
    
    # 체크포인트 순서로 정렬
    results.sort(key=lambda x: x['checkpoint'])
    
    return results

def plot_results(results):
    """결과를 그래프로 표시"""
    if not results:
        print("결과 데이터가 없습니다.")
        return
    
    checkpoints = [r['checkpoint'] for r in results]
    acts = [r['ACT'] for r in results if r['ACT'] is not None]
    throughputs = [r['throughput'] for r in results if r['throughput'] is not None]
    ontimes = [r['on_time'] for r in results if r['on_time'] is not None]
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # ACT 그래프
    if acts:
        axes[0].plot(range(len(acts)), acts, marker='o', linewidth=2, markersize=8)
        axes[0].set_title('Average Cycle Time (ACT) - 낮을수록 좋음', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('ACT (days)', fontsize=12)
        axes[0].grid(True, alpha=0.3)
        axes[0].set_xticks(range(len(acts)))
        axes[0].set_xticklabels([c[:30] for c in checkpoints[:len(acts)]], rotation=45, ha='right')
    
    # Throughput 그래프
    if throughputs:
        axes[1].plot(range(len(throughputs)), throughputs, marker='s', color='green', linewidth=2, markersize=8)
        axes[1].set_title('Throughput - 높을수록 좋음', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Completed Lots', fontsize=12)
        axes[1].grid(True, alpha=0.3)
        axes[1].set_xticks(range(len(throughputs)))
        axes[1].set_xticklabels([c[:30] for c in checkpoints[:len(throughputs)]], rotation=45, ha='right')
    
    # On-time % 그래프
    if ontimes:
        axes[2].plot(range(len(ontimes)), ontimes, marker='^', color='orange', linewidth=2, markersize=8)
        axes[2].set_title('On-time % - 높을수록 좋음', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('On-time %', fontsize=12)
        axes[2].set_xlabel('Checkpoint', fontsize=12)
        axes[2].grid(True, alpha=0.3)
        axes[2].set_xticks(range(len(ontimes)))
        axes[2].set_xticklabels([c[:30] for c in checkpoints[:len(ontimes)]], rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('rl_learning_curves.png', dpi=150, bbox_inches='tight')
    print(f"\n✅ 그래프 저장 완료: rl_learning_curves.png")
    plt.close()
    
    # 결과 텍스트 출력
    print("\n" + "="*70)
    print("📊 체크포인트별 성능 비교")
    print("="*70)
    print(f"{'Checkpoint':<40} {'ACT':>10} {'Throughput':>12} {'On-time %':>10}")
    print("-"*70)
    for r in results:
        act_str = f"{r['ACT']:.1f}" if r['ACT'] is not None else "N/A"
        tp_str = f"{r['throughput']}" if r['throughput'] is not None else "N/A"
        ot_str = f"{r['on_time']:.1f}" if r['on_time'] is not None else "N/A"
        print(f"{r['checkpoint']:<40} {act_str:>10} {tp_str:>12} {ot_str:>10}")
    print("="*70)

if __name__ == '__main__':
    exp_dir = "experiments/DEMO_0_ds_HVLM_a5_tp30_reward2_di_fifo_<I"
    
    print(f"🔍 결과 파일 분석 중: {exp_dir}")
    results = extract_metrics(exp_dir)
    
    if results:
        plot_results(results)
    else:
        print("❌ 결과 파일을 찾을 수 없습니다.")
