import json
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
import matplotlib.pyplot as plt
import urllib
from urllib.request import Request

op_conv_sheet = pd.read_csv('op_conversion.csv', delimiter=',')
url_player = 'https://r6.apitab.com/search/xbl/'
url_id = 'https://r6.apitab.com/player/'
url_refresh = 'https://r6.apitab.com/update/'
KEY_SEPARATOR = "?cid="
API_KEY = 'YOUR_API_KEY_FROM_R6TAB'

NUM_OPS = 7
EXTRA_DATA_WEIGHT = 1


def load_op_map():
    with open('op_map_data.json') as jsonFile:
        local_data = json.load(jsonFile)
        return local_data


def get_op_by_id(ID):
    return op_conv_sheet[ID]


def get_id_by_op(operator):
    id_name = op_conv_sheet.loc[0]
    for ID, name in id_name.items():
        if name == operator:
            return ID


def get_time_played(op_name, so_tp):
    ID = get_id_by_op(op_name)
    for i in range(0, len(so_tp)):
        if so_tp[i][0] == ID:
            return so_tp[i][1]


def get_kills(op_name, so_kills):
    ID = get_id_by_op(op_name)
    for i in range(0, len(so_kills)):
        if so_kills[i][0] == ID:
            return so_kills[i][1]


def get_deaths(op_name, so_deaths):
    ID = get_id_by_op(op_name)
    for i in range(0, len(so_deaths)):
        if so_deaths[i][0] == ID:
            if so_deaths[i][1] == 0:
                return 1
            return so_deaths[i][1]


def get_kd(op_name, so_kills, so_deaths):
    return get_kills(op_name, so_kills) / get_deaths(op_name, so_deaths)


def get_percent_op(op, so_tp, ttd):
    return get_time_played(op, so_tp) * 100 / ttd


def format_op_dict(d, ttd, so_tp, so_kills, so_deaths):
    output = ""
    ops = list(d.values())
    for i in range(0, len(ops)):
        output += (ops[i] +
                   ": " +
                   str(round(get_percent_op(ops[i], so_tp, ttd), 2))
                   + "% (" + str(round(get_kd(ops[i], so_kills, so_deaths), 2)) + ") , ")
    return output[:-2]


def get_id(name):
    url = url_player + urllib.parse.quote(name) + KEY_SEPARATOR + API_KEY

    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    search_req = json.loads(urllib.request.urlopen(request).read())

    players = search_req["players"]
    if len(players) > 1:
        print(str(len(players)) + " results for player \"" + name + "\". What level are they?")
        rank = input()

        for p, data in players.items():
            if int(rank) == data["stats"]["level"]:
                return p, data["profile"]["p_name"]
    else:
        if not players:
            print(name + " not found. Please retype:")
            return get_id(input())
        for p, data in players.items():
            return p, data["profile"]["p_name"]


def get_json(player_id):
    url = (url_id + player_id + KEY_SEPARATOR + API_KEY)
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    search_req = json.loads(urllib.request.urlopen(request).read())
    return search_req


def refresh_player(player_id, player_name):
    url = (url_refresh + player_id + KEY_SEPARATOR + API_KEY)
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    urllib.request.urlopen(request)
    print(player_name + " has been refreshed.")


def print_stats(player_name, show_op_stats):
    ID, actual_name = get_id(player_name)
    if ID is None:
        return None
    player_req = get_json(ID)

    p_ranked = player_req["ranked"]

    rank = p_ranked["rankname"]
    kpm = p_ranked["killpermatch"]
    dpm = p_ranked["deathspermatch"]

    p_ops = player_req["operators"]

    op_kills = dict()
    op_deaths = dict()
    op_tp = dict()

    i = 0
    for operator, op_data in p_ops.items():
        id = op_data["id"]
        kills = op_data["overall"]["kills"]
        deaths = op_data["overall"]["deaths"]
        tp = op_data["overall"]["timeplayed"]

        op_kills[id] = kills
        op_deaths[id] = deaths
        op_tp[id] = tp

        i += 1

    so_kills = sorted(op_kills.items(), key=lambda x: x[1], reverse=True)
    so_deaths = sorted(op_deaths.items(), key=lambda x: x[1], reverse=True)
    so_tp = sorted(op_tp.items(), key=lambda x: x[1], reverse=True)

    total_time_played = 0
    for i in range(0, len(so_tp)):
        total_time_played += so_tp[i][1]

    t5pa = dict()
    t5pd = dict()

    complete = False
    i = 0
    while not complete:
        op_at_index = get_op_by_id(so_tp[i][0])
        if op_at_index[1] == 'Attacker' and len(t5pa) < NUM_OPS:
            t5pa[i] = op_at_index[0]

        if op_at_index[1] == 'Defender' and len(t5pd) < NUM_OPS:
            t5pd[i] = op_at_index[0]

        complete = len(t5pa) >= NUM_OPS and len(t5pd) >= NUM_OPS
        i += 1

    if dpm == 0:
        dpm = 1

    print("Player: " + actual_name + " (" + str(player_req["stats"]["level"]) + ")")
    print("Rank: " + rank + " [" + str(p_ranked["actualmmr"]) + "]")

    if show_op_stats:
        print("\nKills per Match: " + str(kpm) + "\nDeaths per Match: " + str(dpm))

    print("\n---Time Played (K/D)---\nTime Played: " + str(int(total_time_played / 3600.0)) + " hours")

    if show_op_stats:
        print("Attackers:")
        print(format_op_dict(t5pa, total_time_played, so_tp, so_kills, so_deaths))
        print("\nDefenders:")
        print(format_op_dict(t5pd, total_time_played, so_tp, so_kills, so_deaths))
    print("\n=============================\n")

    percent_ops = dict()
    attack_ops = list(t5pa.values())
    for i in range(0, len(attack_ops)):
        percent_ops[i] = (attack_ops[i], get_percent_op(attack_ops[i], so_tp, total_time_played))
    defense_ops = list(t5pd.values())
    for i in range(0, len(defense_ops)):
        percent_ops[i + NUM_OPS] = (defense_ops[i], get_percent_op(defense_ops[i], so_tp, total_time_played))

    player_score = (kpm / dpm) * p_ranked["actualmmr"]

    return percent_ops, kpm, dpm, player_name, player_score


def list_players_in_skill(scored_players):
    for i in range(0, len(scored_players)):
        score, name = scored_players[i][1]
        print(name + " | " + str(int(score)))


def get_op_map_percent(operator, side, obj, map_data):
    obj_data = map_data[obj]

    total_entries = 0
    for op, count in obj_data[side].items():
        total_entries = total_entries + count

    if operator in obj_data[side]:
        return obj_data[side][operator] * EXTRA_DATA_WEIGHT / total_entries
    else:
        return 1


def team_stats(names, show_op_graph, show_op_stats, per_objective_graphs, map_choice):
    percents = dict()
    op_percents = dict()
    player_scores = dict()
    missed = 0

    total_kills_per_match = 0
    total_deaths_per_match = 0

    for i in range(0, len(names)):
        percent, kill_pm, death_pm, player_name, player_score = print_stats(names[i], show_op_stats)
        if percent is None:
            missed += 1
            continue
        percents[i] = percent
        total_kills_per_match += kill_pm
        total_deaths_per_match += death_pm
        player_scores[i] = player_score, player_name

    for entry, data in percents.items():
        if entry is None or data is None:
            continue
        for index, op_data in data.items():
            (op, percent) = op_data
            if op in op_percents:
                op_percents[op] += percent
            else:
                op_percents[op] = percent

    sorted_percentages = sorted(op_percents.items(), key=lambda x: x[1], reverse=True)
    scored_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)

    top_attackers = dict()
    top_defenders = dict()

    avg_score = 0

    for i, data in scored_players:
        score, name = data
        avg_score += score

    avg_score /= 5 * 1000

    if total_deaths_per_match == 0:
        total_deaths_per_match = 1
    match_score = int(total_kills_per_match * 1000 / total_deaths_per_match)
    match_score *= avg_score
    match_score = int(match_score)

    for op, percent in sorted_percentages:
        if get_op_by_id(get_id_by_op(op))[1] == "Attacker" and len(top_attackers) < NUM_OPS:
            top_attackers[len(top_attackers)] = (op, percent)
        if get_op_by_id(get_id_by_op(op))[1] == "Defender" and len(top_defenders) < NUM_OPS:
            top_defenders[len(top_defenders)] = (op, percent)

        if len(top_attackers) >= NUM_OPS and len(top_defenders) >= NUM_OPS:
            break

    print("Accounts for " + str(len(names) - missed) + " out of " + str(len(names)) + " members.")
    print("\n~~~~~~[TEAM BREAKDOWN]~~~~~~\n")
    print("Match Score: " + str(match_score))
    print("\nPlayers:")

    list_players_in_skill(scored_players)

    plt.style.use('dark_background')
    plt.figure(figsize=(2 * NUM_OPS, 5))

    if per_objective_graphs:
        ignore = False
        op_per_map = load_op_map()

        if map_choice in op_per_map['maps']:
            map_data = op_per_map['maps'][map_choice]
        else:
            print('\nCould not find map. Try again:')
            map_choice = input()
            if map_choice not in op_per_map['maps']:
                print("\nCould not find, try running without # obj #.")
                ignore = True

        if not ignore:
            for obj, ops in map_data.items():

                p_a = list()
                n_a = list()

                for index in top_attackers:
                    (op, percent) = top_attackers[index]
                    p_a.append(percent * get_op_map_percent(op, "Attackers", obj, map_data))
                    n_a.append(op)

                if show_op_graph:
                    plt.bar(n_a, p_a)

                p_d = list()
                n_d = list()

                for index in top_defenders:
                    (op, percent) = top_defenders[index]
                    p_d.append(percent * get_op_map_percent(op, "Defenders", obj, map_data))
                    n_d.append(op)

                if show_op_graph:
                    plt.bar(n_d, p_d)

                plt.savefig('graphs/graph' + str(match_score) + '_' + obj + '.png')

    if not per_objective_graphs or ignore:
        p_a = list()
        n_a = list()

        for index in top_attackers:
            (op, percent) = top_attackers[index]
            p_a.append(percent)
            n_a.append(op)

        if show_op_graph:
            plt.bar(n_a, p_a)

        p_d = list()
        n_d = list()

        for index in top_defenders:
            (op, percent) = top_defenders[index]
            p_d.append(percent)
            n_d.append(op)

        if show_op_graph:
            plt.bar(n_d, p_d)

        plt.show()

    return match_score, scored_players


def run_program():
    with open('input.txt', 'r') as f:
        team_file = f.read().splitlines()

    names = list()
    names2 = list()

    is_first_team = True
    show_op_stats = False
    refresh_request = False
    per_obj = False

    map_name = ""

    for line in team_file:
        if line == "":
            continue

        if line[0] == "#":
            if line[:3] == "#NO":
                global NUM_OPS
                NUM_OPS = int(line[4:])
            if line[:4] == "#EDW":
                global EXTRA_DATA_WEIGHT
                EXTRA_DATA_WEIGHT = int(line[5:]) / 100.0
            if line == "# Team 1 #":
                is_first_team = True
            if line == "# Team 2 #":
                is_first_team = False
            if line == "# details #":
                show_op_stats = True
            if line == "# refresh #":
                refresh_request = True
            if line == "# obj #":
                per_obj = True
            if line[:7] == "# map #":
                map_name = line[8:]
            continue

        if is_first_team:
            names.append(line)
        else:
            names2.append(line)

    if not refresh_request:
        print("\nTeam 1:")
        team_1_score, team_1_players = team_stats(names, True, show_op_stats, per_obj, map_name)

        if len(names2) > 0:
            print("\nTeam 2:")
            team_2_score, team_2_players = team_stats(names2, True, show_op_stats, per_obj, map_name)

        print("\nScore difference: " + str(team_1_score - 2718))
        # plt.savefig('graphs/graph_' + str(team_1_score))
    else:
        for name in names:
            player_id, player_name = get_id(name)
            refresh_player(player_id, player_name)


run_program()
