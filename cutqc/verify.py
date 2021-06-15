import pickle
import argparse
import glob
import numpy as np
from qiskit.quantum_info import Statevector

from qiskit_helper_functions.non_ibmq_functions import evaluate_circ
from qiskit_helper_functions.metrics import nearest_probability_distribution

def get_heavy_strings(model_circuit):
    zero = Statevector.from_label('0' * 8)
    sv = zero.evolve(model_circuit)
    probs_ideal = sv.probabilities_dict()

    prob_median = float(np.real(np.median(list(probs_ideal.values()))))
    heavy_strings = list(
        filter(
            lambda x: probs_ideal[x] > prob_median,
            list(probs_ideal.keys()),
        )
    )
    return heavy_strings

def verify(full_circuit,unordered,complete_path_map,subcircuits,smart_order):
    ground_truth = evaluate_circ(circuit=full_circuit,backend='statevector_simulator')
    unordered, _ = nearest_probability_distribution(quasiprobability=unordered)
    subcircuit_out_qubits = {subcircuit_idx:[] for subcircuit_idx in smart_order}
    for input_qubit in complete_path_map:
        path = complete_path_map[input_qubit]
        output_qubit = path[-1]
        subcircuit_out_qubits[output_qubit['subcircuit_idx']].append((output_qubit['subcircuit_qubit'],full_circuit.qubits.index(input_qubit)))
    for subcircuit_idx in subcircuit_out_qubits:
        subcircuit_out_qubits[subcircuit_idx] = sorted(subcircuit_out_qubits[subcircuit_idx],
        key=lambda x:subcircuits[subcircuit_idx].qubits.index(x[0]),reverse=True)
        subcircuit_out_qubits[subcircuit_idx] = [x[1] for x in subcircuit_out_qubits[subcircuit_idx]]
    # print('subcircuit_out_qubits:',subcircuit_out_qubits)
    unordered_qubit = []
    for subcircuit_idx in smart_order:
        unordered_qubit += subcircuit_out_qubits[subcircuit_idx]
    # print('CutQC out qubits:',unordered_qubit)
    squared_error = 0
    absolute_percentage_error = 0
    reconstructed_output = []
    for unordered_state, unordered_p in enumerate(unordered):
        bin_unordered_state = bin(unordered_state)[2:].zfill(full_circuit.num_qubits)
        _, ordered_bin_state = zip(*sorted(zip(unordered_qubit, bin_unordered_state),reverse=True))
        ordered_bin_state = ''.join([str(x) for x in ordered_bin_state])
        ordered_state = int(ordered_bin_state,2)
        ground_p = ground_truth[ordered_state]
        squared_error += np.power(ground_p-unordered_p,2)
        absolute_percentage_error += abs((ground_p-unordered_p)/ground_p)*100
        reconstructed_output.append(unordered_p)
    reconstructed_output = np.array(reconstructed_output)

    mse = squared_error/len(unordered)
    
    mape = absolute_percentage_error/len(unordered)
    
    heavy_strings = get_heavy_strings(full_circuit)
    hop = 0
    for heavy_string in heavy_strings:
        heavy_state = int(heavy_string,2)
        hop += reconstructed_output[heavy_state]
    
    metrics = {'Mean Squared Error':mse,
    'Mean Absolute Percentage Error':mape,
    'HOP':hop}
    return reconstructed_output, metrics