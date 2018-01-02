#!/usr/bin/env python2
"""
MetroCity - a simulation based on the Mini Metro game.

This library contains the Passenger class, which represents the traveling
passenger, the hero of our simulation: a simple commuter struggeling to
find its way from A to B.
"""


import numpy
import Train
import Station

class Passenger:
    """ Represents a passenger

    Attributes:
        city        the city the passenger lives in
        starttime   the time the passenger was spawned at at station of origin
        origin      the station where the passenger was spawned
        destination the station where the passenger deperately tries to go
        trace       boolean indicating if the history list should be kept
        history     list of status strings (such as entering/leaving a train)
        position    where the passenger is; either a Train or Station object
    """

    def __init__(self, city=None, origin=None, destination=None, trace=False):
        """ Initialize a new passenger. """
        self.city = city
        self.starttime = self.city.time
        if origin is None:
            origin = numpy.random.choice(self.city.stations)
        self.origin = self.position = origin
        if destination is None:
            while destination != origin:
                destination = numpy.random.choice(self.city.stations)
        self.destination = destination
        self.trace = trace
        self.history = ['{}: spawned passenger at {}, traveling to {}.'.format(
            self.city.time, origin.idx, destination.idx)]

    def navigate_step_to(self, station):
        """ Returns a set of (line, direction) tuples that are the shortest
            routes to station.
            This method does not change any value or state.
        """
        if isinstance(self.position, Train.Train):
            return self.city.navmap[self.position.station_node.station.idx,
                                    station.idx]
        return self.city.navmap[self.position.idx, station.idx]

    def move(self):
        """ Makes a move towards the destination:
            - on a station: checks if he/she can enter a train to destination
            - on a train: checks if he/she must exit at the next destination
            Updates position and (un)registers at stations/trains as needed.
            Upon exit, it unregisters at stations and trains and notifies
            to the city that the destination is reached.
        """
        if self.position is None:
            print "Warning: faulty position for passenger."

        # On a train, exit if we are traveling in the wrong direction
        # Get off the train if the train does not go to destination and if
        # we can exit the train.
        if (isinstance(self.position, Train.Train) and
                (self.position.line.color, self.position.direction) not in
                self.navigate_step_to(self.destination) and
                self.position.can_exit()):
            # if not, remove the passenger from the train...
            self.position.passengers.remove(self)
            # ...add him/her to the station...
            self.position.station_node.station.passengers.append(self)
            # ...and update position.
            self.position = self.position.station_node.station
            if self.trace:
                self.history.append('{}: disembarked at station {}.'.format(
                    self.city.time, self.position.idx))

        # On a station, check if we can get on any train to destination
        if isinstance(self.position, Station.Station):
            for train in [t for t in self.city.trains if
                          t.can_enter(self.position) and
                          (t.line.color, t.direction) in
                          self.navigate_step_to(self.destination)]:

                # remove the passenger from the station...
                self.position.passengers.remove(self)

                # ...add him/her to the train...
                train.passengers.append(self)

                # ...and update position.
                self.position = train

                # leave a message in the history if trace is on
                if self.trace:
                    msg = '{}: embarked on {} line moving {}.'.format(
                        self.city.time, train.line.color,
                        train.DIRECTION[train.direction])
                    self.history.append(msg)

                # Break out of the train loop
                break

        # Check if we reached final destination
        if self.position == self.destination:
            self.city.passenger_arrived(self)
            self.position.passengers.remove(self)

    def to_dict(self):
        """ Converts the main attributes to a key-value dict

            Returns the following key-value pairs:
            - starttime (int)   time the passenger is spawned
            - origin (int)      id of the station the passenger is spawned
            - destination (int) id of the station the passenger is traveling to
            - current_position_type (string)
              'Train' or 'Station', depending on where the passenger is
            - current_position_id (int)
              id of the station or train where the passenger is
        """
        return {
            'starttime': self.starttime,
            'origin': self.origin.idx,
            'destination': self.destination.idx,
            'current_position_type': self.position.__class__.__name__,
            'current_position_id': self.position.idx
            }
