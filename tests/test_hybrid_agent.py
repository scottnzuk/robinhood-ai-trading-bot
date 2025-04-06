import pytest
import torch
from ai_trading_framework.models.hybrid_agent import HybridMultimodalAgent
from ai_trading_framework.trainers.hybrid_agent_trainer import HybridAgentTrainer

@pytest.fixture
def dummy_inputs():
    batch_size = 4
    seq_len = 20
    dims = {
        'ohlcv': 128,
        'indicators': 64,
        'orderbook': 64,
        'sentiment': 32,
        'events': 32,
        'blockchain': 32,
    }
    inputs = {}
    for k, d in dims.items():
        inputs[k] = torch.randn(batch_size, seq_len, d)
    return inputs

@pytest.fixture
def dummy_targets():
    batch_size = 4
    horizons = (10, 60, 240)
    targets = {h: torch.randn(batch_size) for h in horizons}
    aux_targets = {h: torch.randint(0, 2, (batch_size,)) for h in horizons}
    return targets, aux_targets

@pytest.fixture
def model_and_trainer():
    dims = {
        'ohlcv': 128,
        'indicators': 64,
        'orderbook': 64,
        'sentiment': 32,
        'events': 32,
        'blockchain': 32,
    }
    model = HybridMultimodalAgent(input_dims=dims)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    trainer = HybridAgentTrainer(model, optimizer)
    return model, trainer

@pytest.mark.timeout(30)
@pytest.mark.flaky(reruns=2)
def test_forward_pass(dummy_inputs, model_and_trainer):
    model, _ = model_and_trainer
    outputs = model(dummy_inputs)
    assert isinstance(outputs, dict)
    for horizon, out in outputs.items():
        assert 'mean' in out and 'log_var' in out and 'aux_logits' in out

@pytest.mark.timeout(30)
@pytest.mark.flaky(reruns=2)
def test_training_step(dummy_inputs, dummy_targets, model_and_trainer):
    _, trainer = model_and_trainer
    targets, aux_targets = dummy_targets
    loss = trainer.update(dummy_inputs, targets, aux_targets)
    assert loss >= 0.0

@pytest.mark.timeout(30)
@pytest.mark.flaky(reruns=2)
def test_continual_learning(dummy_inputs, dummy_targets, model_and_trainer):
    _, trainer = model_and_trainer
    targets, aux_targets = dummy_targets
    for _ in range(5):
        trainer.add_to_replay(dummy_inputs, targets, aux_targets)
    loss = trainer.continual_update(batch_size=4)
    assert loss is None or loss >= 0.0