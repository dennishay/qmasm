#! /usr/bin/env python

############################################
# Output the ground state of a QMASM macro #
# By Scott Pakin <pakin@lanl.gov>          #
############################################

import qmasm
import argparse

# Parse the command line.
cl_parser = argparse.ArgumentParser(description="Compute the ground state of a QMASM macro")
cl_parser.add_argument("input", nargs="*", default=[],
                           help="file from which to read a symbolic Hamiltonian")
cl_parser.add_argument("-m", "--macro", metavar="MACRO", default="",
                       help="name of a macro whose ground state should be reported")
cl_parser.add_argument("-v", "--verbose", action="count", default=0,
                       help="increase output verbosity (can be specified repeatedly)")
cl_args = cl_parser.parse_args()
if cl_args.macro == "":
    qmasm.abend("A macro must be specified with --macro")

# Parse the original input file(s) into an internal representation.
qmasm.parse_files(cl_args.input)
if cl_args.macro not in qmasm.macros:
    qmasm.abend('Macro "%s" not found' % cl_args.macro)

def macro_to_coeffs(macro):
    "Convert a macro to h and J coefficient maps."
    h = {}
    J = {}
    syms = set()
    for m in macro:
        if m.__class__ == qmasm.Weight:
            h[m.sym] = m.weight
            syms.add(m.sym)
        elif m.__class__ == qmasm.Strength:
            J[(m.sym1, m.sym2)] = m.strength
            J[(m.sym2, m.sym1)] = m.strength
            syms.add(m.sym1)
            syms.add(m.sym2)
        else:
            qmasm.abend("Only weights and strengths are currently supported")
    return sorted(syms, key=lambda s: ("$" in s, s)), h, J

def output_ground_state(syms, h, J):
    "Exhaustively evaluate the ground states of a truth table."
    width = max([len(s) for s in syms])
    ncols = len(syms)
    table = []   # List of {spins, energy} tuples
    min_energy = 2**30
    all_energies = set()
    for row in range(2**ncols):
        # Precompute a vector of spins.
        spins = [(row>>(ncols - i - 1)&1)*2 - 1 for i in range(ncols)]

        # Compute the current row's energy
        energy = 0.0
        for i in range(ncols):
            try:
                hi = h[syms[i]]
                energy += hi*spins[i]
            except KeyError:
                pass
        for i in range(ncols - 1):
            for j in range(i + 1, ncols):
                try:
                    Jij = J[(syms[i], syms[j])]
                    energy += Jij*spins[i]*spins[j]
                except KeyError:
                    pass

        # Keep track of minimum energy, within precision limits.
        all_energies.add(energy)
        if energy < min_energy:
            min_energy = energy
            if cl_args.verbose == 0:
                table = []    # We don't need excited states unless we're outputting them.
        if energy == min_energy or cl_args.verbose > 0:
            table.append((spins, energy))

    # Output the ground-state rows (or all rows if verbosity is enabled).
    print " ".join(["%*s" % (width, s) for s in syms]), "    Energy", "GS"
    print " ".join(["-"*width for s in syms]), "-"*10, "--"
    for t in table:
        spins, energy = t
        spin_str = " ".join(["%+*d" % (width, s) for s in spins])
        energy_str = "%10.2f" % energy
        gs_str = " N"
        if energy == min_energy:
            gs_str = " Y"
        print spin_str, energy_str, gs_str
    print ""

    # Also output the gap between the ground state and first excited state.
    all_energies = sorted(all_energies)
    if len(all_energies) == 1:
        print "=== GAP: N/A ==="
    else:
        print "=== GAP:", all_energies[1] - all_energies[0], "==="

# Process each macro in turn.
print "=== MACRO: %s ===" % cl_args.macro
print ""
syms, h, J = macro_to_coeffs(qmasm.macros[cl_args.macro])
output_ground_state(syms, h, J)