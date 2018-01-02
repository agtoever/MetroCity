#!/usr/bin/env python2
"""
MetroCity - a simulation based on the Mini Metro game.

This library contains classes to run a metro simulation, where you have to
manage a growing amount of passengers in a growing city with a growing amount
of metro stations. Your task is, with limited resources, to design metro lines,
commission trains and wagons in order to avoid passengers waiting too long
for their metro trains.

The following classes are present as separate modules:
    Simulation    the main object with which to interact with
    City          contains most other objects: stations, trains and lines
    Station       a metro station where passengers come from and go to
    Train         a metro train that can be commissioned on a line
    Line          a sequence of stations where a train runs on
    Passenger     the hero of our sim: a simple commuter going from A to B
"""


import json
import Simulation


def user_function(json_string):
    """ Sample user function, processing the json object that describes the
        current state of the simulation. This function:
        1. adds a new station if a new station is added to the simulation
        2. tries to add trains every turn
    """
    sim = json.loads(json_string)
    line_color = 'blue'  # default color of the first line

    # Initialize my actions for this turn
    # see documentation of Simulation._process_user_actions() for the details
    my_turn = {'actions': []}

    # Add a new metro line at the beginning of the simulation and add 3 trains
    if sim['city']['time'] == 0:
        my_turn['actions'].append({'object_type': 'line', 'action': 'add'})

    # Always add all new stations to the end of the line
    for station_id in sim['city']['new_stations']:
        my_turn['actions'].append({
            'object_type': 'station',
            'object_id': station_id,
            'action': 'add',
            'line': line_color,
            'index': -1})

    # Add a train every 2 turns if possible
    if (sim['city']['num_trains'] < sim['city']['max_trains'] and
            sim['city']['time'] % 2 == 0):
        my_turn['actions'].append({
            'object_type': 'train',
            'action': 'add',
            'line': line_color,
            'station': 0})

    # Return my turn in json format
    return json.dumps(my_turn)


def run_sample_simulation():
    """ example simulation """
    sim = Simulation.Simulation()
    sim.run(usr_func=user_function, iters=1000, create_imgs=True)

    print "Simulation ended after {} iterations.".format(sim.city.time)
    print "{} passengers arrived; {} are left in the simulation.".format(
        len(sim.city.arrived_passengers), len(sim.city.all_passengers()))


def main():
    run_sample_simulation()


if __name__ == '__main__':
    main()
