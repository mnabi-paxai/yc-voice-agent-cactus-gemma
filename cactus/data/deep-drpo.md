# Deep DRPO

## Overview
Deep DRPO is a proposed reinforcement learning technique, an idea originating from "Norv's publication". Its primary innovation lies in simplifying the training process by entirely removing the value function component, which is typically used in many policy optimization algorithms. This deletion is intended to significantly reduce the computational cost and complexity associated with training, making the process more efficient and cheaper.

## Key Ideas
- **Value Function Deletion**: The central tenet of Deep DRPO is the complete removal of the value function from the training architecture. This contrasts with many standard RL algorithms that rely on value functions to estimate future rewards or evaluate states.
- **Cost-Effective Training**: By eliminating the value function, Deep DRPO aims to make the training process substantially cheaper, both in terms of computational resources and time.
- **Norv's Publication Idea**: The concept is attributed to "Norv's publication," suggesting it's a novel research direction or proposal.

## Source
- Session: 2026-04-19_090321
- Transcript excerpt: "Norv's publication idea around deep DRPO where the value function uh is deleted and makes training cheaper."
- Visual context: None observed

## Related Concepts
- [Direct Preference Optimization](direct-preference-optimization.md)
- [Proximal Policy Optimization](proximal-policy-optimization.md)