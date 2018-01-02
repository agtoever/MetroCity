#!/usr/bin/env python2
"""
MetroCity - a simulation based on the Mini Metro game.

This library contains the Line class, which represents the metro line where
trains run on.
"""


from PIL import ImageColor
from platform import node


class Line:
    """ Represents a metro line; contains stations.
        New lines automatically get a color from the following sequence:
            blue, brown, cadetblue, chocolate, cornflowerblue, crimson,
            darkblue, darkgoldenrod, darkgreen, darkkhaki, darkolivegreen,
            darkorchid, darksalmon
        That means that the first line in the simulation is *always* the
        blue line.

        Attributes:
            city           the city the line runs through
            color          the color of the line; used as a line identifier
            station_nodes list of Station_Nodes objects that represent the
                           the stations on the line (double linked list).
    """

    def __init__(self, city=None):
        self.city = city
        self.color = sorted(ImageColor.colormap)[9:35:2][len(self.city.lines)]
        self.station_nodes = []

    def is_circular(self):
        """ Return a boolean value indicating if the line is circular.
            A line is circular if the first stop is the same stop as the
            last stop on the line.
        """
        if len(self.station_nodes) <= 1:
            return False
        return (self.station_nodes[0] is not None and
                self.station_nodes[-1].next_node == self.station_nodes[0])

    def trains(self):
        """ Returns a list of trains that are assigned to this line. """
        return [t for t in self.city.trains if t.line == self]

    def add_station(self, station, position):
        """ Inserts station on the line at position. Position is an integer
            using zero based indexing. Inserting at position = 0 inserts
            the station at the beginning of the line; position = len(stations)
            inserts it at the end of the line. Alternatively, position = -1
            can be used to add a station to the end of the line.

            Returns False if station is already on the line. Also returns False
            if the position < -2 or position > len(stations). Return True in
            all other cases.
        """
        # Handle the case where station is the first station
        if len(self.station_nodes) == 0 and position <= 0:
            node = Station_Node(station)
            node.previous_node = node.next_node = None
            self.station_nodes = [node]
            return True

        # Handle the case where station is already on the line
        if station in [node.station for node in self.station_nodes]:
            return False

        # Handle illegal position values
        if position < -2 or position > len(self.station_nodes):
            return False

        # Handle adding a station to the end of the line
        if position == -1 or position == len(self.station_nodes):
            node = Station_Node(station, self.station_nodes[-1], None)
            node.previous_node.next_node = node
            self.station_nodes.append(node)
            return True

        # Handle adding a station to the beginning of the line
        if position == 0:
            node = Station_Node(station, None, self.station_nodes[0])
            node.next_node.previous_node = node
            self.station_nodes.insert(0, node)
            return True

        # Handje the regular "put it somewhere in the middle"-case
        node = Station_Node(station,
                            self.station_nodes[position-1],
                            self.station_nodes[position])
        node.next_node.previous_node = node
        node.previous_node.next_node = node
        self.station_nodes.insert(position, node)
        return True

    def remove_station(self, station):
        """ Removes a station from the line
            Returns False if station is not on the line.
            Returns True otherwise
        """
        node = self.find_node(station)
        if node is None:
            return False

        # Unhook previous and next nodes if they are there
        if node.previous_node is not None:
            node.previous_node.next_node = node.next_node
        if node.next_node is not None:
            node.next_node.previous_node = node.previous_node

        # remove the node from the list
        self.station_nodes.remove(node)
        return True

    def make_circular(self):
        self.station_nodes[0].previous_node = self.station_nodes[-1].station
        self.station_nodes[-1].next_node = self.station_nodes[0].station

    def break_circular(self):
        self.station_nodes[0].previous_node = None
        self.station_nodes[-1].next_node = None

    def find_node(self, station):
        """ Returns a Station_node that has station in it.
            If station is not on line, returns None.
        """
        for node in self.station_nodes:
            if node.station == station:
                return node
        return None

    def next_station(self, station_node=None, direction=1):
        """ Returns the next station_node and new direction, seen from the
            viewpoint of a specific station on the line and given its
            direction.
            Returns a tuple: (station_node object, new_direction)
            or (None, 0) of this does not exist for some reason.
        """
        if station_node not in self.station_nodes:
            print "Warning: next station not found."
            return (None, 0)

        elif len(self.station_nodes) == 1:
            return (station_node, direction)

        elif direction == 1:
            if station_node.next_node.next_node is None:
                return (station_node.next_node, -1)
            else:
                return (station_node.next_node, 1)

        elif direction == -1:
            if station_node.previous_node.previous_node is None:
                return (station_node.previous_node, 1)
            else:
                return (station_node.previous_node, -1)

        else:
            print "Warning: next station not found."
            return (None, 0)

    def to_dict(self):
        """ Converts the main attributes to a key-value dict

            Returns the following key-value pairs:
            - color (string)  identifyer of the line
            - stations (list) list of Station objects; see to_dict() of Station
        """
        return {
            'color': self.color,
            'stations': [s.idx for s in self.stations]}


class Station_Node:
    def __init__(self, station, previous_node=None, next_node=None):
        self.station = station
        self.previous_node = previous_node
        self.next_node = next_node
