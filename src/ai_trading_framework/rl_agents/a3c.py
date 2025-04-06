import os
import gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.multiprocessing as mp
import ray
from ray import tune

from src.ai_trading_framework.mps_utils import safe_mps_op, timeout_async, Watchdog, log_diagnostic

device = "mps" if torch.backends.mps.is_built() else "cpu"
print(f"[INFO] Using device: {device}")

# -------- Actor-Critic Network --------
class ActorCritic(nn.Module):
    def __init__(self, input_dim, action_dim, hidden_dim=128):
        super(ActorCritic, self).__init__()
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU()
        )
        self.policy = nn.Linear(hidden_dim, action_dim)
        self.value = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = self.shared(x)
        policy_logits = self.policy(x)
        value = self.value(x)
        return policy_logits, value

# -------- Worker Process --------
@safe_mps_op
def worker_fn(worker_id, env_name, global_model, optimizer, config, global_counter, max_steps, result_queue):
    env = gym.make(env_name)
    local_model = ActorCritic(env.observation_space.shape[0], env.action_space.n).to(device)
    local_model.load_state_dict(global_model.state_dict())

    gamma = config.get("gamma", 0.99)
    entropy_beta = config.get("entropy_beta", 0.01)
    t_max = config.get("t_max", 5)

    state = env.reset()
    done = False
    episode_reward = 0
    steps = 0

    while global_counter.value < max_steps:
        values, log_probs, rewards, entropies = [], [], [], []
        for _ in range(t_max):
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            logits, value = local_model(state_tensor)
            probs = torch.softmax(logits, dim=-1)
            log_prob = torch.log_softmax(logits, dim=-1)
            entropy = -(log_prob * probs).sum(1, keepdim=True)

            action = probs.multinomial(num_samples=1).detach()
            log_prob_action = log_prob.gather(1, action)

            next_state, reward, done, _ = env.step(action.item())
            episode_reward += reward
            steps += 1

            values.append(value)
            log_probs.append(log_prob_action)
            rewards.append(reward)
            entropies.append(entropy)

            state = next_state
            if done:
                state = env.reset()
                result_queue.put(episode_reward)
                episode_reward = 0
                break

        R = torch.zeros(1, 1, device=device).clone().detach()
        if not done:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            _, value = local_model(state_tensor)
            R = value.detach()

        policy_loss = torch.tensor(0.0, device=device).clone().detach()
        value_loss = torch.tensor(0.0, device=device).clone().detach()
        gae = torch.zeros(1, 1, device=device).clone().detach()
        for i in reversed(range(len(rewards))):
            R = gamma * R + rewards[i]
            advantage = R - values[i]
            value_loss += 0.5 * advantage.pow(2)

            delta_t = rewards[i] + gamma * (values[i + 1] if i + 1 < len(rewards) else R) - values[i]
            gae = gae * gamma + delta_t

            policy_loss -= log_probs[i] * gae.detach() + entropy_beta * entropies[i]

        optimizer.zero_grad()
        total_loss = policy_loss + value_loss
        total_loss.backward()
        for global_param, local_param in zip(global_model.parameters(), local_model.parameters()):
            global_param._grad = local_param.grad
        optimizer.step()

        local_model.load_state_dict(global_model.state_dict())

        with global_counter.get_lock():
            global_counter.value += steps
        steps = 0

# -------- A3C Agent --------
class A3CAgent:
    def __init__(self, env_name, config):
        self.env_name = env_name
        self.config = config
        dummy_env = gym.make(env_name)
        obs_dim = dummy_env.observation_space.shape[0]
        action_dim = dummy_env.action_space.n
        self.global_model = ActorCritic(obs_dim, action_dim).to(device)
        self.global_model.share_memory()
        self.optimizer = optim.Adam(self.global_model.parameters(), lr=config.get("lr", 1e-3))
        self.max_steps = config.get("max_steps", 1e6)

    @safe_mps_op
    def train(self):
        mp.set_start_method('spawn', force=True)
        global_counter = mp.Value('i', 0)
        result_queue = mp.Queue()

        processes = []
        for worker_id in range(self.config.get("num_workers", 4)):
            p = mp.Process(target=worker_fn, args=(
                worker_id,
                self.env_name,
                self.global_model,
                self.optimizer,
                self.config,
                global_counter,
                self.max_steps,
                result_queue
            ))
            p.start()
            processes.append(p)

        episode_rewards = []
        while global_counter.value < self.max_steps:
            reward = result_queue.get()
            episode_rewards.append(reward)
            if len(episode_rewards) % 10 == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                print(f"Global Step: {global_counter.value}, Avg Reward (last 10): {avg_reward}")

        for p in processes:
            p.join()

    def save(self, path):
        torch.save(self.global_model.state_dict(), path)

    def load(self, path):
        self.global_model.load_state_dict(torch.load(path))

# -------- Ray Tune Trainable --------
def train_a3c_with_tune(config):
    agent = A3CAgent(env_name=config["env_name"], config=config)
    agent.train()
    # After training, evaluate
    env = gym.make(config["env_name"])
    state = env.reset()
    done = False
    total_reward = 0
    while not done:
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        logits, _ = agent.global_model(state_tensor)
        probs = torch.softmax(logits, dim=-1)
        action = probs.argmax().item()
        state, reward, done, _ = env.step(action)
        total_reward += reward
    tune.report(mean_reward=total_reward)

# -------- Example Ray Tune Config --------
def main():
    ray.init(ignore_reinit_error=True)
    search_space = {
        "lr": tune.grid_search([1e-3, 1e-4]),
        "entropy_beta": tune.grid_search([0.01, 0.001]),
        "gamma": 0.99,
        "t_max": 5,
        "num_workers": 4,
        "max_steps": 100000,
        "env_name": "CartPole-v1"
    }
    tune.run(
        train_a3c_with_tune,
        config=search_space,
        resources_per_trial={"cpu": 4},
        stop={"training_iteration": 1}
    )

if __name__ == "__main__":
    main()