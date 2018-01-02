#!/usr/bin/env python2
"""
MetroCity - a simulation based on the Mini Metro game.

This library contains the City class, that contains most objects of the
simulation: stations, trains and lines. The City class keeps track of all
city-wide parameters, such as the size of the city, the time, maximum number
of trains, etc.
"""


import itertools
import numpy
import Station
import Line
import Train


class City:
    """ Contains all stations, lines and trains

    Attributes:
        time        simulation time; same as the number of iterations
        stations    stations in the city; list of Station objects
        lines       lines in the city; list of Line objects
        trains      train in the city; list of Train objects
        max_trains  the maximum number of trains that are allowed
        edgelength  the size of the imaginary square the city lives in
        distmap     matrix of distances between two stations a and b
        navmap      matric of navigation points from station a to b
        arrived_passengers list of travel times of arrived passengers
    """

    def __init__(self):
        """ Initialize a new city """
        self.time = 0
        self.stations = []
        self.lines = []
        self.trains = []
        self.max_trains = 3
        self.max_lines = 3
        self.free_wagons = 0
        self.edgelength = 10
        self.distmap = None
        self.navmap = None
        self.arrived_passengers = []

    def _random_position(self):
        """ Return a random position within the city boundaries,
            that is, inside a square with center (0, 0) and side length
            self.edgelength.
        """
        return numpy.array(numpy.random.randint(-self.edgelength//2,
                                                self.edgelength//2, 2))

    def _update_navmap(self):
        """ Update the navigation map that passengers user to travel
        around the city.
        Updates the class properties distmap and navmap.
        distmap is a matrix of shortest distances from station a to b,
        measured in station hops (the distance from a to d in a->b->c->d is 3)
        navmap is a matrix of (line, direction) tuples that give the
        shortest route from station a to station b.
        For example: distmap[a][b] gives the shortest distance from a to b.
        """
        # Use the Floyd-Warshall algorithm (on distmap)
        # Filling navigation map along with distance map

        # Initialize distmap
        n = len(self.stations)
        self.distmap = numpy.ones((n, n), dtype=int) * numpy.inf
        numpy.fill_diagonal(self.distmap, 0)

        # Initialize navmap
        self.navmap = numpy.empty((n, n), dtype=object)
        for m in numpy.nditer(self.navmap, ['refs_ok'], ['readwrite']):
            m[...] = set()

        # Fill in all connections with distance = 1, iterating over the lines
        for line in self.lines:
            # On circular lines, check if trains run unidirectional
            if line.is_circular():
                directions = set([t.direction for t in line.trains()])
            else:
                directions = {-1, 1}

            # Iterate over all consecutive stations and take into account
            # the possible directions a train can have on that line.
            station_idxs = [node.station.idx for node in line.station_nodes]
            for i in range(len(station_idxs)-1):
                if 1 in directions and self.stations[i] != self.stations[i+1]:
                    self.distmap[i, i+1] = 1
                    self.navmap[i, i+1].add((line.color, 1))
                if -1 in directions and self.stations[i+1] != self.stations[i]:
                    self.distmap[i+1, i] = 1
                    self.navmap[i+1, i].add((line.color, -1))

        # Loop over all source-midpoint-destination combinations (i, k, j),
        # updating the distance map and the navigation map.
        for k, i, j in itertools.product(range(n), repeat=3):
            # if i -> k -> j is equally long, add route to navmap
            if self.distmap[i, j] == self.distmap[i, k] + self.distmap[k, j]:
                self.navmap[i][j] = self.navmap[i][j].union(self.navmap[i][k])
            # if i -> k -> j is shorter, replace i -> j with new dist and nav
            if self.distmap[i, j] > self.distmap[i, k] + self.distmap[k, j]:
                self.distmap[i][j] = self.distmap[i][k] + self.distmap[k][j]
                self.navmap[i][j] = set(self.navmap[i][k])

    def add_station(self):
        """ Adds a new stations to the city  on a random location.
            The location is a 2D coordinate that lies within the square
            centered at (0,0) with side length self.edgelength.
            Returns the added station.
        """
        # Find an unoccupied position within the specified area
        stations_pos = [tuple(s.position) for s in self.stations]
        pos = self._random_position()
        while tuple(pos) in stations_pos:
            pos = self._random_position()

        # Append station, update the distmap and return the station object
        self.stations.append(Station.Station(self, pos))
        self._update_navmap()
        return self.stations[-1]

    def add_line(self, stations_list=[]):
        """ Adds a line to the city and returns the new line object.
            Returns None if the line could not be created.
            Note: does not add trains to the line.
        """
        if len(self.lines) < self.max_lines:
            self.lines.append(Line.Line(self))
            self.lines[-1].stations = stations_list
            return self.lines[-1]
        return None

    def clear_line(self, line):
        """ Removes all stations and trains from a line.
            All passengers on the trains are left at the station that was
            last visited or is currently visited by the train.
            Returns False is line is not a valid line object.
            Returns True on success.
            Note: does *not* delete the line.
        """
        if line not in self.lines:
            return False
        for node in self.line.station_nodes:
            del node
        for train in line.trains():
            self.remove_train(train, update_navmap=False)
        self._update_navmap()
        return True

    def add_train(self, line=None, station=None, direction=1, trace=False):
        """ Adds a train to the city and updates navmap and distmap if needed.
            Returns the train object on success; returns None of the train
            could not be added.
        """
        if len(self.trains) < self.max_trains:
            newtrain = Train.Train(self, trace)
            self.trains.append(newtrain)
            if line is not None:
                self.trains[-1].set_line(line, station, direction)
                if line.is_circular() or len(line.trains()) == 1:
                    self._update_navmap()
            return newtrain
        return None

    def move_train(self, train, line=None, station=None, direction=1):
        """ Moves a train (and its wagons and its passengers) to a
            specified line, station and direction.
            Returns False if train is not a valid train object.
            Returns True on success.
        """
        if train not in self.city.trains:
            return False
        train.set_line(line, station, direction)
        if line.is_circular() or len(line.trains()) == 1:
            self._update_navmap()
        return True

    def remove_train(self, train, update_navmap=True):
        """ Removes a train from its (current) line.
            All passengers on the trains are left at the station that was
            last visited or is currently visited by the train.
            Returns False is train is not a valid train object.
            Returns True on success.
        """
        if train not in self.trains:
            return False

        # put all passengers on the last visited station
        train.station.passengers.extend(train.passengers)

        # set relevant train attributes
        line = train.line
        train.line = None
        train.station = None

        # update train history if traced
        if train.trace:
            train.history.append(
                "{}: Train removed from line.".format(self.time))

        if update_navmap and (line.is_circular() or len(line.trains()) == 0):
            self._update_navmap()

        return True

    def add_wagon(self, train):
        """ Adds a wagon to a train.
            Returns False is this was not possible or if train is not a valid
            Train object. Returns True on success.
        """
        if self.city.free_wagons > 0 and train.add_wagon():
            self.city.free_wagons -= 1
            return True
        return False

    def remove_wagon(self, train):
        """ Removes a wagon from a train.
            If there are more passengers than capacity after removing the
            wagon, the last entered passengers are dropped at the current
            station or the last station the train stoped at.
            Returns a boolean that indicates if this has succeeded.
        """
        if train.remove_wagon():
            self.city.free_wagons += 1
            return True
        return False

    def add_station_to_line(self, line, station, index=-1):
        """ Adds a station to the line at a given index (zero-based).
            The default index of -1 puts a station at the end of the list.
            Returns False if line or station are invalid objects.
            Return True otherwise.
        """
        if line not in self.lines or station not in self.stations:
            return False
        return line.add_station(station, index)

    def remove_station_from_line(self, line, station):
        """ Removes a station from the line.
            Returns False if line or station are invalid objects.
            Return True otherwise.
        """
        if line not in self.lines:
            return False
        return line.remove_station(station)

    def move_station_in_line(self, line, station, index, update_navmap=True):
        """ Moves a station to the line to a given index.
            Returns False if line or station are invalid objects.
            Return True otherwise.
        """
        # todo: handle partial success: remove succeeds, but add fails
        return (self.remove_station_from_line(line, station, False) and
                self.add_station_to_line(line, station, index, update_navmap))

    def all_passengers(self):
        """ Returns a list of all passengers. First the passengers on trains
            are returned, than the passengers on stations. Withing that
            groups, passengers are sorted to their starting time, oldest first.
        """
        passengers = (sorted([p for t in self.trains for p in t.passengers],
                             key=lambda p: p.starttime) +
                      sorted([p for s in self.stations for p in s.passengers],
                             key=lambda p: p.starttime))
        return passengers

    def station_ids(self):
        """ Return a dict of all station id's, pointing to the station objects
        """
        # todo: consider using dicts in the class instead of lists
        return {station.idx: station for station in self.stations}

    def line_colors(self):
        """ Return a dict of all line colors, pointing to the line objects
        """
        # todo: consider using dicts in the class instead of lists
        return {line.color: line for line in self.lines}

    def train_ids(self):
        """ Return a dict of all train id's, pointing to the train objects
        """
        # todo: consider using dicts in the class instead of lists
        return {train.idx: train for train in self.trains}

    def passenger_arrived(self, passenger):
        """ Registers the traveled time of an arrived passenger """
        self.arrived_passengers.append(self.time - passenger.starttime)
        if passenger.trace:
            msg = "{}: passenger arrived after {}.".format(
                self.time, self.time - passenger.starttime)
            passenger.history.append(msg)
