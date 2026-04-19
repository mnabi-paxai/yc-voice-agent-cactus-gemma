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

- [Equipment Functionality Testing](equipment-functionality-testing.md) — The process of verifying that audio and visual hardware is working correctly for a communication session.
- [Live Session Readiness](live-session-readiness.md) — The state of being prepared for real-time communication, often involving coordination of participants and technical setup.

---

This wiki synthesizes concepts from research papers on reinforcement learning, preference optimization, and mathematical reasoning for language models. Each article explains concepts in plain language accessible to junior researchers, summarizes key ideas from the sources, and highlights areas of agreement and disagreement across different approaches.
- [Session Recording Test](session-recording-test.md) — The participant is testing the functionality of saving the current session, likely including the video recording.
- [Anonymity](anonymity.md) — The condition of being unknown or unidentifiable, often employed to protect privacy or enable unrestricted expression.
- [Content Attribution](content-attribution.md) — The act of identifying and crediting the original source, author, or creator of specific information, data, or media.
- [Narrative Paper Publication](narrative-paper-publication.md) — The process of preparing and submitting a scholarly paper that presents information in a story-like or descriptive format.
- [Testing Session](testing-session.md) — A dedicated period for evaluating a system, model, or experiment to assess its performance, functionality, or user experience.
- [Wiki Embedding Index](wiki-embedding-index.md) — This refers to the process of constructing a searchable index of wiki article embeddings, derived from existing knowledge, to facilitate information retrieval and understanding.
- [Deep DRPO](deep-drpo.md) — A reinforcement learning technique that simplifies training by deleting the value function to make it cheaper.
- [Direct Preference Optimization (DPO)](direct-preference-optimization-dpo.md) — A simpler and scalable reinforcement learning technique that directly optimizes policies based on human preferences.
- [Reward Modeling for Mathematics Proving](reward-modeling-for-mathematics-proving.md) — The application of reinforcement learning's reward modeling techniques to assist in the process of proving mathematical theorems.
- [Loss Functions in Reinforcement Learning](loss-functions-in-reinforcement-learning.md) — The objective functions used in reinforcement learning algorithms to guide policy updates and learning.
- [Trial and Error Learning](trial-and-error-learning.md) — A learning method where an agent learns through repeated attempts, observing the outcomes of its actions to find successful solutions.
- [Learning Without Explicit Parental Reward](learning-without-explicit-parental-reward.md) — A learning scenario where an agent develops skills or knowledge without direct, predefined reward signals or guidance from parents or external teachers.
- [Reinforcement Learning](reinforcement-learning.md) — A machine learning paradigm where an agent learns to make decisions by performing actions in an environment to maximize a cumulative reward signal.
- [Loss Functions in RL](loss-functions-in-rl.md) — The session discussed the role of loss functions in Reinforcement Learning, specifically comparing traditional RL objectives with newer techniques.
- [PPO Clipped Objective](ppo-clipped-objective.md) — The PPO clipped objective was introduced as a method to maintain stability when training the RL policy.
- [Direct Preference Optimization (DPO)](direct-preference-optimization-dpo.md) — DPO is a technique that reformulates the RL objective function into a classification loss, offering an alternative to traditional RL methods.
