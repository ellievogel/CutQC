import itertools
import logging
import os
from time import perf_counter
import tensorflow as tf
from cutqc.post_process_helper import ComputeGraph
from cutqc.abstract_graph_contractor import AbstractGraphContractor

logging.disable(logging.WARNING)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf

class GraphContractor(AbstractGraphContractor):
    def __init__(self):
        self.times = {}
        self.reconstructed_prob = None
        self.compute_graph = None
        self.subcircuit_entry_probs = None
        self.num_cuts = None
        self.overhead = {"additions": 0, "multiplications": 0}
        self.smart_order = []
    
    def _compute(self):
        edges = self.compute_graph.get_edges(from_node=None, to_node=None)
        partial_compute_begin = perf_counter()
        reconstructed_prob = tf.zeros_like(self._get_paulibase_probability(["I"] * len(edges), edges))
        counter = 0

        for edge_bases in itertools.product(["I", "X", "Y", "Z"], repeat=len(edges)):
            summation_term = self._get_paulibase_probability(edge_bases, edges)
            reconstructed_prob = tf.add(reconstructed_prob, summation_term)
            self.overhead["additions"] += len(summation_term)
            counter += 1
            
        self.compute_graph.remove_bases_from_edges(edges=self.compute_graph.edges)
        partial_compute_time = perf_counter() - partial_compute_begin

        scale_begin = perf_counter()
        reconstructed_prob = tf.math.scalar_mul(
            1 / 2**self.num_cuts, reconstructed_prob
        ).numpy()
        scale_time = perf_counter() - scale_begin

        self.times["compute"] = (
            partial_compute_time / counter * 4 ** len(edges) + scale_time
        )
        self.overhead["additions"] = int(
            self.overhead["additions"] / counter * 4 ** len(edges)
        )
        self.overhead["multiplications"] = int(
            self.overhead["multiplications"] / counter * 4 ** len(edges)
        )
        return reconstructed_prob
    
    def _set_smart_order(self) -> None:
        subcircuit_entry_lengths = {}
        for subcircuit_idx in self.subcircuit_entry_probs:
            first_entry_init_meas = list(self.subcircuit_entry_probs[subcircuit_idx].keys())[0]
            length = len(self.subcircuit_entry_probs[subcircuit_idx][first_entry_init_meas])
            subcircuit_entry_lengths[subcircuit_idx] = length

        self.smart_order = sorted(
            subcircuit_entry_lengths.keys(),
            key=lambda subcircuit_idx: subcircuit_entry_lengths[subcircuit_idx],
        )
    
    def _get_paulibase_probability(self, edge_bases: tuple, edges: list):
        summation_term = None
        self.compute_graph.assign_bases_to_edges(edge_bases=edge_bases, edges=edges)

        for subcircuit_idx in self.smart_order:
            subcircuit_entry_prob = self._get_subcircuit_entry_prob(subcircuit_idx)
            if summation_term is None:
                summation_term = subcircuit_entry_prob
            else:
                summation_term = tf.reshape(
                    tf.tensordot(summation_term, subcircuit_entry_prob, axes=0),
                    [-1],
                )
                self.overhead["multiplications"] += len(summation_term)

        return summation_term
