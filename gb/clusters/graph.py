#   Copyright (c) 2016 CNRS - Centre national de la recherche scientifique.
#   All rights reserved.
#
#   Written by Telmo Menezes <telmo@telmomenezes.com>
#
#   This file is part of GraphBrain.
#
#   GraphBrain is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   GraphBrain is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with GraphBrain.  If not, see <http://www.gnu.org/licenses/>.


import itertools
import igraph
import gb.tools.json as json_tools
import gb.hypergraph.symbol as sym
import gb.hypergraph.edge as ed
import gb.nlp.parser as par
from gb.clusters.meronomy import Meronomy


MAX_PROB = -12


class Graph(object):
    def __init__(self, parser, claims, black_list=None):
        self.parser = parser
        if black_list:
            self.black_list = black_list
        else:
            self.black_list = []
        self.meronomy = None
        self.graph = None
        self.edges = {}
        self.vertices = set()
        self.init_graph(claims)

    def init_graph(self, claims):
        # build meronomy
        self.meronomy = Meronomy(par, claims)
        self.meronomy.normalize_graph()
        self.meronomy.generate_synonyms()

        for claim in claims:
            self.add_claim(claim)
        self.graph = igraph.Graph()
        self.graph.add_vertices(list(self.vertices))
        self.vertices = None
        self.graph.add_edges(self.edges.keys())
        self.graph.es['weight'] = list(self.edges.values())
        self.edges = None

    def add_link(self, orig, targ):
        if orig != targ:
            if (orig, targ) not in self.edges:
                self.edges[(orig, targ)] = 0.
            self.edges[(orig, targ)] += 1.

    def edge2str(self, edge):
        s = ed.edge2str(edge, namespaces=False)
        if sym.is_edge(edge):
            return s

        if s[0] == '+':
            s = s[1:]

        if len(s) == 0:
            return None

        if not s[0].isalnum():
            return None

        word = self.parser.make_word(s)
        if word.prob < MAX_PROB:
            return s

        return None

    def edge2syn(self, edge):
        atom = self.edge2str(edge)
        if atom:
            if atom in self.black_list:
                return None
            syn_id = self.meronomy.syn_id(atom)
            if syn_id:
                return str(syn_id)
        return None

    def add_claim(self, edge):
        orig = self.edge2syn(edge)
        if not orig:
            return
        self.vertices.add(orig)
        if sym.is_edge(edge):
            elements = []
            # links from part to whole
            for element in edge:
                targ = self.edge2syn(element)
                if targ:
                    elements.append(targ)
                    self.vertices.add(targ)
                    self.add_link(orig, targ)
                self.add_claim(element)

            # links between peers
            combs = itertools.combinations(elements, 2)
            for comb in combs:
                self.add_link(*comb)

    def contains_synonym(self, full_edge, syn_id):
        for atom in self.meronomy.synonym_sets[syn_id]:
            edge = ed.str2edge(atom)
            if ed.contains(full_edge, edge, deep=True):
                return True
        return False

    def synset_pr_pairs(self):
        pr = g.graph.pagerank(weights='weight')
        pairs = [(g.graph.vs[i]['name'], pr[i]) for i in range(len(pr))]
        return sorted(pairs, key=lambda x: x[1], reverse=True)


def contains_one_of(edge, concepts):
    for concept in concepts:
        if ed.contains(edge, concept):
            return True
    return False


def contains_all_concept_sets(edge, concept_sets):
    for concept_set in concept_sets:
        if concept_set:
            if not contains_one_of(edge, concept_set):
                return False
    return True


if __name__ == '__main__':
    print('creating parser...')
    par = par.Parser()
    print('parser created.')

    # read data
    # edge_data = json_tools.read('edges_similar_concepts.json')
    edge_data = json_tools.read('all.json')

    # build full edges list
    full_edges = []
    for it in edge_data:
        full_edges.append(ed.without_namespaces(ed.str2edge(it['edge'])))

    # synonym_set
    synset1 = []
    synset2 = []
    synset3 = []

    synset1 = ['trump', 'donald', '(+ donald trump)']
    # synset2 = ['ryan', '(+ paul ryan)', 'paul']
    synset2 = ['vladimir', '(+ vladimir putin)', 'putin']
    concepts1 = [ed.str2edge(x) for x in synset1]
    concepts2 = [ed.str2edge(x) for x in synset2]
    concepts3 = [ed.str2edge(x) for x in synset3]

    concept_sets = [concepts1, concepts2, concepts3]

    # filter edges
    print('before filter: %s' % len(full_edges))
    full_edges = [edge for edge in full_edges if contains_all_concept_sets(edge, concept_sets)]
    print('after filter: %s' % len(full_edges))

    # build graph
    g = Graph(par, full_edges, black_list=synset1+synset2)

    pr_pairs = g.synset_pr_pairs()

    remaining_edges = full_edges[:]
    covered = set()
    for pr_pair in pr_pairs[:50]:
        syn_id = int(pr_pair[0])
        pr = pr_pair[1]
        count = 0
        new_remaining_edges = []
        for full_edge in remaining_edges:
            if g.contains_synonym(full_edge, syn_id):
                count += 1
                covered.add(ed.edge2str(full_edge, namespaces=False))
            else:
                new_remaining_edges.append(full_edge)
        remaining_edges = new_remaining_edges
        if count > 0:
            print('%s [%s]{%s} %.2f%% %s' % (g.meronomy.synonym_label(syn_id), count, len(covered),
                                             (float(len(covered)) / float(len(full_edges))) * 100., pr))
