# REFS-PUBLIC.md — Public References

> Record external public repositories, datasets, documentation, APIs, or other
> public resources that this repository utilizes or depends on.
> This file is tracked and intentionally kept free of private or local-only
> details.

## Public Repositories

- https://github.com/JayDDee/cpuminer-opt — CPU miner cloned by the host setup flow
- https://github.com/tpruvot/ccminer — NVIDIA CUDA miner cloned by the host setup flow
- https://github.com/ckolivas/cgminer — OpenCL miner cloned by the host setup flow

## Public Datasets and APIs

- https://solo.ckpool.org/ — upstream Solo CKPool homepage and published
  connection parameters
- https://solo.ckpool.org/pool/pool.status — public pool-status endpoint used by
  the CLI status command

## Documentation and Specifications

- https://solo.ckpool.org/ — upstream guidance for host, port, worker naming,
  and regional pool selection
- https://rpmfusion.org/Configuration — RPM Fusion package-source reference used by miner installation
- https://download1.rpmfusion.org/ — RPM Fusion release-package base used by the Fedora miner installer
- https://developer.nvidia.com/cuda-downloads — CUDA toolkit reference for the NVIDIA miner build path
- https://developer.download.nvidia.com/compute/cuda/repos/ — NVIDIA CUDA repository base printed by the NVIDIA miner installer
- https://cryptography.io/ — optional encrypted-wallet export dependency

## Notes

- This repository intentionally uses `solo.ckpool.org` as the default upstream
  and treats the status endpoint as an informational, non-authenticated health
  signal.
