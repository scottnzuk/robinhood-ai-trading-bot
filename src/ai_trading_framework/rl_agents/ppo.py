import torch  
import torch.nn as nn  
import torch.optim as optim  
import numpy as np  
import gym  
from ray import tune  

class PPOPolicy(nn.Module):  
    def __init__(self, obs_dim, act_dim, hidden_size=64):  
        super().__init__()  
        self.fc = nn.Sequential(  
            nn.Linear(obs_dim, hidden_size),  
            nn.ReLU(),  
            nn.Linear(hidden_size, hidden_size),  
            nn.ReLU()  
        )  
        self.actor = nn.Linear(hidden_size, act_dim)  
        self.critic = nn.Linear(hidden_size, 1)  
  
    def forward(self, x):  
        x = self.fc(x)  
        return self.actor(x), self.critic(x)  
  
def ppo_train(config):  
    env = gym.make(config.get("env_name", "CartPole-v1"))  
    obs_dim = env.observation_space.shape[0]  
    act_dim = env.action_space.n  
  
    policy = PPOPolicy(obs_dim, act_dim, hidden_size=config.get("hidden_size", 64))  
    optimizer = optim.Adam(policy.parameters(), lr=config.get("lr", 1e-3))  
  
    gamma = config.get("gamma", 0.99)  
    clip_param = config.get("clip_param", 0.2)  
    epochs = config.get("epochs", 10)  
    batch_size = config.get("batch_size", 500)  
  
    for iteration in range(epochs):  
        obs_list, act_list, rew_list, done_list, logp_list, val_list = [], [], [], [], [], []  
        obs = env.reset()  
        done = False  
        ep_rews = []  
  
        while len(obs_list) < batch_size:  
            obs_tensor = torch.FloatTensor(obs).unsqueeze(0)  
            logits, value = policy(obs_tensor)  
            dist = torch.distributions.Categorical(logits=logits)  
            action = dist.sample()  
            logp = dist.log_prob(action)  
  
            next_obs, reward, done, _ = env.step(action.item())  
  
            obs_list.append(obs)  
            act_list.append(action.item())  
            rew_list.append(reward)  
            done_list.append(done)  
            logp_list.append(logp.item())  
            val_list.append(value.item())  
  
            obs = next_obs  
            ep_rews.append(reward)  
  
            if done:  
                obs = env.reset()  
                done = False  
                ep_rews = []  
  
        # Convert to tensors  
        obs_tensor = torch.FloatTensor(obs_list)  
        act_tensor = torch.LongTensor(act_list)  
        old_logp_tensor = torch.FloatTensor(logp_list)  
        returns = compute_returns(rew_list, done_list, val_list, gamma)  
  
        # PPO update  
        logits, values = policy(obs_tensor)  
        dist = torch.distributions.Categorical(logits=logits)  
        logp = dist.log_prob(act_tensor)  
        ratio = torch.exp(logp - old_logp_tensor)  
        advantage = returns - torch.FloatTensor(val_list)  
        surr1 = ratio * advantage  
        surr2 = torch.clamp(ratio, 1.0 - clip_param, 1.0 + clip_param) * advantage  
        policy_loss = -torch.min(surr1, surr2).mean()  
        value_loss = nn.functional.mse_loss(values.squeeze(), returns)  
  
        optimizer.zero_grad()  
        (policy_loss + value_loss).backward()  
        optimizer.step()  
  
        tune.report(loss=(policy_loss + value_loss).item(), reward=np.sum(rew_list)/epochs)  
  
def compute_returns(rewards, dones, values, gamma):  
    returns = []  
    R = 0  
    for r, d, v in zip(reversed(rewards), reversed(dones), reversed(values)):  
        if d:  
            R = 0  
        R = r + gamma * R  
        returns.insert(0, R)  
    return torch.FloatTensor(returns)  
  
if __name__ == "__main__":  
    search_space = {  
        "lr": tune.grid_search([1e-3, 5e-4]),  
        "gamma": tune.grid_search([0.95, 0.99]),  
        "clip_param": tune.grid_search([0.1, 0.2]),  
        "hidden_size": 64,  
        "epochs": 10,  
        "batch_size": 500,  
        "env_name": "CartPole-v1"  
    }  
    tune.run(ppo_train, config=search_space)