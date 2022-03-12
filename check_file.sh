#!/bin/bash

if [ "$1" == "" ]; then
  echo "no argument. set file path"
  exit 1
fi

source venv/bin/activate
python3 $1
deactivate
