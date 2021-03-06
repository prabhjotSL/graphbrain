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


import logging
import gb.hypergraph.hypergraph as hyperg
import gb.hypergraph.edge as ed
from gb.nlp.parser import Parser
from gb.nlp.sentence import Sentence
from gb.sense.disambiguation import Disambiguation
from gb.reader.stages.alpha_forest import AlphaForest
from gb.reader.stages.beta import BetaStage
from gb.reader.stages.beta_simple import BetaStageSimple
from gb.reader.stages.beta_naive import BetaStageNaive
from gb.reader.stages.gamma import GammaStage
from gb.reader.stages.delta import DeltaStage
from gb.reader.stages.epsilon import EpsilonStage


class Extractor(object):
    def __init__(self, hg, stages=('alpha-forest', 'beta-naive', 'gamma', 'delta', 'epsilon'), show_namespaces=False):
        self.hg = hg
        self.stages = stages
        self.parser = None
        self.disamb = None
        self.debug = False
        self.outputs = []
        self.aux_text = ''
        self.show_namespaces = show_namespaces

    def create_stage(self, name, output):
        if name == 'alpha-forest':
            return AlphaForest()
        elif name == 'beta':
            return BetaStage(self.hg, self.parser, self.disamb, output, self.aux_text)
        elif name == 'beta-simple':
            return BetaStageSimple(output)
        elif name == 'beta-naive':
            return BetaStageNaive(output)
        elif name == 'gamma':
            return GammaStage(output)
        elif name == 'delta':
            return DeltaStage(output)
        elif name == 'epsilon':
            return EpsilonStage(output)
        else:
            raise RuntimeError('unknnown stage name: %s' % name)

    def debug_msg(self, msg):
        logging.info(msg)
        if self.debug:
            print(msg)

    def read_text(self, text, aux_text=None, reset_context=True):
        if self.parser is None:
            self.debug_msg('creating parser...')
            self.parser = Parser()
            self.disamb = Disambiguation(self.hg, self.parser)
        nlp_parses = self.parser.parse_text(text)
        if reset_context:
            self.aux_text = text
            if aux_text:
                self.aux_text = '%s\n%s' % (text, aux_text)

        parses = [(p[0], self.read_sentence(Sentence(p[1]))) for p in nlp_parses]

        for p in parses:
            self.debug_msg('== extra ==')
            for edg in p[1].edges:
                self.debug_msg(ed.edge2str(edg))

        return parses

    def read_sentence(self, sentence):
        self.debug_msg('parsing sentence: %s' % sentence)
        if self.debug:
            sentence.print_tree()

        self.outputs = []

        last_stage_output = None
        first = True
        for name in self.stages:
            stage = self.create_stage(name, last_stage_output)
            self.debug_msg('executing %s stage...' % name)
            if first:
                last_stage_output = stage.process_sentence(sentence)
                first = False
            else:
                last_stage_output = stage.process()
            output = last_stage_output.tree.to_hyperedge_str(with_namespaces=self.show_namespaces)
            self.outputs.append(output)
            self.debug_msg(output)

        last_stage_output.main_edge = last_stage_output.tree.to_hyperedge()
        return last_stage_output


if __name__ == '__main__':
    # test_text = "Due to its location in the European Plain, Berlin is influenced by a temperate seasonal climate."
    # test_text = "Lots of cars require lots of paved roadways and parking lots."
    # test_text = "Critics have pointed out the dangers of group forming among like-minded in Internet. "
    # test_text = "Recently online platforms such as Facebook and Google have been criticized."
    # test_text = "Koikuchi shoyu, best known as soy sauce, is the mother of all sauces in Japan."
    test_text = "Satellites from NASA and other agencies have been tracking sea ice changes since 1979."

    print(test_text)

    hgraph = hyperg.HyperGraph({'backend': 'leveldb',
                                'hg': 'wordnet_dbpedia.hg'})
    extractor = Extractor(hgraph)
    extractor.debug = True
    results = extractor.read_text(test_text)
    for result in results:
        print('result: %s' % str(result[1].main_edge))
        for edge in result[1].edges:
            print('extra edge: %s' % str(edge))
