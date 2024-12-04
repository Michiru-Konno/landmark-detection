#!/bin/bash

# システム依存パッケージのインストール
apt-get update && apt-get install -y \
    build-essential cmake libboost-all-dev

# MAKEFLAGSを設定して並列ビルド数を制限
export MAKEFLAGS="-j4"

# Pythonパッケージのインストール
pip install --upgrade pip
pip install -r requirements.txt
