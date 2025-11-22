import datetime
import json
import os
import sys
import time

from stable_baselines3 import PPO
from simulation.gym.environment import DynamicSCFabSimulationEnvironment
from stable_baselines3.common.callbacks import CheckpointCallback
from sys import argv
from simulation.gym.sample_envs import DEMO_ENV_1


def main():
    # 데모용: 5만 스텝만 학습 (원본은 100만)
    to_train = 50000
    t = time.time()

    class MyCallBack(CheckpointCallback):
        def on_step(self) -> bool:
            if self.num_timesteps % 100 == 0:
                ratio = self.num_timesteps / to_train
                perc = round(ratio * 100)
                remaining = (time.time() - t) / ratio * (1 - ratio) if ratio > 0 else 9999999999999
                remaining /= 60  # 분 단위로 표시

                sys.stderr.write(f'\r{self.num_timesteps} / {to_train} {perc}% {round(remaining, 1)} minutes left    Day:{round(env.instance.current_time_days, 1)}      ')
                sys.stderr.flush()
            return super().on_step()

    # config.json 읽기
    fn = argv[1]
    with open(fn, 'r') as config:
        p = json.load(config)['params']

    args = dict(
        num_actions=p['action_count'],
        active_station_group=p['station_group'],
        days=p['training_period'],
        dataset='SMT2020_' + p['dataset'],
        dispatcher=p['dispatcher']
    )

    print(f"🚀 데모 RL 학습 시작!")
    print(f"📊 설정: {p['dataset']}, {p['action_count']} actions, {p['training_period']} days")
    print(f"🎯 목표: {to_train:,} 스텝 학습\n")

    # 환경 생성
    env = DynamicSCFabSimulationEnvironment(
        **DEMO_ENV_1,
        **args,
        seed=p['seed'],
        max_steps=1000000,
        reward_type=p['reward']
    )

    # PPO 모델 생성
    model = PPO("MlpPolicy", env, verbose=1)

    # 체크포인트 설정 (1만 스텝마다)
    save_path = os.path.dirname(os.path.realpath(fn))
    checkpoint_callback = MyCallBack(
        save_freq=10000,
        save_path=save_path,
        name_prefix='checkpoint_'
    )

    # 학습 시작
    start_time = time.time()
    model.learn(
        total_timesteps=to_train,
        callback=checkpoint_callback
    )

    # 최종 모델 저장
    model.save(os.path.join(save_path, 'trained.weights'))

    elapsed = time.time() - start_time
    print(f"\n\n✅ 학습 완료!")
    print(f"⏱️  소요 시간: {elapsed/60:.1f}분")
    print(f"💾 모델 저장: {save_path}/trained.weights.zip")


if __name__ == '__main__':
    main()
