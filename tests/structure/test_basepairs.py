# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

import pytest
import numpy as np
import biotite.structure as struc
import biotite.structure.io as strucio
from biotite.structure.info import residue
from os.path import join
from ..util import data_dir


def reversed_iterator(iter):
    """
    Returns a reversed list of the elements of an Iterator.
    """
    return reversed(list(iter))


@pytest.fixture
def nuc_sample_array():
    """
    Sample structure for basepair detection.
    """
    return strucio.load_structure(join(data_dir("structure"), "1qxb.cif"))

@pytest.fixture
def basepairs(nuc_sample_array):
    """
    Generate a test output for the base_pairs function.
    """
    residue_indices, residue_names = struc.residues.get_residues(
        nuc_sample_array
    )[0:24]
    return np.vstack((residue_indices[:12], np.flip(residue_indices)[:12])).T

def check_residue_starts(computed_starts, nuc_sample_array):
    """
    Assert that computed starts are residue starts.
    """
    residue_starts = struc.get_residue_starts(nuc_sample_array)
    for start in computed_starts.flatten():
        assert start in residue_starts

def check_output(computed_basepairs, basepairs):
    """
    Check the output of base_pairs.
    """

    # Check if basepairs are unique in computed_basepairs
    seen = set()
    assert (not any(
        (base1, base2) in seen) or (base2, base1 in seen)
        or seen.add((base1, base2)) for base1, base2 in computed_basepairs
        )
    # Check if the right number of basepairs is in computed_basepairs
    assert(len(computed_basepairs) == len(basepairs))
    # Check if the right basepairs are in computed_basepairs
    for comp_basepair in computed_basepairs:
        assert ((comp_basepair in basepairs) \
                or (comp_basepair in np.flip(basepairs)))

@pytest.mark.parametrize("unique_bool", [False, True])
def test_base_pairs_forward(nuc_sample_array, basepairs, unique_bool):
    """
    Test for the function base_pairs.
    """
    computed_basepairs = struc.base_pairs(nuc_sample_array, unique=unique_bool)
    check_residue_starts(computed_basepairs, nuc_sample_array)
    check_output(nuc_sample_array[computed_basepairs].res_id, basepairs)


def test_base_pairs_forward_no_hydrogen(nuc_sample_array, basepairs):
    """
    Test for the function base_pairs with the hydrogens removed from the
    test structure.
    """
    nuc_sample_array = nuc_sample_array[nuc_sample_array.element != "H"]
    computed_basepairs = struc.base_pairs(nuc_sample_array)
    check_residue_starts(computed_basepairs, nuc_sample_array)
    check_output(nuc_sample_array[computed_basepairs].res_id, basepairs)

@pytest.mark.parametrize("unique_bool", [False, True])
def test_base_pairs_reverse(nuc_sample_array, basepairs, unique_bool):
    """
    Reverse the order of residues in the atom_array and then test the
    function base_pairs.
    """

    # Reverse sequence of residues in nuc_sample_array
    reversed_nuc_sample_array = struc.AtomArray(0)
    for residue in reversed_iterator(struc.residue_iter(nuc_sample_array)):
        reversed_nuc_sample_array = reversed_nuc_sample_array + residue

    computed_basepairs = struc.base_pairs(
        reversed_nuc_sample_array, unique=unique_bool
    )
    check_residue_starts(computed_basepairs, reversed_nuc_sample_array)
    check_output(
        reversed_nuc_sample_array[computed_basepairs].res_id, basepairs
    )

def test_base_pairs_reverse_no_hydrogen(nuc_sample_array, basepairs):
    """
    Remove the hydrogens from the sample structure. Then reverse the
    order of residues in the atom_array and then test the function
    base_pairs.
    """
    nuc_sample_array = nuc_sample_array[nuc_sample_array.element != "H"]
    # Reverse sequence of residues in nuc_sample_array
    reversed_nuc_sample_array = struc.AtomArray(0)
    for residue in reversed_iterator(struc.residue_iter(nuc_sample_array)):
        reversed_nuc_sample_array = reversed_nuc_sample_array + residue

    computed_basepairs = struc.base_pairs(reversed_nuc_sample_array)
    check_residue_starts(computed_basepairs, reversed_nuc_sample_array)
    check_output(
        reversed_nuc_sample_array[computed_basepairs].res_id, basepairs
    )

@pytest.mark.parametrize("seed", range(10))
def test_base_pairs_reordered(nuc_sample_array, seed):
    """
    Test the function base_pairs with structure where the atoms are not
    in the RCSB-Order.
    """
    # Randomly reorder the atoms in each residue
    nuc_sample_array_reordered = struc.AtomArray(0)
    np.random.seed(seed)

    for residue in struc.residue_iter(nuc_sample_array):
        bound = residue.array_length()
        indices = np.random.choice(
            np.arange(bound), bound,replace=False
        )
        nuc_sample_array_reordered += residue[..., indices]

    assert(np.all(
        struc.base_pairs(nuc_sample_array)
        == struc.base_pairs(nuc_sample_array_reordered)
    ))

def test_map_nucleotide():
    """Test the function map_nucleotide with some examples.
    """
    pyrimidines = ['C', 'T', 'U']
    purines = ['A', 'G']

    # Test that the standard bases are correctly identified
    assert struc.map_nucleotide(residue('U')) == ('U', True)
    assert struc.map_nucleotide(residue('A')) == ('A', True)
    assert struc.map_nucleotide(residue('T')) == ('T', True)
    assert struc.map_nucleotide(residue('G')) == ('G', True)
    assert struc.map_nucleotide(residue('C')) == ('C', True)

    # Test that some non_standard nucleotides are mapped correctly to
    # pyrimidine/purine references
    psu_tuple = struc.map_nucleotide(residue('PSU'))
    assert psu_tuple[0] in pyrimidines
    assert psu_tuple[1] == False

    psu_tuple = struc.map_nucleotide(residue('3MC'))
    assert psu_tuple[0] in pyrimidines
    assert psu_tuple[1] == False

    i_tuple = struc.map_nucleotide(residue('I'))
    assert i_tuple[0] in purines
    assert i_tuple[1] == False

    m7g_tuple = struc.map_nucleotide(residue('M7G'))
    assert m7g_tuple[0] in purines
    assert m7g_tuple[1] == False

    assert struc.map_nucleotide(residue('ALA')) == (None, False)


def test_base_stacking():
    """
    Test ``base_stacking()`` using the DNA-double-helix 1BNA. It is
    expected that adjacent bases are stacked. However, due to
    distortions in the helix there are exception for this particular
    helix.
    """
    # Load the test structure (1BNA) - a DNA-double-helix
    helix = strucio.load_structure(join(data_dir("structure"), "1bna.mmtf"))

    residue_starts = struc.get_residue_starts(helix)

    # For a DNA-double-helix it is expected that adjacent bases are
    # stacked.
    expected_stackings = []
    for i in range(1, 24):
        expected_stackings.append([i, i+1])

    # Due to distortions in the helix not all adjacent bases have a
    # geometry that meets the criteria of `base_stacking`.
    expected_stackings.remove([10, 11])
    expected_stackings.remove([12, 13])
    expected_stackings.remove([13, 14])

    stacking = struc.base_stacking(helix)

    # Assert stacking outputs correct residue starts
    for stacking_start in stacking.flatten():
        assert stacking_start in residue_starts

    # Assert the number of stacking interactions is corrrect
    assert len(struc.base_stacking(helix)) == len(expected_stackings)

    # Assert the stacking interactions are correct
    for interaction in helix[stacking].res_id:
        assert list(interaction) in expected_stackings


