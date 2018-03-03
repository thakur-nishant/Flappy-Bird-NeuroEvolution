import random

import numpy as np

from NEAT.ConnectionGene import ConnectionGene
from NEAT.InnovationNumberGenerator import InnovationNumberGenerator
from NEAT.NodeGene import Type, NodeGene

"""
Based on the paper: Evolving Neural Networks through Augmenting Topologies
"""


class Genome:
    def __init__(self, connection_genes, fitness=0):
        self.connection_genes = connection_genes  # Dictionary of (innovation_number: ConnectionGene)
        self.input_nodes = {1: NodeGene(1, Type.INPUT), 2: NodeGene(2, Type.INPUT), 3: NodeGene(3, Type.INPUT)}
        self.output_nodes = {4: NodeGene(4, Type.OUTPUT)}
        self.hidden_nodes = self.generate_nodes()  # List of Tuple(id)
        self.nodes = {**self.input_nodes, **self.hidden_nodes, **self.output_nodes}
        self.innovation_number_generator = InnovationNumberGenerator(self.get_last_innovation_number())
        self.fitness = fitness

    def total_nodes(self):
        """
        Return sum of input nodes, hidden nodes and output nodes
        :return: The total count of all nodes in this genome
        """
        return len(self.input_nodes) + len(self.hidden_nodes) + len(self.output_nodes)

    def get_last_innovation_number(self):
        """
        Gets the last used innovation number for this genome
        :return: Innovation number which was last used
        """
        return sorted(self.connection_genes.keys())[-1]

    def generate_nodes(self):
        """
        Generates node objects using the connection genes
        :return: Dictionary of nodes keyed by node id
        """
        nodes = dict()
        for connection in self.connection_genes:
            connection = self.connection_genes[connection]
            in_node_exists = False
            if connection.in_node in self.input_nodes or connection.in_node in self.output_nodes:
                in_node_exists = True

            out_node_exists = False
            if connection.out_node in self.input_nodes or connection.out_node in self.output_nodes:
                out_node_exists = True

            if not in_node_exists:
                node = NodeGene(connection.in_node, Type.HIDDEN)
                if node.id not in nodes:
                    nodes[node.id] = node
            if not out_node_exists:
                node = NodeGene(connection.out_node, Type.HIDDEN)
                if node.id not in nodes:
                    nodes[node.id] = node
        return nodes

    def add_connection_mutation(self):
        """
        Modifies the existing connection genes by adding a new connection between two unconnected nodes
        or if connection exists, does nothing
        """
        node_1 = self.nodes[random.choice(list(self.nodes.keys()))]
        node_2 = self.nodes[random.choice(list(self.nodes.keys()))]
        while node_1 == node_2:
            node_2 = self.nodes[random.choice(list(self.nodes.keys()))]

        reversed = False
        if node_1.type == Type.OUTPUT and (node_2.type == Type.HIDDEN or node_2.type == Type.INPUT):
            reversed = True

        if node_1.type == Type.HIDDEN and node_2.type == Type.INPUT:
            reversed = True

        connection_exists = False
        for connection_gene in self.connection_genes:
            connection_gene = self.connection_genes[connection_gene]
            if connection_gene.in_node == node_1.id and connection_gene.out_node == node_2.id:
                connection_exists = True
                break
            if connection_gene.in_node == node_2.id and connection_gene.out_node == node_1.id:
                connection_exists = True
                break

        if connection_exists:
            return

        new_connection = ConnectionGene(in_node=node_2.id if reversed else node_1.id,
                                        out_node=node_1.id if reversed else node_2.id,
                                        weight=np.random.random(),
                                        enabled=True,
                                        innovation_number=self.innovation_number_generator.next_int()
                                        )
        self.connection_genes[new_connection.innovation_number] = new_connection

    def add_node_mutation(self):
        """
        Adds a new node between a existing connection as shown below
        o =========== 0    Old connection
        o ==== o ==== o    New connections
        """
        old_connection = self.connection_genes[random.choice(list(self.connection_genes.keys()))]

        in_node = old_connection.in_node
        out_node = old_connection.out_node

        new_node = NodeGene(self.total_nodes() + 1, Type.HIDDEN)
        old_connection.enabled = False

        new_connection_1 = ConnectionGene(in_node=in_node,
                                          out_node=new_node.id,
                                          weight=1.0,
                                          enabled=True,
                                          innovation_number=self.innovation_number_generator.next_int())

        new_connection_2 = ConnectionGene(in_node=new_node.id,
                                          out_node=out_node,
                                          weight=old_connection.weight,
                                          enabled=True,
                                          innovation_number=self.innovation_number_generator.next_int())

        self.nodes[new_node.id] = new_node
        self.connection_genes[new_connection_1.innovation_number] = new_connection_1
        self.connection_genes[new_connection_2.innovation_number] = new_connection_2

    @staticmethod
    def crossover(parent_1_genome, parent_2_genome):
        """
        Abstract for crossover between two genomes
        :param parent_1_genome: The genome for 1st parent
        :param parent_2_genome: The genome for 2nd parent
        :return: Child genome with mutation applied
        """
        child_connections = Genome.get_child_connections(parent_1_genome, parent_2_genome)
        child_genome = Genome(child_connections)
        if np.random.random() < 0.5:
            child_genome.add_node_mutation()
        if np.random.random() < 0.5:
            child_genome.add_connection_mutation()
        return child_genome

    @staticmethod
    def get_child_connections(parent_1_genome, parent_2_genome):
        """
        Performs actual crossover between the two genomes
        :param parent_1_genome: The genome for 1st parent
        :param parent_2_genome: The genome for 2nd parent
        :return: Child genome connections dictionary
        """
        child_connections = dict()

        if parent_1_genome.fitness > parent_2_genome.fitness:
            parent_1_genome, parent_2_genome = parent_1_genome, parent_2_genome
        elif parent_1_genome.fitness < parent_2_genome.fitness:
            parent_1_genome, parent_2_genome = parent_2_genome, parent_1_genome
        else:
            parent_1_genome, parent_2_genome = parent_1_genome, parent_2_genome

        parent_1_connections = parent_1_genome.connection_genes
        parent_2_connections = parent_2_genome.connection_genes

        if parent_1_genome.fitness != parent_2_genome.fitness:
            for k, v in parent_1_connections.items():
                if parent_2_connections.get(k) is None:
                    child_connections[k] = parent_1_connections[k]
                else:
                    child_connections[k] = v if np.random.random() < 0.5 else parent_2_connections[k]
        else:
            for k, v in parent_1_connections.items():
                if parent_2_connections.get(k) is None:
                    child_connections[k] = parent_1_connections[k]
            for k, v in parent_2_connections.items():
                if parent_1_connections.get(k) is None:
                    child_connections[k] = parent_2_connections[k]
            for k, v in parent_1_connections.items():
                if parent_1_connections.get(k) is not None and parent_2_connections.get(k) is not None:
                    child_connections[k] = v if np.random.random() < 0.5 else parent_2_connections[k]
        return child_connections

    @staticmethod
    def get_matching_connections(parent_1_genome, parent_2_genome):
        """
        Finds the connections between the two genomes which have the same innovation number
        Refer Figure 4 in the paper
        :param parent_1_genome: The genome for 1st parent
        :param parent_2_genome: The genome for 2nd parent
        :return: Dictionary of all the matching connections
        """
        matching_connections = dict()
        parent_1_connections = parent_1_genome.connection_genes
        parent_2_connections = parent_2_genome.connection_genes
        for k, v in parent_1_connections.items():
            if k in parent_2_connections:
                matching_connections[k] = v if np.random.random() < 0.5 else parent_2_connections[k]
        return matching_connections

    @staticmethod
    def get_disjoint_connections(parent_1_genome, parent_2_genome):
        """
        Finds the connections between the two genomes are unique in both genomes
        Refer Figure 4 in the paper
        :param parent_1_genome: The genome for 1st parent
        :param parent_2_genome: The genome for 2nd parent
        :return: Dictionary of all the disjoint connections
        """
        disjoint_connections = dict()

        #   Make parent 1 the longest of both
        if len(parent_1_genome.connection_genes) > len(parent_2_genome.connection_genes):
            parent_1_genome, parent_2_genome = parent_1_genome, parent_2_genome
        else:
            parent_1_genome, parent_2_genome = parent_2_genome, parent_1_genome

        parent_1_connections = parent_1_genome.connection_genes
        parent_2_connections = parent_2_genome.connection_genes

        for k, v in parent_1_connections.items():
            if parent_2_connections.get(k) is not None:
                continue
            else:
                if k < parent_2_genome.get_last_innovation_number():
                    disjoint_connections[k] = v
        for k, v in parent_2_connections.items():
            if parent_1_connections.get(k) is not None:
                continue
            else:
                disjoint_connections[k] = v
        return disjoint_connections

    @staticmethod
    def get_excess_connections(parent_1_genome, parent_2_genome):
        """
        Finds the connections between the two genomes which are out of bounds in either of the genomes
        Refer Figure 4 in the paper
        :param parent_1_genome: The genome for 1st parent
        :param parent_2_genome: The genome for 2nd parent
        :return: Dictionary of all the excess connections
        """
        excess_connections = dict()

        #   Make parent 1 the longest of both
        if parent_1_genome.get_last_innovation_number() > parent_2_genome.get_last_innovation_number():
            parent_1_genome, parent_2_genome = parent_1_genome, parent_2_genome
        else:
            parent_1_genome, parent_2_genome = parent_2_genome, parent_1_genome

        # Only longest genes will have excess genes
        parent_1_connections = parent_1_genome.connection_genes
        for k, v in parent_1_connections.items():
            if k > parent_2_genome.get_last_innovation_number():
                excess_connections[k] = v

        return excess_connections

    def print_genome(self):
        """
        Prints the genotype of the genome
        """
        return_string = ""
        return_string += "----------------------"
        print("----------------------")

        for k, v in self.nodes.items():
            return_string += v.__repr__()
            print(v)
        print()
        for k, v in self.connection_genes.items():
            return_string += v.__repr__()
            print(v)
        return_string += "----------------------"
        print("----------------------\n")
        return return_string

    @staticmethod
    def get_compatibility_distance(parent_1_genome, parent_2_genome):
        """
        Gets the compatibility distance between the two genomes which is a measure of how different the two
        genomes are.

        Formula: d = ((c1 * E) + (c2 * D)) / N + (c3 * W)
        c1, c2, c3 are constants with values 1.0, 1.0, 0.4 (Values from paper. Section 4.1)
        E = Number of matching genes
        D = Number of disjoint genes
        W = Average weight difference of the matching genes
        Refer section 3.3 of paper

        :param parent_1_genome: The genome of 1st parent
        :param parent_2_genome: The genome of 2nd parent
        :return: Compatibility distance
        """

        E = len(Genome.get_excess_connections(parent_1_genome, parent_2_genome))
        D = len(Genome.get_disjoint_connections(parent_1_genome, parent_2_genome))
        W = Genome.get_average_weight_difference_of_matching_genes(parent_1_genome, parent_2_genome)
        N = 1 if len(parent_1_genome.connection_genes) < 20 and len(parent_2_genome.connection_genes) < 20 else len(
            parent_1_genome.connection_genes) if len(parent_1_genome.connection_genes) > len(
            parent_2_genome.connection_genes) else len(parent_1_genome.connection_genes)

        c1 = 1.0
        c2 = 1.0
        c3 = 0.4
        d = ((c1 * E) + (c2 * D)) / N + (c3 * W)
        return d

    @staticmethod
    def get_average_weight_difference_of_matching_genes(parent_1_genome, parent_2_genome):
        """
        Gets the average weight distance between the two genomes
        :param parent_1_genome: The genome of 1st parent
        :param parent_2_genome: The genome of 2nd parent
        :return: Average weight distance
        """
        matching_connections = 0
        weight_difference = 0
        parent_1_connections = parent_1_genome.connection_genes
        parent_2_connections = parent_2_genome.connection_genes
        for k, v in parent_1_connections.items():
            if k in parent_2_connections:
                matching_connections += 1
                weight_difference += abs(v.weight - parent_2_connections[k].weight)
        return float(weight_difference / matching_connections)

    def __repr__(self):
        return self.print_genome()


# Testing starts #
cg1 = ConnectionGene(1, 4, 0.5, True, 1)
cg2 = ConnectionGene(2, 4, 0.5, False, 2)
cg3 = ConnectionGene(3, 4, 0.5, True, 3)
cg4 = ConnectionGene(2, 5, 0.5, True, 4)
cg5 = ConnectionGene(5, 4, 0.5, True, 5)
cg6 = ConnectionGene(1, 5, 0.5, True, 8)
parent_1_genes = dict()
for i in range(1, 7):
    parent_1_genes[locals()['cg{}'.format(i)].innovation_number] = locals()['cg{}'.format(i)]
parent_1_genome = Genome(parent_1_genes)

cg1 = ConnectionGene(1, 4, 0.5, True, 1)
cg2 = ConnectionGene(2, 4, 0.5, False, 2)
cg3 = ConnectionGene(3, 4, 0.5, True, 3)
cg4 = ConnectionGene(2, 5, 0.5, True, 4)
cg5 = ConnectionGene(5, 4, 0.5, False, 5)
cg6 = ConnectionGene(5, 6, 0.5, True, 6)
cg7 = ConnectionGene(6, 4, 0.5, True, 7)
cg8 = ConnectionGene(3, 5, 0.5, True, 9)
cg9 = ConnectionGene(1, 6, 0.5, True, 10)
parent_2_genes = dict()
for i in range(1, 10):
    parent_2_genes[locals()['cg{}'.format(i)].innovation_number] = locals()['cg{}'.format(i)]
parent_2_genome = Genome(parent_2_genes)

# print(Genome.crossover(parent_1_genome, parent_2_genome))
# print(Genome.get_matching_connections(parent_1_genome, parent_2_genome))
# print(Genome.get_disjoint_connections(parent_1_genome, parent_2_genome))
# print(Genome.get_excess_connections(parent_1_genome, parent_2_genome))
# print(Genome.get_compatibility_distance(parent_1_genome, parent_2_genome))

# Testing ends #