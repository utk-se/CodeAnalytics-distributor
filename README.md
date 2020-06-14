# CodeAnalytics-distributor

You need to run some python code and collect results on millions of repositories in parallel? This is the answer.

This project is one package that has two parts:

## Worker

Gets jobs from the jobserver and clones repos, runs analysis, and sends back results.

The worker uses a TOML configuration file, and imports the specified analysis function at startup. Each worker should have a unique name and token.

Depending on the analysis function you might have only one worker per node, or you could have as many as the hardware can support. Workers aren't parallel by themselves, but you can spin up as many as you need.

## Job Server

Connects to the mongoDB backend and provides a RESTful-like API for the workers to get jobs.

Run this in production behind a secure reverse proxy and use tokens to authenticate to allow the server to be accessible across the internet.
