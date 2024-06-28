# example.py

import logging
import math
import os

logging.disable(logging.WARNING)                # DEBUG and INFO messages will not be displayed
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "1"
# Comment this line if using GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"       # CutQC should not utilize a GPU

# Uncomment this line for debugging purposes
# import pdb

from cutqc.main import CutQC  # Use this for exact computation

# from cutqc_runtime.main import CutQC  # Use this just to benchmark the runtime
from helper_functions.benchmarks import generate_circ

if __name__ == "__main__":
    # Uncomment to begin stepping through code
    # pdb.set_trace()

    # Set circuit requirements
    circuit_type = "supremacy"
    circuit_size = 16
    circuit_depth = 1

    # Generate circuit given a number of qubits, a depth, a circuit type
    circuit = generate_circ(
        num_qubits=circuit_size,
        depth=circuit_depth,
        circuit_type=circuit_type,
        reg_name="q",
        connected_only=True,
        seed=None,
    )

    # Generate an instance of the CutQC class from the circuit
    cutqc = CutQC(
        name="%s_%d" % (circuit_type, circuit_size),
        circuit=circuit,
        
        # Set constraints for the subcircuits
        cutter_constraints={
            "max_subcircuit_width": math.ceil(circuit.num_qubits / 4 * 3),
            "max_subcircuit_cuts": 10,
            "subcircuit_size_imbalance": 2,
            "max_cuts": 10,
            "num_subcircuits": [2, 3],
        },
        verbose=True,
    )

    # Cut circuit into subcircuits given constraints if possible
    """
    Required:
        max_subcircuit_width: max number of qubits in each subcircuit
    Optional:
        max_cuts: max total number of cuts allowed
        num_subcircuits: list of subcircuits to try, CutQC returns the best solution found among the trials
        max_subcircuit_cuts: max number of cuts for a subcircuit
        max_subcircuit_size: max number of gates in a subcircuit
        quantum_cost_weight: quantum_cost_weight : MIP overall cost objective is given by
        quantum_cost_weight * num_subcircuit_instances + (1-quantum_cost_weight) * classical_postprocessing_cost
        subcircuit_vertices: supply manually (overrides all other arguments)
    """
    cutqc.cut()
    if not cutqc.has_solution:
        raise Exception("The input circuit and constraints have no viable cuts")

    # eval_mode: qasm = simulate shots or sv = statevector simulation
    cutqc.evaluate(eval_mode="sv", num_shots_fn=None)
    cutqc.build(mem_limit=32, recursion_depth=1)
    print("Cut: %d recursions." % (cutqc.num_recursions))
    print(cutqc.approximation_bins)
    cutqc.clean_data()
