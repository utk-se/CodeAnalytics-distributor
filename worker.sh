#!/bin/bash
source ./venv/bin/activate
[[ -r ca-local-worker-config.toml ]] || {
  echo "Copying example config..."
  cp ca-local-worker-example.toml ca-local-worker-config.toml
}
python3 -m cadistributor.worker.jsonresults -v -c ca-local-worker-config.toml
