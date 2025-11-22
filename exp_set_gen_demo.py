import io
import json
import os.path
from os import mkdir, path

root = 'experiments'
if not os.path.exists(root):
    mkdir(root)

stngrps = [
    '<Implant_128>',
]

# 데모용 짧은 설정
for seed in [0]:
    for dataset, dispatcher in [('HVLM', 'fifo')]:
        for action_count in [5]:  # 9 -> 5 (더 간단)
            for training_period in [30]:  # 730 -> 30 (짧게)
                for reward in [2]:
                    for stngrp in stngrps:
                        case_name = f'DEMO_{seed}_ds_{dataset}_a{action_count}_tp{training_period}_reward{reward}_di_{dispatcher}_{str(stngrp)[:2]}'
                        d = path.join(root, case_name)
                        if not os.path.exists(d):
                            mkdir(d)
                        with io.open(path.join(d, 'config.json'), 'w') as f:
                            case = {
                                'name': case_name,
                                'params': {
                                    'seed': seed,
                                    'dataset': dataset,
                                    'action_count': action_count,
                                    'training_period': training_period,
                                    'dispatcher': dispatcher,
                                    'reward': reward,
                                    'station_group': stngrp,
                                }
                            }
                            json.dump(case, f, indent=2)

print(f"✅ 데모 실험 설정 생성 완료: {case_name}")
