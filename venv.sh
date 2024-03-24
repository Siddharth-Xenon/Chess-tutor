#!/bin/bash
PWD=`pwd`
python3.10 -m venv venv
echo $PWD
activate () {
    . $PWD/venv/bin/activate
}

activate

pip install -r requirements.txt
pip install pre-commit
pre-commit install
