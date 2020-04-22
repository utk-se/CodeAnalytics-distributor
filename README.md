# CodeAnalytics-distributor

 - Get a job for a repo
 - Clone that repo
 - Run the analysis program on that repo
 - Collect results and compile into central db

This project is one package that has two parts:

## Worker

Gets jobs from the jobserver and clones repos, runs analysis, and sends back results.

## Job Server

Connects to the mongoDB backend and provides a RESTful-like API for the workers to get jobs.

