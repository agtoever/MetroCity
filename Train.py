#!/usr/bin/env python2
"""
MetroCity - a simulation based on the Mini Metro game.

This library contains the Train class, which represents the metro train.
Trains are commissioned to lines and transport passengers.
"""


class Train:
    """ Represents a train; contains passengers

    Attributes:
        city         the city the train runs through
        capacity     the maximum capacity of the train (number of passengers)
        passengers   passengers in the train; list of passenger objects
        trace        boolean indicating if the history list should be kept
        history      list of status strings (such as entering a station)
        state        train's situation: AT_STATION or LEFT_STATION
        line         the line the train is commissioned on; None if none
        direction    direction of the train: FOREWARD or BACKWARD
        station_node current of last visited station (see state)
        idx          unique id of the train
    """

    # Class constants
    AT_STATION = 0
    LEFT_STATION = 1
    STATES = {AT_STATION: 'at station', LEFT_STATION: 'left station'}
    FOREWARD = 1
    BACKWARD = -1
    DIRECTION = {1: 'foreward', -1: 'backward'}
    MAX_WAGONS = 5
    WAGON_CAPACITY = 6

    def __init__(self, city=None, trace=False):
        """ Initialize a new train.
            Note: use the set_line method to deploy the train. """
        self.city = city
        self.capacity = self.WAGON_CAPACITY
        self.passengers = []
        self.trace = trace
        self.history = []
        self.state = self.AT_STATION
        self.line = None
        self.direction = self.FOREWARD
        self.station_node = None
        self.idx = len(self.city.trains)

    def set_line(self, line, station=None, direction=1):
        """ Put a train on a line, at a station with a cetrain direction.
            Updates line, direction and station.
            Puts the train in forward direction at the first station of
            the line if arguments station and/or direction are not given.
            Returns False if station is not on line. Returns True otherwise.
        """
        if station is None:
            node = line.station_node[0]
        else:
            node = line.find_node(station)
            if node is None:
                return False
        self.station_node = node
        self.state = self.AT_STATION
        self.line = line
        self.direction = direction
        if self.trace:
            self.history.append(
                '{}: train put on line {} at station {} heading {}.'.format(
                    self.city.time, line.color,
                    self.station_node.station.idx,
                    self.DIRECTION[direction]))

    def add_wagon(self):
        """ Add a wagon to the train.
            Updates capacity upon success.
            Returns a boolean that indicates if this has succeeded.
        """
        if self.capacity // self.WAGON_CAPACITY >= self.MAX_WAGONS:
            return False
        self.capacity += self.WAGON_CAPACITY
        if self.trace:
            self.history.append('{}: added wagon. New capacity: {}.'.format(
                self.city.time, self.capacity))
        return True

    def remove_wagon(self):
        """ Removes a wagon from the train.
            Updates capacity upon success.
            If there are more passengers than capacity after removing the
            wagon, the last entered passengers are dropped at the current
            station or the last station the train stoped at.
            Returns a boolean that indicates if this has succeeded.
        """
        if self.capacity // self.WAGON_CAPACITY <= 1:
            return False
        self.capacity -= self.WAGON_CAPACITY

        if self.trace:
            self.history.append('{}: removed wagon. New capacity: {}.'.format(
                self.city.time, self.capacity))

        while len(self.passengers) > self.capacity:
            p = self.passengers.pop()
            self.station_node.station.passengers.append(p)
            if p.trace:
                p.history.append(('{}: removed passenger from train ' +
                                  ' at station {}.').format(
                                      self.city.time,
                                      self.station_node.station.idx))
        return True

    def move(self):
        """ Move the train one step. Updates state and station.
            Station is only changes after arriving at the next station.
        """
        if self.state == self.AT_STATION:
            self.state = self.LEFT_STATION
        else:
            self.state = self.AT_STATION
            self.station_node, self.direction = \
                self.line.next_station(self.station_node, self.direction)
            if self.trace:
                self.history.append(
                    ('{}: arrived at station {} with {} passengers aboard ' +
                     'and {} passengers waiting at the station.').format(
                        self.city.time,
                        self.station_node.station.idx,
                        len(self.passengers),
                        len(self.station_node.station.passengers)))

    def can_enter(self, station):
        """ Returns a boolean expressing if a passenger can enter the train
            at the given station. This is only true if the train is at the
            station and there is enough capacity left on the train.
        """
        return (self.state == self.AT_STATION and
                self.station_node.station == station and
                len(self.passengers) < self.capacity)

    def can_exit(self):
        """ Return a boolean expressing if a passenger can exit at the
            current station. This is only true if the train is at the
            station.
            This method does not change any value or state.
        """
        return self.state == self.AT_STATION

    def to_dict(self):
        """ Converts the main attributes to a key-value dict

            Returns the following key-value pairs:
            - id (int)             identifyer of the train
            - state (int)          0 = at station; 1 = left station
            - station (int)        id of the station the train is at/just left
            - capacity (int)       capacity of the train (# passengers)
            - wagons (int)         number of wagons (capacity / wagon cap.)
            - num_passengers (int) number of passengers on this station
            - passengers (list)    list of passenger objects;
                                   see to_dict() of the Passenger class)
        """
        return {
            'id': self.idx,
            'state': self.state,
            'direction': self.DIRECTION[self.direction],
            'station': self.station_node.station.idx,
            'capacity': self.capacity,
            'wagons': self.capacity // self.WAGON_CAPACITY,
            'num_passengers': len(self.passengers),
            'passengers': [p.to_dict() for p in self.passengers]}
