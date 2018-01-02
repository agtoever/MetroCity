#!/usr/bin/env python2
"""
MetroCity - a simulation based on the Mini Metro game.

This library contains the Station class, which represents a metro station
where passengers come from and go to.
"""


import numpy
import Passenger


class Station:
    """ Represents a metro station; contains passengers.

        Attributes:
            city       the city where the station is located in
            idx        an unique index number to identify the station
            position   station's position as a (x, y) numpy array
            avgrate    the average rate at which new passengers are spawned
            passengers list of Passenger objects - passengers at that station
    """

    def __init__(self, city, position=(0, 0), avgrate=.1):
        """ Initialize a new station.
            The station has a position (x,y) and an average Poisson rate
            for spawning new passengers.
        """
        self.city = city
        self.idx = len(self.city.stations)
        self.position = numpy.array(position)
        self.avgrate = avgrate
        self.passengers = []

    def spawn_passengers(self, trace=False):
        """ Spawns new passengers; averages to avgrate passengers per unit of
            time. Gives the passenger a random station as distination.
        """
        for _ in range(numpy.random.poisson(self.avgrate)):
            dest = self
            while dest == self:
                dest = numpy.random.choice(self.city.stations)
            self.passengers.append(
                Passenger.Passenger(self.city, self, dest, trace))

    def to_dict(self):
        """ Converts the main attributes to a key-value dict

            Returns the following key-value pairs:
            - id (int)             identifyer of the station
            - position_x (int)     x-position of the station
            - position_y (int)     y-position of the station
            - num_passengers (int) number of passengers on this station
            - passengers (list)    list of passenger objects;
                                   see to_dict() of the Passenger class)
        """
        return {
            'id': self.idx,
            'position_x': self.position[0],
            'position_y': self.position[1],
            'num_passengers': len(self.passengers),
            'passengers': [p.to_dict() for p in self.passengers]}
