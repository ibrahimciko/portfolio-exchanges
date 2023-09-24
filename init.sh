#!/bin/bash

#install make file
sudo yum install make -y

# Check if the provided environment variables are non-empty and non-zero before setting the ARGS
BUFFER_SIZE_ARG=""
if [ -n "${BufferSize}" ] && [ "${BufferSize}" != "0" ]; then
  BUFFER_SIZE_ARG="--buffer-size ${BufferSize}"
fi

SLEEP_DURATION_ARG=""
if [ -n "${SleepDuration}" ] && [ "${SleepDuration}" != "0" ]; then
  SLEEP_DURATION_ARG="--sleep-duration ${SleepDuration}"
fi

WRITER_TYPE_ARG=""
if [ -n "${WriterType}" ] && [ "${WriterType}" != "0" ]; then
  WRITER_TYPE_ARG="--writer-type ${WriterType}"
fi

# add local bin to path
export PATH="/root/.local/bin:$PATH"
# Set environment variables
APP_ENV=${1:-development}
# Append APP_ENV to /etc/environment if it's not already there
grep -qxF "APP_ENV=${APP_ENV}" /etc/environment || echo "APP_ENV=${APP_ENV}" | sudo tee -a /etc/environment
source /etc/environment

# Use Makefile for setup and run
make setup
