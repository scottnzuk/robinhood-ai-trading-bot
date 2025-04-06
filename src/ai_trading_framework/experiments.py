import optuna
from ai_trading_framework.trainers.supervised_trainer import SupervisedTrainer

def objective(trial):
    # Suggest hyperparameters
    lr = trial.suggest_loguniform('learning_rate', 1e-5, 1e-1)
    batch_size = trial.suggest_categorical('batch_size', [32, 64, 128, 256])
    dropout = trial.suggest_uniform('dropout', 0.0, 0.5)
    num_layers = trial.suggest_int('num_layers', 1, 4)
    hidden_size = trial.suggest_categorical('hidden_size', [64, 128, 256, 512])

    hyperparams = {
        'learning_rate': lr,
        'batch_size': batch_size,
        'dropout': dropout,
        'num_layers': num_layers,
        'hidden_size': hidden_size
    }

    # Instantiate trainer with trial hyperparameters
    trainer = SupervisedTrainer(hyperparams)

    # Train and evaluate
    score = trainer.train_and_evaluate()

    # Optuna minimizes by default; negate if maximizing
    return -score

def main():
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=50)

    print("Best trial:")
    trial = study.best_trial
    print(f"  Value: {-trial.value}")
    print("  Params: ")
    for key, value in trial.params.items():
        print(f"    {key}: {value}")

if __name__ == "__main__":
    main()