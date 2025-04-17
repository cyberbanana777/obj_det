#!/bin/bash

# Открытие первого терминала
#lxterminal --title="CompVision C++" --command="bash -c '
#./actual&; exec bash;
#python3 Navigation_v3.0.py; exec bash;
#'"

# Задержка в 1 секунду
#sleep 1

# Открытие второго терминала
#lxterminal --title="NavBrain Python" --command="sleep 1;exec bash; bash -c 'python3 Navigation_v3.0.py; exec bash'"

./actual &
python3 Navigation_v3.0.py &

