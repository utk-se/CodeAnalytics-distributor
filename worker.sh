#!/bin/bash
source ./venv/bin/activate
[[ -r ca-local-worker-config.toml ]] || {
  cp ca-local-worker-example.toml ca-local-worker-config.toml
}
python -m cadistributor.worker -v -c ca-local-worker-config.toml
