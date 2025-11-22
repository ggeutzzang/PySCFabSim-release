import datetime
import io
import json
import os
from sys import argv, stdout

from stable_baselines3 import PPO
from simulation.gym.environment import DynamicSCFabSimulationEnvironment
from simulation.gym.sample_envs import DEMO_ENV_1
from simulation.stats import print_statistics


def main():
    t = datetime.datetime.now()

    # 모델 로드
    model = PPO.load(os.path.join(argv[1], argv[2]))

    # config.json 읽기
    with io.open(os.path.join(argv[1], "config.json"), "r") as f:
        config = json.load(f)['params']

    # 평가 환경 생성 (30일)
    args = dict(
        seed=0,
        num_actions=config['action_count'],
        active_station_group=config['station_group'],
        days=30,  # 데모용: 30일만 평가
        dataset='SMT2020_' + config['dataset'],
        dispatcher=config['dispatcher'],
        reward_type=config['reward']
    )

    print(f"🎯 데모 RL 평가 시작!")
    print(f"📊 모델: {argv[2]}")
    print(f"⏱️  평가 기간: 30일\n")

    env = DynamicSCFabSimulationEnvironment(**DEMO_ENV_1, **args, max_steps=1000000000)
    obs = env.reset()
    reward = 0

    steps = 0
    shown_days = 0
    deterministic = True

    while True:
        # 액션 예측
        action, _states = model.predict(obs, deterministic=deterministic)

        # 스텝 실행
        obs, r, done, info = env.step(action)

        # 패널티 받으면 stochastic으로 전환
        if r < 0:
            deterministic = False
        else:
            deterministic = True

        reward += r
        steps += 1
        di = int(env.instance.current_time_days)

        # 진행 상황 출력 (5일마다)
        if di % 5 == 0 and di > shown_days:
            print(f'Step {steps:5d} | Day {di:2d} | Reward: {reward:,.0f}')
            shown_days = di
            stdout.flush()

        # 30일 도달 시 통계 출력
        if env.instance.current_time_days > 30:
            print(f'\n📊 30일 평가 완료!')
            print_statistics(
                env.instance,
                30,
                config['dataset'],
                config['dispatcher'],
                method='rl_demo',
                dir=argv[1]
            )
            break

        # 완료 체크
        if done:
            print('완료 (done)')
            break

    print(f'\n✅ 평가 완료!')
    print(f'💰 총 보상: {reward:,.0f}')
    dt = datetime.datetime.now() - t
    print(f'⏱️  소요 시간: {dt}')
    env.close()


if __name__ == '__main__':
    main()
