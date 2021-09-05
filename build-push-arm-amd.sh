#!/usr/bin/env bash
docker buildx build --platform linux/amd64,linux/arm64 --push -t gergnz/mcshop:latest .
