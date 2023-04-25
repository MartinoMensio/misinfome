#!/bin/sh
set -e

git pull
git submodule update --init --recursive