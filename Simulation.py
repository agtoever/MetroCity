#!/usr/bin/env python2
"""
MetroCity - a simulation based on the Mini Metro game.

This library contains the Simulation class, needed to run a metro simulation.
The Simulation class is the main simulation object in which the simulation is
controlled and all user interaction takes place.
"""


import json
from PIL import Image, ImageDraw
import City


class Simulation:
    """ Encompasses all simulation methods and objects.

    Attributes:
        city        the city object where the simulation takes place
        limits      limits for number of trains, wagons and lines
        new_stations list of new station objects added in the last iteration.
    """

    # Class constants
    NEW_STATION_INTERVAL = 50           # interval for new station creation
    STATION_AVG_RATE_GROWTH = 1.001     # growth of the passenger spawn rate
    CITY_EXPANSION_INTERVAL = 25        # interval for the city edge increase
    CITY_EXPANSION_RATE = 1.1           # rate at which the city edge increases
    MAX_WAITING_TIME = 25               # max waiting time; ends the simulation
    IMG_SCALE = 20                      # scale factor for images

    def __init__(self):
        """ Initialize simulation """
        self.city = None
        self.new_stations = []

    def run(self, iters=1000, create_imgs=False, trace=False, usr_func=None):
        """ Run a single simulation until the end criteria are met.
            After each iterations, usr_func is called, with a json dump of
            all relevant data. The user should return a json parsable string
            with actions to be taken.
            Returns the number of passengers transported.
        """
        self.initialize_simulation()

        while self.continue_simulation(iters):
            # export simulation as json, give it to usr_func and process
            # the actions that are returned from usr_func
            self._process_user_actions(
                usr_func(self.export_json()), trace=trace)

            self.simulate_step(trace)

            if create_imgs:
                self.export_png()

        return len(self.city.arrived_passengers)

    def initialize_simulation(self):
        self.city = City.City()
        for _ in range(5):
            self.new_stations.append(self.city.add_station())

    def continue_simulation(self, max_iterations=1000):
        """ Returns a boolean indicating if the simulation should
            continue (True) of if it should be ended (False).
            The simulation must be ended if:
            - the maximum waiting time exceeds MAX_WAITING TIME, OR
            - the required number of iterations (max_iterations) is met.
        """
        waiting_times = [self.city.time - p.starttime
                         for p in self.city.all_passengers()]
        return (self.city.time < max_iterations and
                (len(waiting_times) == 0 or
                 max(waiting_times) < self.MAX_WAITING_TIME))

    def simulate_step(self, trace=False):
        """ Runs one full simulation step. The following steps are processed:
            - Enlarge the city at the specified interval
            - Add stations at the specified interval
            - Move all trains
            - Spawn passengers
            - Move all passengers
            - Increase the simulation clock (time)
        """
        # Enlarge city an specified interval
        if self.city.time % self.CITY_EXPANSION_INTERVAL == 0:
            self.city.edgelength = int(
                self.CITY_EXPANSION_RATE * self.city.edgelength)

        # Enlarge average passenger rate
        for s in self.city.stations:
            s.avgrate *= self.STATION_AVG_RATE_GROWTH

        # Add stations on specified interval
        self.new_stations = []
        if (self.city.time > 0 and
                self.city.time % self.NEW_STATION_INTERVAL == 0):
            self.new_stations.append(self.city.add_station())

        # Move all trains
        for train in self.city.trains:
            train.move()

        # Spawn passengers
        for station in self.city.stations:
            station.spawn_passengers(trace=trace)

        # Process all passengers movements
        for passenger in self.city.all_passengers():
            passenger.move()

        self.city.time += 1

    def _process_user_actions(self, json_string="", trace=False):
        """ Processes the user actions, supplied by a json string.
            The json string needs to be empty ("") if no actions are give,
            or it needs to have the following key-value pairs:
            - actions (list of action objects)

            The action object needs to have the following key-value pairs
            (note that the object_type and the action together actually
            define *what* has to be done; the rest is needed to specify
            to what object(s) and the specifics to do that):
            - object_type    string that refers to the type of object the
                             action applies to; 'Train' or 'Line' or 'Station'
                             (adding/moving/removing stations on a line are
                             about a Line, so object_type is 'Line')
            - object         id of the object (Train/Line/Station) to apply the
                             action to. Either int or string (for Line).
                             Can be omitted for action Add.
            - action         one of the following strings:
                             o 'add': adds a train or a line (adding a station
                               is not possible)
                             o 'remove': removes a train from a line or removes
                                a station from a line or clears an entire line.
                                In all these cases, the objects are
                                'decommissioned' but *not* removed (deleted),
                                so the line/train can be recommissioned by
                                adding a station to a line or by moving a
                                train to a line.
                             o 'move': moves a train or a station on a line
                               (moving a line is not possible).
                             o 'extend': adds a wagon to a train
                             o 'shrink': removes a wagon from a train
            - station        id of the station; only relevant if object_type
                             is Line and action is Add, Remove or Move or if
                             object_type is Train and action is Add or Move.
            - line           string of the line; only relevant in for adding
                             or moving trains.
            - direction      1 (forward) or -1 (backward). Only relevant for
                             adding or moving trains.
            - index          index of the position of the station to be moved
                             or added to the line, expressed as an index number
                             (zero-based) on the list of stations on the line.

            Example: add train 2 to line 'red' at station 3 driving forward:
            '{"actions": [{"object_type": "Train", "object_id": 2,
             "action": "Add", "station": 3, "line": "red", "direction": 1}]}'

            Example: add a (one) wagon to train 8:
            '{"actions": [{"object_type": "Train", "object_id": 8,
             "action": "Extend"}]}'

            Example: move station 5 to line 'red' from 12th to 2nd position:
            '{"actions": [{"object_type": "Line", "object_id": "red",
             "action": "Move", "station": 5, "index": 1}]}'

            Note: all keys and string values are case insensitive.
        """
        success = True

        if not json_string:
            return success
        actions = json.loads(json_string)

        for act in actions['actions']:
            (obj_type, obj, action, station, line, direction, index,
             success, err) = self._parse_action(act)
            if not success:
                print "Invalid action: {}; error: {}.".format(act, err)
            elif obj_type == 'train' and action == 'add':
                if direction is None:
                    direction = 1
                success &= self.city.add_train(line, station,
                                               direction, trace) is not None

            elif obj_type == 'train' and action == 'remove':
                self.city.remove_train(obj)

            elif obj_type == 'train' and action == 'move':
                self.city.move_train(obj, line, station, direction)

            elif obj_type == 'train' and action == 'extend':
                success &= self.city.add_wagon(obj)

            elif obj_type == 'train' and action == 'shrink':
                success &= self.city.remove_wagon(obj)

            elif obj_type == 'line' and action == 'add':
                success &= self.city.add_line([]) is not None

            elif obj_type == 'line' and action == 'remove':
                success &= self.city.clear_line()

            elif obj_type == 'station' and action == 'add':
                # if no index is given, add a station to the end of the list
                if index is None:
                    index = len(line.station_nodes)
                success &= self.city.add_station_to_line(line, obj, index)

            elif obj_type == 'station' and action == 'remove':
                success &= self.city.remove_station_from_line(line, obj)

            elif obj_type == 'station' and action == 'move':
                success &= self.city.move_station_in_line(line, obj, index)
            else:
                print "Invalid action received: {}".format(action)

        self.city._update_navmap()
        return success

    def _parse_action(self, action):
        """ Parse all key, value pairs in action and check their validity.
            Returns a tuple containing (object_type, object_id, action,
            station, line, direction, index, success, errors).
            Values not present are returned as None.
            - success is False if an error is found.
            - errors is a list of error messages if success if False
        """
        _VALID_ACTIONS = ['add', 'remove', 'move', 'extend', 'shrink']
        success = True
        obj_type = obj = act = station = line = direct = ind = None
        err = []
        line_dict = self.city.line_colors()
        station_dict = self.city.station_ids()

        # Set all keys and string values to lowercase utf-8
        for key, value in action.iteritems():
            if isinstance(value, basestring):
                action[key.lower()] = action.pop(key).lower()
            else:
                action[key.lower()] = action.pop(key)

        # Check if we can successfully extract a valid object_type
        if 'object_type' not in action.keys():
            success = False
            err = ["Key 'object_type' not found in action {}.".format(action)]
        elif action['object_type'] not in ['train', 'station', 'line']:
            success = False
            err = ["Invalid object type: {}.".format(obj_type)]
        else:
            obj_type = action['object_type'].lower()

            # Once we have a valid object_type, we can loop the other keys
            for key, value in action.iteritems():
                if key == 'object_type':
                    # already processed that.
                    pass
                elif key == 'object_id' and obj_type == 'train':
                    if action[key] in self.city.train_ids():
                        obj = self.city.trains[action[key]]
                    else:
                        success = False
                        err.append("Train {} not found.".format(action[key]))
                elif key == 'object_id' and obj_type == 'station':
                    if action[key] in station_dict.keys():
                        obj = station_dict[action[key]]
                    else:
                        success = False
                        err.append("Station {} not found.".format(action[key]))
                elif key == 'object_id' and obj_type == 'line':
                    if action[key] in line_dict.keys():
                        obj = line_dict[action[key]]
                    else:
                        success = False
                        err.append("Line {} not found.".format(action[key]))
                elif key == 'action':
                    act = action[key]
                    if act not in _VALID_ACTIONS:
                        success = False
                        err.append("Invalid action {}.".format(act))
                elif key == 'station':
                    if action[key] in station_dict.keys():
                        station = station_dict[action[key]]
                    else:
                        success = False
                        err.append("Station {} not found.".format(station))
                elif key == 'line':
                    if action[key] in line_dict.keys():
                        line = line_dict[action[key]]
                    else:
                        success = False
                        err.append("Line {} not found.".format(line))
                elif key == 'direction':
                    direct = action[key]
                    if direct not in [-1, 1]:
                        success = False
                        err.append("Direction {} not valid.".format(direct))
                elif key == 'index':
                    ind = action[key]
                else:
                    success = False
                    err.append("Invalid key found: {}.".format(key))

        return (obj_type, obj, act, station, line, direct, ind, success, err)

    def to_dict(self):
        """ Converts the main attributes to a key-value dict.

            Returns the following key-value pairs:
            - time (int)
              current simulation time (number of iterations)
            - new_stations (list of int)
              list of new stations in this iteration. The int refers to the
              id of the station (see stations)
            - num_stations, num_trains, num_lines, num_passengers (int)
              the total number of stations (including new ones), trains
              (including not on lines), lines and passengers (only the
              passengers on trains or stations are returned; the passengers
              that have arrived are not counted).
            - num_passengers_arrived (int)
              number of passengers arrived to their destination.
            - stations (list of Station objects; see to_dict() of Station)
            - lines    (list of Line objects; see to_dict() of Line)
            - trains (list of Train objects; see to_dict() of Train)

            Note that the passenger objects are given as part of the Station
            and Train objects. Therefore, there exists not passenger list on
            this level.
        """
        return {'city':
                {'time': self.city.time,
                 'num_new_stations': len(self.new_stations),
                 'new_stations': [s.idx for s in self.new_stations],
                 'num_stations': len(self.city.stations),
                 'num_trains': len(self.city.trains),
                 'max_trains': self.city.max_trains,
                 'free_wagons': self.city.free_wagons,
                 'num_lines': len(self.city.lines),
                 'max_lines': self.city.max_lines,
                 'num_passengers': len(self.city.all_passengers()),
                 'num_passengers_arrived': len(self.city.arrived_passengers),
                 'stations': [s.to_dict() for s in self.city.stations],
                 'lines': [l.to_dict() for l in self.city.lines],
                 'trains': [t.to_dict() for t in self.city.trains]
                 }
                }

    def export_json(self):
        """ Export relevant info of current situation as a json file.
            For an explanation of the data in the json files, see the
            to_dict() methods of the classes City (and Stations, Lines,
            Trains and Passengers)
        """
        return json.dumps(self.to_dict())

    def export_png(self):
        """ Export current situation as a png file.
            The file is saved in the current directory under the
            filename: 'metro_[6 digit serial number].png'
        """
        IMGLEN = self.city.edgelength * self.IMG_SCALE
        img = Image.new('RGB', (IMGLEN, IMGLEN), 'white')
        draw = ImageDraw.Draw(img)
        # Draw stations
        for station in self.city.stations:
            draw.rectangle(
                [tuple((station.position * self.IMG_SCALE) - 5 + IMGLEN // 2),
                 tuple((station.position * self.IMG_SCALE) + 5 + IMGLEN // 2)],
                fill='black')
            text = "{} ({})".format(station.idx, len(station.passengers))
            draw.text(
                tuple((station.position * self.IMG_SCALE) + 6 + IMGLEN // 2),
                text, fill='gray')

        # Draw lines
        for line in self.city.lines:
            xy = [tuple(node.station.position * self.IMG_SCALE + IMGLEN // 2)
                  for node in line.station_nodes]
            draw.line(xy, fill=line.color, width=self.IMG_SCALE//4)

        # Draw trains
        for train in [t for t in self.city.trains if t.line is not None]:
            xy = train.station_node.station.position
            if train.state == train.LEFT_STATION:
                xy2 = train.line.next_station(
                    train.station_node, train.direction)[0].station.position
                xy = (xy + xy2) * 0.5
            draw.ellipse(
                [tuple((xy * self.IMG_SCALE) - 5 + IMGLEN // 2),
                 tuple((xy * self.IMG_SCALE) + 5 + IMGLEN // 2)],
                fill=train.line.color, outline='black')
            text = "({})".format(len(train.passengers))
            draw.text(
                tuple((xy * self.IMG_SCALE) + [6, 0] + IMGLEN // 2),
                text, fill='gray')

        # save image
        img.save("metro_{:06}.png".format(self.city.time))
