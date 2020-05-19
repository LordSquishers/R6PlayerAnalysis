import json
import requests
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
import matplotlib.pyplot as plt


def init_data():
    local_data['maps'] = []


def store_data(data):
    all_maps = local_data['maps']
    for op, map_data in data.items():
        map, obj, is_attackers, optp = map_data

        operator, tp = optp

        if map not in all_maps:
            all_maps[map] = dict()

        if obj not in all_maps[map]:
            all_maps[map][obj] = dict()

        side = "Attackers" if is_attackers else "Defenders"
        if side not in all_maps[map][obj]:
            all_maps[map][obj][side] = dict()

        if operator not in all_maps[map][obj][side]:
            all_maps[map][obj][side][operator] = int(tp)
        else:
            count = all_maps[map][obj][side][operator]
            all_maps[map][obj][side][operator] = count + int(tp)

    local_data['maps'] = all_maps

    with open('op_map_data.json', 'w') as outfile:
        json.dump(local_data, outfile)


with open('op_map_data.json') as jsonFile:
    local_data = json.load(jsonFile)


if local_data is None:
    init_data()

with open('data_input.txt', 'r') as f:
    team_file = f.read().splitlines()

operator_data = dict()
is_attackers = True

for line in team_file:
    if line == "" or line[:3] == "#--":
        continue
    if line == "# Attackers #":
        is_attackers = True
    if line == "# Defenders #":
        is_attackers = False
    if line[:2] == "#M":
        map = line[3:]
    if line[:2] == "#B":
        objective = line[3:]
    if line[:2] == "#O":
        operator = line[6:]
        times_played = line[3:5]
        operator_data[operator] = (map, objective, is_attackers, (operator, times_played))
    if line[0] == "#":
        continue

store_data(operator_data)

