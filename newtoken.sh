#!/bin/zsh
echo -n '{"name": "'$1'", "token": "' && head /dev/urandom | tr -dc A-Za-z0-9 | head -c 30 && echo '"}'
