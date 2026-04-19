# Concept Wiki Index

## Core RL Methods for Language Models

- [Reinforcement Learning from Human Feedback (RLHF)](reinforcement-learning-from-human-feedback.md) - Standard multi-stage approach using reward models and policy optimization to align language models with human preferences
- [Direct Preference Optimization (DPO)](direct-preference-optimization.md) - Simplified alternative to RLHF that optimizes preferences directly without explicit reward modeling
- [Proximal Policy Optimization (PPO)](proximal-policy-optimization.md) - Actor-critic RL algorithm with clipped objectives, the standard method for RLHF's policy optimization phase
- [Group Relative Policy Optimization (GRPO)](group-relative-policy-optimization.md) - Efficient RL variant using group-based advantages instead of value functions, reducing computational overhead

## Reward and Supervision

- [Reward Modeling](reward-modeling.md) - Learning reward functions from human preferences to guide RL optimization
- [KL Divergence Regularization](kl-divergence-regularization.md) - Constraint preventing policies from deviating too far from reference behavior during RL training

## Applications

- [Mathematical Reasoning with Language Models](mathematical-reasoning-with-language-models.md) - Techniques for training LLMs on mathematical problem solving using specialized data and RL
- [Formal Theorem Proving](formal-theorem-proving.md) - Using LLMs to generate machine-verifiable proofs in formal languages like Lean


## Learned from Sessions

- [Narrative Paper Publication](narrative-paper-publication.md) — A discussion about the timeline for publishing a narrative paper, with a deadline approaching in two to three weeks.
- [GRPO](grpo.md) — A concept discussed from class that the speaker is considering for a narrative paper.
- [Loss Function](loss-function.md) — A specific element of a model or process that the speaker suggests focusing on when discussing GRPO.

---

This wiki synthesizes concepts from research papers on reinforcement learning, preference optimization, and mathematical reasoning for language models. Each article explains concepts in plain language accessible to junior researchers, summarizes key ideas from the sources, and highlights areas of agreement and disagreement across different approaches.
