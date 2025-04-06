import ray
from ray import tune
from ray.tune import Trainable
from src.ai_trading_framework.rl_agents import ppo, a3c

class PPOTrainable(Trainable):
    def setup(self, config):
        self.config = config
        self.agent = ppo.PPOAgent(**config)

    def step(self):
        result = self.agent.train_step()
        return {
            "episode_reward_mean": result.get("reward", 0),
            "loss": result.get("loss", 0),
            "custom_metrics": result.get("metrics", {})
        }

    def save_checkpoint(self, checkpoint_dir):
        return self.agent.save(checkpoint_dir)

    def load_checkpoint(self, checkpoint_path):
        self.agent.load(checkpoint_path)

class A3CTrainable(Trainable):
    def setup(self, config):
        self.config = config
        self.agent = a3c.A3CAgent(**config)

    def step(self):
        result = self.agent.train_step()
        return {
            "episode_reward_mean": result.get("reward", 0),
            "loss": result.get("loss", 0),
            "custom_metrics": result.get("metrics", {})
        }

    def save_checkpoint(self, checkpoint_dir):
        return self.agent.save(checkpoint_dir)

    def load_checkpoint(self, checkpoint_path):
        self.agent.load(checkpoint_path)

def get_search_space(agent_type):
    if agent_type == "ppo":
        return {
            "learning_rate": tune.loguniform(1e-5, 1e-2),
            "gamma": tune.uniform(0.9, 0.999),
            "clip_param": tune.uniform(0.1, 0.3),
            "entropy_coef": tune.uniform(0.0, 0.02),
            "value_loss_coef": tune.uniform(0.1, 1.0),
            "num_epochs": tune.choice([3, 5, 10]),
            "batch_size": tune.choice([64, 128, 256])
        }
    elif agent_type == "a3c":
        return {
            "learning_rate": tune.loguniform(1e-5, 1e-2),
            "gamma": tune.uniform(0.9, 0.999),
            "entropy_coef": tune.uniform(0.0, 0.02),
            "value_loss_coef": tune.uniform(0.1, 1.0),
            "max_grad_norm": tune.choice([0.5, 1.0, 5.0]),
            "update_freq": tune.choice([5, 10, 20])
        }
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

def run_tuning(agent_type="ppo", num_samples=20, max_iters=50):
    search_space = get_search_space(agent_type)
    trainable_cls = PPOTrainable if agent_type == "ppo" else A3CTrainable

    analysis = tune.run(
        trainable_cls,
        config=search_space,
        num_samples=num_samples,
        stop={"training_iteration": max_iters},
        checkpoint_at_end=True,
        local_dir="ray_results",
        metric="episode_reward_mean",
        mode="max"
    )
    return analysis