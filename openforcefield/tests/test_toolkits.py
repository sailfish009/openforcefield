#!/usr/bin/env python

#=============================================================================================
# MODULE DOCSTRING
#=============================================================================================

"""
Tests for cheminformatics toolkit wrappers

"""

#=============================================================================================
# GLOBAL IMPORTS
#=============================================================================================

from simtk import unit
import numpy as np
from numpy.testing import assert_almost_equal
from tempfile import NamedTemporaryFile

import pytest
from openforcefield.utils.toolkits import (OpenEyeToolkitWrapper, RDKitToolkitWrapper,
                                           AmberToolsToolkitWrapper, ToolkitRegistry,
                                           GAFFAtomTypeWarning, UndefinedStereochemistryError)
from openforcefield.utils import get_data_file_path
from openforcefield.topology.molecule import Molecule
from openforcefield.tests.test_forcefield import create_ethanol, create_cyclohexane


#=============================================================================================
# TESTS
#=============================================================================================

class TestOpenEyeToolkitWrapper:
    """Test the OpenEyeToolkitWrapper"""

    # TODO: Make separate smiles_add_H and smiles_explicit_H tests

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_smiles(self):
        """Test OpenEyeToolkitWrapper to_smiles() and from_smiles()"""
        toolkit_wrapper = OpenEyeToolkitWrapper()

        # This differs from RDKit's SMILES due to different canonicalization schemes

        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = Molecule.from_smiles(smiles,
                                        toolkit_registry=toolkit_wrapper)
        smiles2 = molecule.to_smiles(toolkit_registry=toolkit_wrapper)
        assert smiles == smiles2

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_smiles_missing_stereochemistry(self):
        """Test OpenEyeToolkitWrapper to_smiles() and from_smiles()"""
        toolkit_wrapper = OpenEyeToolkitWrapper()

        unspec_chiral_smiles = r"C\C(F)=C(/F)CC(C)(Cl)Br"
        spec_chiral_smiles = r"C\C(F)=C(/F)C[C@@](C)(Cl)Br"
        unspec_db_smiles = r"CC(F)=C(F)C[C@@](C)(Cl)Br"
        spec_db_smiles = r"C\C(F)=C(/F)C[C@@](C)(Cl)Br"

        for title, smiles, raises_exception in [("unspec_chiral_smiles", unspec_chiral_smiles, True),
                                                ("spec_chiral_smiles", spec_chiral_smiles, False),
                                                ("unspec_db_smiles", unspec_db_smiles, True),
                                                ("spec_db_smiles", spec_db_smiles, False),
                                                ]:
            if raises_exception:
                with pytest.raises(UndefinedStereochemistryError) as context:
                    Molecule.from_smiles(smiles, toolkit_registry=toolkit_wrapper)
                Molecule.from_smiles(smiles,
                                     toolkit_registry=toolkit_wrapper,
                                     allow_undefined_stereo=True)
            else:
                Molecule.from_smiles(smiles, toolkit_registry=toolkit_wrapper)

    # TODO: test_smiles_round_trip


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_smiles_add_H(self):
        """Test OpenEyeToolkitWrapper for adding explicit hydrogens"""
        toolkit_wrapper = OpenEyeToolkitWrapper()
        # This differs from RDKit's SMILES due to different canonicalization schemes
        input_smiles = 'CC'
        expected_output_smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = Molecule.from_smiles(input_smiles,
                                        toolkit_registry=toolkit_wrapper)
        smiles2 = molecule.to_smiles(toolkit_registry=toolkit_wrapper)
        assert expected_output_smiles == smiles2

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_smiles_charged(self):
        """Test OpenEyeToolkitWrapper functions for reading/writing charged SMILES"""
        toolkit_wrapper = OpenEyeToolkitWrapper()
        # This differs from RDKit's expected output due to different canonicalization schemes
        smiles = '[H]C([H])([H])[N+]([H])([H])[H]'
        molecule = Molecule.from_smiles(smiles,
                                        toolkit_registry=toolkit_wrapper)
        smiles2 = molecule.to_smiles(toolkit_registry=toolkit_wrapper)
        assert smiles == smiles2


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_to_from_openeye_core_props_filled(self):
        """Test OpenEyeToolkitWrapper to_openeye() and from_openeye()"""
        toolkit_wrapper = OpenEyeToolkitWrapper()

        # Replacing with a simple molecule with stereochemistry
        input_smiles = r'C\C(F)=C(/F)C[C@@](C)(Cl)Br'
        expected_output_smiles = r'[H]C([H])([H])/C(=C(/C([H])([H])[C@@](C([H])([H])[H])(Cl)Br)\F)/F'
        molecule = Molecule.from_smiles(input_smiles, toolkit_registry=toolkit_wrapper)
        assert molecule.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles

        # Populate core molecule property fields
        molecule.name = 'Alice'
        partial_charges = unit.Quantity(np.array([-.9, -.8, -.7, -.6,
                                                  -.5, -.4, -.3, -.2,
                                                  -.1, 0., .1, .2,
                                                  .3, .4, .5, .6,
                                                  .7, .8]), unit.elementary_charge)
        molecule.partial_charges = partial_charges
        coords = unit.Quantity(np.array([['0.0', '1.0', '2.0'], ['3.0', '4.0', '5.0'], ['6.0', '7.0', '8.0'],
                                         ['9.0', '10.0', '11.0'], ['12.0', '13.0', '14.0'],
                                         ['15.0', '16.0', '17.0'],
                                         ['18.0', '19.0', '20.0'], ['21.0', '22.0', '23.0'],
                                         ['24.0', '25.0', '26.0'],
                                         ['27.0', '28.0', '29.0'], ['30.0', '31.0', '32.0'],
                                         ['33.0', '34.0', '35.0'],
                                         ['36.0', '37.0', '38.0'], ['39.0', '40.0', '41.0'],
                                         ['42.0', '43.0', '44.0'],
                                         ['45.0', '46.0', '47.0'], ['48.0', '49.0', '50.0'],
                                         ['51.0', '52.0', '53.0']]),
                               unit.angstrom)
        molecule.add_conformer(coords)
        # Populate core atom property fields
        molecule.atoms[2].name = 'Bob'
        # Ensure one atom has its stereochemistry specified
        central_carbon_stereo_specified = False
        for atom in molecule.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "S":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified

        # Populate bond core property fields
        fractional_bond_orders = [float(val) for val in range(1, 19)]
        for fbo, bond in zip(fractional_bond_orders, molecule.bonds):
            bond.fractional_bond_order = fbo

        # Do a first conversion to/from oemol
        oemol = molecule.to_openeye()
        molecule2 = Molecule.from_openeye(oemol)

        # Test that properties survived first conversion
        # assert molecule.to_dict() == molecule2.to_dict()
        assert molecule.name == molecule2.name
        # NOTE: This expects the same indexing scheme in the original and new molecule

        central_carbon_stereo_specified = False
        for atom in molecule2.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "S":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified
        for atom1, atom2 in zip(molecule.atoms, molecule2.atoms):
            assert atom1.to_dict() == atom2.to_dict()
        for bond1, bond2 in zip(molecule.bonds, molecule2.bonds):
            assert bond1.to_dict() == bond2.to_dict()
        assert (molecule._conformers[0] == molecule2._conformers[0]).all()
        for pc1, pc2 in zip(molecule._partial_charges, molecule2._partial_charges):
            pc1_ul = pc1 / unit.elementary_charge
            pc2_ul = pc2 / unit.elementary_charge
            assert_almost_equal(pc1_ul, pc2_ul, decimal=6)
        assert molecule2.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_to_from_openeye_core_props_unset(self):
        """Test OpenEyeToolkitWrapper to_openeye() and from_openeye() when given empty core property fields"""
        toolkit_wrapper = OpenEyeToolkitWrapper()

        # Using a simple molecule with tetrahedral and bond stereochemistry
        input_smiles = r'C\C(F)=C(/F)C[C@](C)(Cl)Br'

        expected_output_smiles = r'[H]C([H])([H])/C(=C(/C([H])([H])[C@](C([H])([H])[H])(Cl)Br)\F)/F'
        molecule = Molecule.from_smiles(input_smiles, toolkit_registry=toolkit_wrapper)
        assert molecule.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles

        # Ensure one atom has its stereochemistry specified
        central_carbon_stereo_specified = False
        for atom in molecule.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "R":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified

        # Do a first conversion to/from oemol
        oemol = molecule.to_openeye()
        molecule2 = Molecule.from_openeye(oemol)

        # Test that properties survived first conversion
        assert molecule.name == molecule2.name
        # NOTE: This expects the same indexing scheme in the original and new molecule

        central_carbon_stereo_specified = False
        for atom in molecule2.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "R":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified
        for atom1, atom2 in zip(molecule.atoms, molecule2.atoms):
            assert atom1.to_dict() == atom2.to_dict()
        for bond1, bond2 in zip(molecule.bonds, molecule2.bonds):
            assert bond1.to_dict() == bond2.to_dict()
        assert (molecule._conformers == None)
        assert (molecule2._conformers == None)
        for pc1, pc2 in zip(molecule._partial_charges, molecule2._partial_charges):
            pc1_ul = pc1 / unit.elementary_charge
            pc2_ul = pc2 / unit.elementary_charge
            assert_almost_equal(pc1_ul, pc2_ul, decimal=6)
        assert molecule2.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_from_openeye_implicit_hydrogen(self):
        """
        Test OpenEyeToolkitWrapper for loading a molecule with implicit
        hydrogens (correct behavior is to add them explicitly)
        """
        from openeye import oechem

        smiles_impl = "C#C"
        oemol_impl = oechem.OEMol()
        oechem.OESmilesToMol(oemol_impl, smiles_impl)
        molecule_from_impl = Molecule.from_openeye(oemol_impl)

        assert molecule_from_impl.n_atoms == 4

        smiles_expl = "HC#CH"
        oemol_expl = oechem.OEMol()
        oechem.OESmilesToMol(oemol_expl, smiles_expl)
        molecule_from_expl = Molecule.from_openeye(oemol_expl)
        assert molecule_from_expl.to_smiles() == molecule_from_impl.to_smiles()

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_openeye_from_smiles_hydrogens_are_explicit(self):
        """
        Test to ensure that OpenEyeToolkitWrapper.from_smiles has the proper behavior with
        respect to its hydrogens_are_explicit kwarg
        """
        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles_impl = "C#C"
        with pytest.raises(ValueError,
                           match="but OpenEye Toolkit interpreted SMILES 'C#C' as having implicit hydrogen") as excinfo:
            offmol = Molecule.from_smiles(smiles_impl,
                                          toolkit_registry=toolkit_wrapper,
                                          hydrogens_are_explicit=True)
        offmol = Molecule.from_smiles(smiles_impl,
                                      toolkit_registry=toolkit_wrapper,
                                      hydrogens_are_explicit=False)
        assert offmol.n_atoms == 4

        smiles_expl = "HC#CH"
        offmol = Molecule.from_smiles(smiles_expl,
                                      toolkit_registry=toolkit_wrapper,
                                      hydrogens_are_explicit=True)
        assert offmol.n_atoms == 4
        # It's debatable whether this next function should pass. Strictly speaking, the hydrogens in this SMILES
        # _are_ explicit, so allowing "hydrogens_are_explicit=False" through here is allowing a contradiction.
        # We might rethink the name of this kwarg.

        offmol = Molecule.from_smiles(smiles_expl,
                                      toolkit_registry=toolkit_wrapper,
                                      hydrogens_are_explicit=False)
        assert offmol.n_atoms == 4



    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_get_sdf_coordinates(self):
        """Test OpenEyeToolkitWrapper for importing a single set of coordinates from a sdf file"""

        toolkit_wrapper = OpenEyeToolkitWrapper()
        filename = get_data_file_path('molecules/toluene.sdf')
        molecule = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecule._conformers) == 1
        assert molecule._conformers[0].shape == (15,3)

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_load_multiconformer_sdf_as_separate_molecules(self):
        """
        Test OpenEyeToolkitWrapper for reading a "multiconformer" SDF, which the OFF
        Toolkit should treat as separate molecules
        """
        toolkit_wrapper = OpenEyeToolkitWrapper()
        filename = get_data_file_path('molecules/methane_multiconformer.sdf')
        molecules = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecules) == 2
        assert len(molecules[0]._conformers) == 1
        assert len(molecules[1]._conformers) == 1
        assert molecules[0]._conformers[0].shape == (5, 3)

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_load_multiconformer_sdf_as_separate_molecules_properties(self):
        """
        Test OpenEyeToolkitWrapper for reading a "multiconformer" SDF, which the OFF
        Toolkit should treat as separate molecules
        """
        toolkit_wrapper = OpenEyeToolkitWrapper()
        filename = get_data_file_path('molecules/methane_multiconformer_properties.sdf')
        molecules = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecules) == 2
        assert len(molecules[0]._conformers) == 1
        assert len(molecules[1]._conformers) == 1
        assert molecules[0]._conformers[0].shape == (5, 3)
        assert molecules[0].properties['test_property_key'] == 'test_property_value'
        np.testing.assert_allclose(molecules[0].partial_charges / unit.elementary_charge,
                                          [-0.108680, 0.027170, 0.027170, 0.027170, 0.027170])
        assert molecules[1].properties['test_property_key'] == 'test_property_value2'
        assert molecules[1].properties['another_test_property_key'] == 'another_test_property_value'
        np.testing.assert_allclose(molecules[1].partial_charges / unit.elementary_charge,
                                   [0.027170, 0.027170, 0.027170, 0.027170, -0.108680])

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_write_sdf_charges(self):
        """Test OpenEyeToolkitWrapper for writing partial charges to a sdf file"""
        from openforcefield.tests.test_forcefield import create_ethanol
        from io import StringIO
        toolkit_wrapper = OpenEyeToolkitWrapper()
        ethanol = create_ethanol()
        sio = StringIO()
        ethanol.to_file(sio, 'SDF', toolkit_registry=toolkit_wrapper)
        sdf_text = sio.getvalue()
        # The output lines of interest here will look like
        # > <atom.dprop.PartialCharge>
        # -0.400000 -0.300000 -0.200000 -0.100000 0.000010 0.100000 0.200000 0.300000 0.400000
        # Parse the SDF text, grabbing the numeric line above
        sdf_split = sdf_text.split('\n')
        charge_line_found = False
        for line in sdf_split:
            if charge_line_found:
                charges = [float(i) for i in line.split()]
                break
            if '> <atom.dprop.PartialCharge>' in line:
                charge_line_found = True

        # Make sure that a charge line was ever found
        assert charge_line_found == True

        # Make sure that the charges found were correct
        assert_almost_equal(charges, [-0.4, -0.3, -0.2, -0.1, 0.00001, 0.1, 0.2, 0.3, 0.4])


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_write_sdf_no_charges(self):
        """Test OpenEyeToolkitWrapper for importing a charges from a sdf file"""
        from openforcefield.tests.test_forcefield import create_ethanol
        from io import StringIO
        toolkit_wrapper = OpenEyeToolkitWrapper()
        ethanol = create_ethanol()
        ethanol.partial_charges = None
        sio = StringIO()
        ethanol.to_file(sio, 'SDF', toolkit_registry=toolkit_wrapper)
        sdf_text = sio.getvalue()
        # In our current configuration, if the OFFMol doesn't have partial charges, we DO NOT want a partial charge
        # block to be written. For reference, it's possible to indicate that a partial charge is not known by writing
        # out "n/a" (or another placeholder) in the partial charge block atoms without charges.
        assert '<atom.dprop.PartialCharge>' not in sdf_text

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_sdf_properties_roundtrip(self):
        """Test OpenEyeToolkitWrapper for performing a round trip of a molecule with partial charge to and from
        a sdf file"""
        from openforcefield.tests.test_forcefield import create_ethanol
        toolkit_wrapper = OpenEyeToolkitWrapper()
        ethanol = create_ethanol()
        ethanol.properties['test_property'] = 'test_value'
        # The file is automatically deleted outside the with-clause.
        with NamedTemporaryFile(suffix='.sdf') as iofile:
            ethanol.to_file(iofile.name, file_format='SDF', toolkit_registry=toolkit_wrapper)
            ethanol2 = Molecule.from_file(iofile.name, file_format='SDF', toolkit_registry=toolkit_wrapper)
        np.testing.assert_allclose(ethanol.partial_charges / unit.elementary_charge,
                                   ethanol2.partial_charges / unit.elementary_charge)
        assert ethanol2.properties['test_property'] == 'test_value'

        # Now test with no properties or charges
        ethanol = create_ethanol()
        ethanol.partial_charges = None
        with NamedTemporaryFile(suffix='.sdf') as iofile:
            ethanol.to_file(iofile.name, file_format='SDF', toolkit_registry=toolkit_wrapper)
            ethanol2 = Molecule.from_file(iofile.name, file_format='SDF', toolkit_registry=toolkit_wrapper)
        assert ethanol2.partial_charges is None
        assert ethanol2.properties is None



    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_write_multiconformer_mol_as_sdf(self):
        """
        Test OpenEyeToolkitWrapper for writing a multiconformer molecule to SDF. The OFF toolkit should only
        save the first conformer.
        """
        toolkit_wrapper = OpenEyeToolkitWrapper()
        filename = get_data_file_path('molecules/ethanol.sdf')
        ethanol = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        ethanol.partial_charges = np.array([-4., -3., -2., -1., 0., 1., 2., 3., 4.]) * unit.elementary_charge
        ethanol.properties['test_prop'] = 'test_value'
        new_conf = ethanol.conformers[0] + (np.ones(ethanol.conformers[0].shape) * unit.angstrom)
        ethanol.add_conformer(new_conf)
        ethanol.to_file('temp.sdf', 'sdf', toolkit_registry=toolkit_wrapper)
        data = open('temp.sdf').read()
        # In SD format, each molecule (or "conformer", if you have a bone in your brain) ends with "$$$$"
        assert data.count('$$$$') == 1
        # A basic SDF for ethanol would be 27 lines, though the properties add three more
        assert len(data.split('\n')) == 30
        assert 'test_prop' in data
        assert '<atom.dprop.PartialCharge>' in data
        # Ensure the first conformer's first atom's X coordinate is in the file
        assert str(ethanol.conformers[0][0][0].value_in_unit(unit.angstrom))[:5] in data
        # Ensure the SECOND conformer's first atom's X coordinate is NOT in the file
        assert str(ethanol.conformers[1][0][0].in_units_of(unit.angstrom))[:5] not in data


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_get_mol2_coordinates(self):
        """Test OpenEyeToolkitWrapper for importing a single set of molecule coordinates"""
        toolkit_wrapper = OpenEyeToolkitWrapper()
        filename = get_data_file_path('molecules/toluene.mol2')
        molecule1 = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecule1._conformers) == 1
        assert molecule1._conformers[0].shape == (15, 3)
        assert_almost_equal(molecule1.conformers[0][5][1] / unit.angstrom, 22.98, decimal=2)

        # Test loading from file-like object
        with open(filename, 'r') as infile:
            molecule2 = Molecule(infile, file_format='MOL2', toolkit_registry=toolkit_wrapper)
        assert molecule1.is_isomorphic_with(molecule2)
        assert len(molecule2._conformers) == 1
        assert molecule2._conformers[0].shape == (15, 3)
        assert_almost_equal(molecule2.conformers[0][5][1] / unit.angstrom, 22.98, decimal=2)

        # Test loading from gzipped mol2
        import gzip
        with gzip.GzipFile(filename + '.gz', 'r') as infile:
            molecule3 = Molecule(infile, file_format='MOL2', toolkit_registry=toolkit_wrapper)
        assert molecule1.is_isomorphic_with(molecule3)
        assert len(molecule3._conformers) == 1
        assert molecule3._conformers[0].shape == (15, 3)
        assert_almost_equal(molecule3.conformers[0][5][1] / unit.angstrom, 22.98, decimal=2)

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_get_mol2_charges(self):
        """Test OpenEyeToolkitWrapper for importing a mol2 file specifying partial charges"""
        toolkit_wrapper = OpenEyeToolkitWrapper()
        filename = get_data_file_path('molecules/toluene_charged.mol2')
        molecule = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecule._conformers) == 1
        assert molecule._conformers[0].shape == (15,3)
        target_charges = unit.Quantity(np.array([-0.1342,-0.1271,-0.1271,-0.1310,
                                                 -0.1310,-0.0765,-0.0541, 0.1314,
                                                  0.1286, 0.1286, 0.1303, 0.1303,
                                                  0.0440, 0.0440, 0.0440]),
                                                unit.elementary_charge)
        for pc1, pc2 in zip(molecule._partial_charges, target_charges):
            pc1_ul = pc1 / unit.elementary_charge
            pc2_ul = pc2 / unit.elementary_charge
            assert_almost_equal(pc1_ul, pc2_ul, decimal=4)

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_get_mol2_gaff_atom_types(self):
        """Test that a warning is raised OpenEyeToolkitWrapper when it detects GAFF atom types in a mol2 file."""
        toolkit_wrapper = OpenEyeToolkitWrapper()
        mol2_file_path = get_data_file_path('molecules/AlkEthOH_test_filt1_ff.mol2')
        with pytest.warns(GAFFAtomTypeWarning, match='SYBYL'):
            Molecule.from_file(mol2_file_path, toolkit_registry=toolkit_wrapper)

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_generate_conformers(self):
        """Test OpenEyeToolkitWrapper generate_conformers()"""
        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = toolkit_wrapper.from_smiles(smiles)
        molecule.generate_conformers()
        assert molecule.n_conformers != 0
        assert not(molecule.conformers[0] == (0.*unit.angstrom)).all()

        # TODO: Make this test more robust

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_compute_partial_charges(self):
        """Test OpenEyeToolkitWrapper compute_partial_charges()"""
        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = toolkit_wrapper.from_smiles(smiles)
        # Ensure that an exception is raised if no conformers are provided
        with pytest.raises(Exception) as excinfo:
            molecule.compute_partial_charges(toolkit_registry=toolkit_wrapper)
        molecule.generate_conformers(toolkit_registry=toolkit_wrapper)
        # Ensure that an exception is raised if an invalid charge model is passed in
        with pytest.raises(Exception) as excinfo:
            charge_model = 'notARealChargeModel'
            molecule.compute_partial_charges(toolkit_registry=toolkit_wrapper, charge_model=charge_model)

        # TODO: Test all supported charge models
        # Note: "amber" and "amberff94" only work for a subset of residue types, so we'll need to find testing data for
        # those
        # charge_model = [,'amber','amberff94']
        # TODO: 'mmff' and 'mmff94' often assign charges of 0, presumably if the molecule is unrecognized.
        # charge_model = ['mmff', 'mmff94']
        for charge_model in ['noop', 'am1bcc', 'am1bccnosymspt', 'am1bccelf10']:
            with pytest.raises(NotImplementedError) as excinfo:
                molecule.compute_partial_charges(toolkit_registry=toolkit_wrapper)  # , charge_model=charge_model)
                charge_sum = 0 * unit.elementary_charge
                for pc in molecule._partial_charges:
                    charge_sum += pc
                assert charge_sum < 0.001 * unit.elementary_charge

        # For now, just test AM1-BCC while the SMIRNOFF spec for other charge models gets worked out
        molecule.compute_partial_charges_am1bcc(toolkit_registry=toolkit_wrapper)  # , charge_model=charge_model)
        charge_sum = 0 * unit.elementary_charge
        for pc in molecule._partial_charges:
            charge_sum += pc
        assert charge_sum < 0.001 * unit.elementary_charge

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_compute_partial_charges_net_charge(self):
        """Test OpenEyeToolkitWrapper compute_partial_charges() on a molecule with a net +1 charge"""

        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles = '[H]C([H])([H])[N+]([H])([H])[H]'
        molecule = toolkit_wrapper.from_smiles(smiles)
        molecule.generate_conformers(toolkit_registry=toolkit_wrapper)


        with pytest.raises(NotImplementedError) as excinfo:
            charge_model = 'notARealChargeModel'
            molecule.compute_partial_charges(toolkit_registry=toolkit_wrapper)#, charge_model=charge_model)

        # TODO: Test all supported charge models
        # TODO: "amber" and "amberff94" only work for a subset of residue types, so we'll need to find testing data for
        # those
        # charge_model = [,'amber','amberff94']
        # The 'noop' charge model doesn't add up to the formal charge, so we shouldn't test it
        # charge_model = ['noop']
        for charge_model in ['mmff', 'mmff94', 'am1bcc', 'am1bccnosymspt', 'am1bccelf10']:
            with pytest.raises(NotImplementedError) as excinfo:
                molecule.compute_partial_charges(toolkit_registry=toolkit_wrapper) #, charge_model=charge_model)
                charge_sum = 0 * unit.elementary_charge
                for pc in molecule._partial_charges:
                    charge_sum += pc
                assert 0.999 * unit.elementary_charge < charge_sum < 1.001 * unit.elementary_charge
        # For now, I'm just testing AM1-BCC (will test more when the SMIRNOFF spec for other charges is finalized)
        molecule.compute_partial_charges_am1bcc(toolkit_registry=toolkit_wrapper)
        charge_sum = 0 * unit.elementary_charge
        for pc in molecule._partial_charges:
            charge_sum += pc
        assert 0.999 * unit.elementary_charge < charge_sum < 1.001 * unit.elementary_charge


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_compute_partial_charges_trans_cooh_am1bcc(self):
        """Test OpenEyeToolkitWrapper for computing partial charges for problematic molecules, as exemplified by
        Issue 346 (https://github.com/openforcefield/openforcefield/issues/346)"""

        lysine = Molecule.from_smiles("C(CC[NH3+])C[C@@H](C(=O)O)N")
        toolkit_wrapper = OpenEyeToolkitWrapper()
        lysine.generate_conformers(toolkit_registry=toolkit_wrapper)
        lysine.compute_partial_charges_am1bcc(toolkit_registry=toolkit_wrapper)


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_assign_fractional_bond_orders(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders()"""

        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = toolkit_wrapper.from_smiles(smiles)
        molecule.generate_conformers(toolkit_registry=toolkit_wrapper)
        for bond_order_model in ['am1-wiberg', 'pm3-wiberg']:
            molecule.assign_fractional_bond_orders(toolkit_registry=toolkit_wrapper,
                                                    bond_order_model=bond_order_model)
            # TODO: Add test for equivalent Wiberg orders for equivalent bonds



    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_assign_fractional_bond_orders_neutral_charge_mol(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders() for neutral and charged molecule"""

        toolkit_wrapper = OpenEyeToolkitWrapper()
        # Reading neutral molecule from file
        filename = get_data_file_path('molecules/CID20742535_neutral.sdf')
        molecule1 = Molecule.from_file(filename)
        # Reading negative molecule from file
        filename = get_data_file_path('molecules/CID20742535_anion.sdf')
        molecule2 = Molecule.from_file(filename)

        # Checking that only one additional bond is present in the neutral molecule
        assert (len(molecule1.bonds) == len(molecule2.bonds)+1)

        for bond_order_model in ['am1-wiberg']:
            molecule1.assign_fractional_bond_orders(toolkit_registry=toolkit_wrapper,
                                                    bond_order_model=bond_order_model,
                                                    use_conformers=molecule1.conformers)

            for i in molecule1.bonds:
                if i.is_aromatic:
                    # Checking aromatic bonds
                    assert (1.05 < i.fractional_bond_order < 1.65)
                elif (i.atom1.atomic_number == 1 or i.atom2.atomic_number == 1):
                    # Checking bond order of C-H or O-H bonds are around 1
                    assert (0.85 < i.fractional_bond_order < 1.05)
                elif (i.atom1.atomic_number == 8 or i.atom2.atomic_number == 8):
                    # Checking C-O single bond
                    wbo_C_O_neutral = i.fractional_bond_order
                    assert (1.0 < wbo_C_O_neutral < 1.5)
                else:
                    # Should be C-C single bond
                    assert (i.atom1_index == 4 and i.atom2_index == 6) or (i.atom1_index == 6 and i.atom2_index == 4)
                    wbo_C_C_neutral = i.fractional_bond_order
                    assert (1.0 < wbo_C_C_neutral < 1.3)

            molecule2.assign_fractional_bond_orders(toolkit_registry=toolkit_wrapper,
                                                    bond_order_model=bond_order_model,
                                                    use_conformers=molecule2.conformers)
            for i in molecule2.bonds:
                if i.is_aromatic:
                    # Checking aromatic bonds
                    assert (1.05 < i.fractional_bond_order < 1.65)
                elif (i.atom1.atomic_number == 1 or i.atom2.atomic_number == 1):
                    # Checking bond order of C-H or O-H bonds are around 1
                    assert (0.85 < i.fractional_bond_order < 1.05)
                elif (i.atom1.atomic_number == 8 or i.atom2.atomic_number == 8):
                    # Checking C-O single bond
                    wbo_C_O_anion = i.fractional_bond_order
                    assert (1.3 < wbo_C_O_anion < 1.8)
                else:
                    # Should be C-C single bond
                    assert(i.atom1_index == 4 and i.atom2_index == 6) or (i.atom1_index == 6 and i.atom2_index == 4)
                    wbo_C_C_anion = i.fractional_bond_order
                    assert (1.0 < wbo_C_C_anion < 1.3)

            # Wiberg bond order of C-C single bond is higher in the anion
            assert (wbo_C_C_anion > wbo_C_C_neutral)
            # Wiberg bond order of C-O bond is higher in the anion
            assert (wbo_C_O_anion > wbo_C_O_neutral)

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_assign_fractional_bond_orders_charged(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders() on a molecule with net charge +1"""

        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles = '[H]C([H])([H])[N+]([H])([H])[H]'
        molecule = toolkit_wrapper.from_smiles(smiles)
        molecule.generate_conformers(toolkit_registry=toolkit_wrapper)
        for bond_order_model in ['am1-wiberg', 'pm3-wiberg']:
            molecule.assign_fractional_bond_orders(toolkit_registry=toolkit_wrapper,
                                                   bond_order_model=bond_order_model)
            # TODO: Add test for equivalent Wiberg orders for equivalent bonds

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_assign_fractional_bond_orders_invalid_method(self):
        """
        Test that OpenEyeToolkitWrapper assign_fractional_bond_orders() raises the
        correct error if an invalid charge model is provided
        """
        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles = '[H]C([H])([H])[N+]([H])([H])[H]'
        molecule = toolkit_wrapper.from_smiles(smiles)
        molecule.generate_conformers(toolkit_registry=toolkit_wrapper)
        expected_error = "Bond order model 'not a real bond order model' is not supported by " \
                         "OpenEyeToolkitWrapper. Supported models are ([[]'am1-wiberg', 'pm3-wiberg'[]])"
        with pytest.raises(ValueError, match=expected_error) as excinfo:
            molecule.assign_fractional_bond_orders(toolkit_registry=toolkit_wrapper,
                                                    bond_order_model='not a real bond order model')


    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_assign_fractional_bond_orders_double_bond(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders() on a molecule with a double bond"""

        toolkit_wrapper = OpenEyeToolkitWrapper()
        smiles = r'C\C(F)=C(/F)C[C@@](C)(Cl)Br'
        molecule = toolkit_wrapper.from_smiles(smiles)
        molecule.generate_conformers(toolkit_registry=toolkit_wrapper)
        for bond_order_model in ['am1-wiberg', 'pm3-wiberg']:
            molecule.assign_fractional_bond_orders(toolkit_registry=toolkit_wrapper,
                                                   bond_order_model=bond_order_model)
            # TODO: Add test for equivalent Wiberg orders for equivalent bonds

        double_bond_has_wbo_near_2 = False
        for bond in molecule.bonds:
            if bond.bond_order == 2:
                if 1.75 < bond.fractional_bond_order < 2.25:
                    double_bond_has_wbo_near_2 = True
        assert double_bond_has_wbo_near_2

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_find_rotatable_bonds(self):
        """Test finding rotatable bonds while ignoring some groups"""

        # test a simple molecule
        ethanol = create_ethanol()
        bonds = ethanol.find_rotatable_bonds()
        assert len(bonds) == 2
        for bond in bonds:
            assert ethanol.atoms[bond.atom1_index].atomic_number != 1
            assert ethanol.atoms[bond.atom2_index].atomic_number != 1

        # now ignore the C-O bond, forwards
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups='[#6:1]-[#8:2]')
        assert len(bonds) == 1
        assert ethanol.atoms[bonds[0].atom1_index].atomic_number == 6
        assert ethanol.atoms[bonds[0].atom2_index].atomic_number == 6

        # now ignore the O-C bond, backwards
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups='[#8:1]-[#6:2]')
        assert len(bonds) == 1
        assert ethanol.atoms[bonds[0].atom1_index].atomic_number == 6
        assert ethanol.atoms[bonds[0].atom2_index].atomic_number == 6

        # now ignore the C-C bond
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups='[#6:1]-[#6:2]')
        assert len(bonds) == 1
        assert ethanol.atoms[bonds[0].atom1_index].atomic_number == 6
        assert ethanol.atoms[bonds[0].atom2_index].atomic_number == 8

        # ignore a list of searches, forward
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups=['[#6:1]-[#8:2]', '[#6:1]-[#6:2]'])
        assert bonds == []

        # ignore a list of searches, backwards
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups=['[#6:1]-[#6:2]', '[#8:1]-[#6:2]'])
        assert bonds == []

        # test  molecules that should have no rotatable bonds
        cyclohexane = create_cyclohexane()
        bonds = cyclohexane.find_rotatable_bonds()
        assert bonds == []

        methane = Molecule.from_smiles('C')
        bonds = methane.find_rotatable_bonds()
        assert bonds == []

        ethene = Molecule.from_smiles('C=C')
        bonds = ethene.find_rotatable_bonds()
        assert bonds == []

        terminal_forwards = '[*]~[*:1]-[X2H1,X3H2,X4H3:2]-[#1]'
        terminal_backwards = '[#1]-[X2H1,X3H2,X4H3:1]-[*:2]~[*]'
        # test removing terminal rotors
        toluene = Molecule.from_file(get_data_file_path('molecules/toluene.sdf'))
        bonds = toluene.find_rotatable_bonds()
        assert len(bonds) == 1
        assert toluene.atoms[bonds[0].atom1_index].atomic_number == 6
        assert toluene.atoms[bonds[0].atom2_index].atomic_number == 6

        # find terminal bonds forward
        bonds = toluene.find_rotatable_bonds(ignore_functional_groups=terminal_forwards)
        assert bonds == []

        # find terminal bonds backwards
        bonds = toluene.find_rotatable_bonds(ignore_functional_groups=terminal_backwards)
        assert bonds == []
        
        
        # TODO: Check partial charge invariants (total charge, charge equivalence)

        # TODO: Add test for aromaticity
        # TODO: Add test and molecule functionality for isotopes



class TestRDKitToolkitWrapper:
    """Test the RDKitToolkitWrapper"""
    
    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_smiles(self):
        """Test RDKitToolkitWrapper to_smiles() and from_smiles()"""
        toolkit_wrapper = RDKitToolkitWrapper()
        # This differs from OE's expected output due to different canonicalization schemes
        smiles = '[H][C]([H])([H])[C]([H])([H])[H]'
        molecule = Molecule.from_smiles(smiles,
                                        toolkit_registry=toolkit_wrapper)
        smiles2 = molecule.to_smiles(toolkit_registry=toolkit_wrapper)
        #print(smiles, smiles2)
        assert smiles == smiles2

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    @pytest.mark.parametrize("smiles,exception_regex", [
        (r"C\C(F)=C(/F)CC(C)(Cl)Br", "Undefined chiral centers"),
        (r"C\C(F)=C(/F)C[C@@](C)(Cl)Br", None),
        (r"CC(F)=C(F)C[C@@](C)(Cl)Br", "Bonds with undefined stereochemistry")
    ])
    def test_smiles_missing_stereochemistry(self, smiles, exception_regex):
        """Test RDKitToolkitWrapper to_smiles() and from_smiles() when given ambiguous stereochemistry"""
        toolkit_wrapper = RDKitToolkitWrapper()

        if exception_regex is not None:
            with pytest.raises(UndefinedStereochemistryError, match=exception_regex):
                Molecule.from_smiles(smiles, toolkit_registry=toolkit_wrapper)
            Molecule.from_smiles(smiles,
                                 toolkit_registry=toolkit_wrapper,
                                 allow_undefined_stereo=True)
        else:
            Molecule.from_smiles(smiles, toolkit_registry=toolkit_wrapper)

    # TODO: test_smiles_round_trip

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_smiles_add_H(self):
        """Test RDKitToolkitWrapper to_smiles() and from_smiles()"""
        toolkit_wrapper = RDKitToolkitWrapper()
        input_smiles = 'CC'
        # This differs from OE's expected output due to different canonicalization schemes
        expected_output_smiles = '[H][C]([H])([H])[C]([H])([H])[H]'
        molecule = Molecule.from_smiles(input_smiles,
                                        toolkit_registry=toolkit_wrapper)
        smiles2 = molecule.to_smiles(toolkit_registry=toolkit_wrapper)
        assert smiles2 == expected_output_smiles

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_rdkit_from_smiles_hydrogens_are_explicit(self):
        """
        Test to ensure that RDKitToolkitWrapper.from_smiles has the proper behavior with
        respect to its hydrogens_are_explicit kwarg
        """
        toolkit_wrapper = RDKitToolkitWrapper()
        smiles_impl = "C#C"
        with pytest.raises(ValueError,
                           match="but RDKit toolkit interpreted SMILES 'C#C' as having implicit hydrogen") as excinfo:
            offmol = Molecule.from_smiles(smiles_impl,
                                          toolkit_registry=toolkit_wrapper,
                                          hydrogens_are_explicit=True)
        offmol = Molecule.from_smiles(smiles_impl,
                                      toolkit_registry=toolkit_wrapper,
                                      hydrogens_are_explicit=False)
        assert offmol.n_atoms == 4

        smiles_expl = "[H][C]#[C][H]"
        offmol = Molecule.from_smiles(smiles_expl,
                                      toolkit_registry=toolkit_wrapper,
                                      hydrogens_are_explicit=True)
        assert offmol.n_atoms == 4
        # It's debatable whether this next function should pass. Strictly speaking, the hydrogens in this SMILES
        # _are_ explicit, so allowing "hydrogens_are_explicit=False" through here is allowing a contradiction.
        # We might rethink the name of this kwarg.

        offmol = Molecule.from_smiles(smiles_expl,
                                      toolkit_registry=toolkit_wrapper,
                                      hydrogens_are_explicit=False)
        assert offmol.n_atoms == 4


    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_smiles_charged(self):
        """Test RDKitWrapper functions for reading/writing charged SMILES"""
        toolkit_wrapper = RDKitToolkitWrapper()
        # This differs from OE's expected output due to different canonicalization schemes
        smiles = '[H][C]([H])([H])[N+]([H])([H])[H]'
        molecule = Molecule.from_smiles(smiles,
                                        toolkit_registry=toolkit_wrapper)
        smiles2 = molecule.to_smiles(toolkit_registry=toolkit_wrapper)
        assert smiles == smiles2

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_to_from_rdkit_core_props_filled(self):
        """Test RDKitToolkitWrapper to_rdkit() and from_rdkit() when given populated core property fields"""
        toolkit_wrapper = RDKitToolkitWrapper()

        # Replacing with a simple molecule with stereochemistry
        input_smiles = r'C\C(F)=C(/F)C[C@@](C)(Cl)Br'
        expected_output_smiles = r'[H][C]([H])([H])/[C]([F])=[C](\[F])[C]([H])([H])[C@@]([Cl])([Br])[C]([H])([H])[H]'
        molecule = Molecule.from_smiles(input_smiles, toolkit_registry=toolkit_wrapper)
        assert molecule.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles

        # Populate core molecule property fields
        molecule.name = 'Alice'
        partial_charges = unit.Quantity(np.array([-.9, -.8, -.7, -.6,
                                                  -.5, -.4, -.3, -.2,
                                                  -.1,  0.,  .1,  .2,
                                                   .3,  .4,  .5,  .6,
                                                   .7,  .8]), unit.elementary_charge)
        molecule.partial_charges = partial_charges
        coords = unit.Quantity(np.array([['0.0', '1.0', '2.0'],    ['3.0', '4.0', '5.0'],    ['6.0', '7.0', '8.0'],
                                         ['9.0', '10.0', '11.0'] , ['12.0', '13.0', '14.0'], ['15.0', '16.0', '17.0'],
                                         ['18.0', '19.0', '20.0'], ['21.0', '22.0', '23.0'], ['24.0', '25.0', '26.0'],
                                         ['27.0', '28.0', '29.0'], ['30.0', '31.0', '32.0'], ['33.0', '34.0', '35.0'],
                                         ['36.0', '37.0', '38.0'], ['39.0', '40.0', '41.0'], ['42.0', '43.0', '44.0'],
                                         ['45.0', '46.0', '47.0'], ['48.0', '49.0', '50.0'], ['51.0', '52.0', '53.0']]),
                                    unit.angstrom)
        molecule.add_conformer(coords)
        # Populate core atom property fields
        molecule.atoms[2].name = 'Bob'
        # Ensure one atom has its stereochemistry specified
        central_carbon_stereo_specified = False
        for atom in molecule.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "S":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified

        # Populate bond core property fields
        fractional_bond_orders = [float(val) for val in range(18)]
        for fbo, bond in zip(fractional_bond_orders, molecule.bonds):
            bond.fractional_bond_order = fbo

        # Do a first conversion to/from oemol
        rdmol = molecule.to_rdkit()
        molecule2 = Molecule.from_rdkit(rdmol)

        # Test that properties survived first conversion
        #assert molecule.to_dict() == molecule2.to_dict()
        assert molecule.name == molecule2.name
        # NOTE: This expects the same indexing scheme in the original and new molecule

        central_carbon_stereo_specified = False
        for atom in molecule2.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "S":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified
        for atom1, atom2 in zip(molecule.atoms, molecule2.atoms):
            assert atom1.to_dict() == atom2.to_dict()
        for bond1, bond2 in zip(molecule.bonds, molecule2.bonds):
            assert bond1.to_dict() == bond2.to_dict()
        assert (molecule._conformers[0] == molecule2._conformers[0]).all()
        for pc1, pc2 in zip(molecule._partial_charges, molecule2._partial_charges):
            pc1_ul = pc1 / unit.elementary_charge
            pc2_ul = pc2 / unit.elementary_charge
            assert_almost_equal(pc1_ul, pc2_ul, decimal=6)
        assert molecule2.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles
        # TODO: This should be its own test

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_to_from_rdkit_core_props_unset(self):
        """Test RDKitToolkitWrapper to_rdkit() and from_rdkit() when given empty core property fields"""
        toolkit_wrapper = RDKitToolkitWrapper()

        # Replacing with a simple molecule with stereochemistry
        input_smiles = r'C\C(F)=C(/F)C[C@](C)(Cl)Br'
        expected_output_smiles = r'[H][C]([H])([H])/[C]([F])=[C](\[F])[C]([H])([H])[C@]([Cl])([Br])[C]([H])([H])[H]'
        molecule = Molecule.from_smiles(input_smiles, toolkit_registry=toolkit_wrapper)
        assert molecule.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles

        # Ensure one atom has its stereochemistry specified
        central_carbon_stereo_specified = False
        for atom in molecule.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "R":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified

        # Do a first conversion to/from oemol
        rdmol = molecule.to_rdkit()
        molecule2 = Molecule.from_rdkit(rdmol)

        # Test that properties survived first conversion
        assert molecule.name == molecule2.name
        # NOTE: This expects the same indexing scheme in the original and new molecule

        central_carbon_stereo_specified = False
        for atom in molecule2.atoms:
            if (atom.atomic_number == 6) and atom.stereochemistry == "R":
                central_carbon_stereo_specified = True
        assert central_carbon_stereo_specified
        for atom1, atom2 in zip(molecule.atoms, molecule2.atoms):
            assert atom1.to_dict() == atom2.to_dict()
        for bond1, bond2 in zip(molecule.bonds, molecule2.bonds):
            assert bond1.to_dict() == bond2.to_dict()
        assert (molecule._conformers == None)
        assert (molecule2._conformers == None)
        for pc1, pc2 in zip(molecule._partial_charges, molecule2._partial_charges):
            pc1_ul = pc1 / unit.elementary_charge
            pc2_ul = pc2 / unit.elementary_charge
            assert_almost_equal(pc1_ul, pc2_ul, decimal=6)
        assert molecule2.to_smiles(toolkit_registry=toolkit_wrapper) == expected_output_smiles
        
    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_get_sdf_coordinates(self):
        """Test RDKitToolkitWrapper for importing a single set of coordinates from a sdf file"""
        toolkit_wrapper = RDKitToolkitWrapper()
        filename = get_data_file_path('molecules/toluene.sdf')
        molecule = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecule._conformers) == 1
        assert molecule._conformers[0].shape == (15, 3)
        assert_almost_equal(molecule.conformers[0][5][1] / unit.angstrom, 2.0104, decimal=4)

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_read_sdf_charges(self):
        """Test RDKitToolkitWrapper for importing a charges from a sdf file"""
        toolkit_wrapper = RDKitToolkitWrapper()
        filename = get_data_file_path('molecules/ethanol_partial_charges.sdf')
        molecule = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert molecule.partial_charges is not None
        assert molecule.partial_charges[0] == -0.4 * unit.elementary_charge
        assert molecule.partial_charges[-1] == 0.4 * unit.elementary_charge

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_write_sdf_charges(self):
        """Test RDKitToolkitWrapper for writing partial charges to a sdf file"""
        from openforcefield.tests.test_forcefield import create_ethanol
        from io import StringIO
        toolkit_wrapper = RDKitToolkitWrapper()
        ethanol = create_ethanol()
        sio = StringIO()
        ethanol.to_file(sio, 'SDF', toolkit_registry=toolkit_wrapper)
        sdf_text = sio.getvalue()
        # The output lines of interest here will look like
        # >  <atom.dprop.PartialCharge>  (1)
        # -0.40000000000000002 -0.29999999999999999 -0.20000000000000001 -0.10000000000000001 0.01 0.10000000000000001 0.20000000000000001 0.29999999999999999 0.40000000000000002

        # Parse the SDF text, grabbing the numeric line above
        sdf_split = sdf_text.split('\n')
        charge_line_found = False
        for line in sdf_split:
            if charge_line_found:
                charges = [float(i) for i in line.split()]
                break
            if '>  <atom.dprop.PartialCharge>' in line:
                charge_line_found = True

        # Make sure that a charge line was ever found
        assert charge_line_found

        # Make sure that the charges found were correct
        assert_almost_equal(charges, [-0.4, -0.3, -0.2, -0.1, 0.00001, 0.1, 0.2, 0.3, 0.4])


    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_sdf_charges_roundtrip(self):
        """Test RDKitToolkitWrapper for performing a round trip of a molecule with partial charge to and from
        a sdf file"""
        from openforcefield.tests.test_forcefield import create_ethanol
        toolkit_wrapper = RDKitToolkitWrapper()
        ethanol = create_ethanol()
        # The file is automatically deleted outside the with-clause.
        with NamedTemporaryFile(suffix='.sdf') as iofile:
            ethanol.to_file(iofile.name, file_format='SDF', toolkit_registry=toolkit_wrapper)
            #raise Exception(open(iofile.name).read())
            ethanol2 = Molecule.from_file(iofile.name, file_format='SDF', toolkit_registry=toolkit_wrapper)
        assert (ethanol.partial_charges == ethanol2.partial_charges).all()

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_write_sdf_no_charges(self):
        """Test RDKitToolkitWrapper for importing a charges from a sdf file"""
        from openforcefield.tests.test_forcefield import create_ethanol
        from io import StringIO
        toolkit_wrapper = RDKitToolkitWrapper()
        ethanol = create_ethanol()
        ethanol.partial_charges = None
        sio = StringIO()
        ethanol.to_file(sio, 'SDF', toolkit_registry=toolkit_wrapper)
        sdf_text = sio.getvalue()
        # In our current configuration, if the OFFMol doesn't have partial charges, we DO NOT want a partial charge
        # block to be written. For reference, it's possible to indicate that a partial charge is not known by writing
        # out "n/a" (or another placeholder) in the partial charge block atoms without charges.
        assert '>  <atom.dprop.PartialCharge>' not in sdf_text


    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_load_multiconformer_sdf_as_separate_molecules(self):
        """
        Test RDKitToolkitWrapper for reading a "multiconformer" SDF, which the OFF
        Toolkit should treat as separate molecules
        """
        toolkit_wrapper = RDKitToolkitWrapper()
        filename = get_data_file_path('molecules/methane_multiconformer.sdf')
        molecules = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecules) == 2
        assert len(molecules[0]._conformers) == 1
        assert len(molecules[1]._conformers) == 1
        assert molecules[0]._conformers[0].shape == (5, 3)

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_load_multiconformer_sdf_as_separate_molecules_properties(self):
        """
        Test RDKitToolkitWrapper for reading a "multiconformer" SDF, which the OFF
        Toolkit should treat as separate molecules
        """
        toolkit_wrapper = RDKitToolkitWrapper()
        filename = get_data_file_path('molecules/methane_multiconformer_properties.sdf')
        molecules = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecules) == 2
        assert len(molecules[0]._conformers) == 1
        assert len(molecules[1]._conformers) == 1
        assert molecules[0]._conformers[0].shape == (5, 3)
        assert molecules[0].properties['test_property_key'] == 'test_property_value'
        np.testing.assert_allclose(molecules[0].partial_charges / unit.elementary_charge,
                                          [-0.108680, 0.027170, 0.027170, 0.027170, 0.027170])
        assert molecules[1].properties['test_property_key'] == 'test_property_value2'
        assert molecules[1].properties['another_test_property_key'] == 'another_test_property_value'
        np.testing.assert_allclose(molecules[1].partial_charges / unit.elementary_charge,
                                   [0.027170, 0.027170, 0.027170, 0.027170, -0.108680])

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_write_multiconformer_mol_as_sdf(self):
        """
        Test RDKitToolkitWrapper for writing a multiconformer molecule to SDF. The OFF toolkit should only
        save the first conformer
        """
        toolkit_wrapper = RDKitToolkitWrapper()
        filename = get_data_file_path('molecules/ethanol.sdf')
        ethanol = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        ethanol.partial_charges = np.array([-4., -3., -2., -1., 0., 1., 2., 3., 4.]) * unit.elementary_charge
        ethanol.properties['test_prop'] = 'test_value'
        new_conf = ethanol.conformers[0] + (np.ones(ethanol.conformers[0].shape) * unit.angstrom)
        ethanol.add_conformer(new_conf)
        ethanol.to_file('temp.sdf', 'sdf', toolkit_registry=toolkit_wrapper)
        data = open('temp.sdf').read()
        # In SD format, each molecule (or "conformer", if you have a bone in your brain) ends with "$$$$"
        assert data.count('$$$$') == 1
        # A basic SDF for ethanol would be 27 lines, though the properties add three more
        assert len(data.split('\n')) == 30
        assert 'test_prop' in data
        assert '<atom.dprop.PartialCharge>' in data
        # Ensure the first conformer's first atom's X coordinate is in the file
        assert str(ethanol.conformers[0][0][0].value_in_unit(unit.angstrom))[:5] in data
        # Ensure the SECOND conformer's first atom's X coordinate is NOT in the file
        assert str(ethanol.conformers[1][0][0].in_units_of(unit.angstrom))[:5] not in data

    # Unskip this when we implement PDB-reading support for RDKitToolkitWrapper
    @pytest.mark.skip
    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_get_pdb_coordinates(self):
        """Test RDKitToolkitWrapper for importing a single set of coordinates from a pdb file"""
        toolkit_wrapper = RDKitToolkitWrapper()
        filename = get_data_file_path('molecules/toluene.pdb')
        molecule = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecule._conformers) == 1
        assert molecule._conformers[0].shape == (15,3)

    # Unskip this when we implement PDB-reading support for RDKitToolkitWrapper
    @pytest.mark.skip
    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_load_aromatic_pdb(self):
        """Test OpenEyeToolkitWrapper for importing molecule conformers"""
        toolkit_wrapper = RDKitToolkitWrapper()
        filename = get_data_file_path('molecules/toluene.pdb')
        molecule = Molecule.from_file(filename, toolkit_registry=toolkit_wrapper)
        assert len(molecule._conformers) == 1
        assert molecule._conformers[0].shape == (15,3)

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_generate_conformers(self):
        """Test RDKitToolkitWrapper generate_conformers()"""
        toolkit_wrapper = RDKitToolkitWrapper()
        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = toolkit_wrapper.from_smiles(smiles)
        molecule.generate_conformers()
        # TODO: Make this test more robust

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_find_rotatable_bonds(self):
        """Test finding rotatable bonds while ignoring some groups"""

        # test a simple molecule
        ethanol = create_ethanol()
        bonds = ethanol.find_rotatable_bonds()
        assert len(bonds) == 2
        for bond in bonds:
            assert ethanol.atoms[bond.atom1_index].atomic_number != 1
            assert ethanol.atoms[bond.atom2_index].atomic_number != 1

        # now ignore the C-O bond, forwards
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups='[#6:1]-[#8:2]')
        assert len(bonds) == 1
        assert ethanol.atoms[bonds[0].atom1_index].atomic_number == 6
        assert ethanol.atoms[bonds[0].atom2_index].atomic_number == 6

        # now ignore the O-C bond, backwards
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups='[#8:1]-[#6:2]')
        assert len(bonds) == 1
        assert ethanol.atoms[bonds[0].atom1_index].atomic_number == 6
        assert ethanol.atoms[bonds[0].atom2_index].atomic_number == 6

        # now ignore the C-C bond
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups='[#6:1]-[#6:2]')
        assert len(bonds) == 1
        assert ethanol.atoms[bonds[0].atom1_index].atomic_number == 6
        assert ethanol.atoms[bonds[0].atom2_index].atomic_number == 8

        # ignore a list of searches, forward
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups=['[#6:1]-[#8:2]', '[#6:1]-[#6:2]'])
        assert bonds == []

        # ignore a list of searches, backwards
        bonds = ethanol.find_rotatable_bonds(ignore_functional_groups=['[#6:1]-[#6:2]', '[#8:1]-[#6:2]'])
        assert bonds == []

        # test  molecules that should have no rotatable bonds
        cyclohexane = create_cyclohexane()
        bonds = cyclohexane.find_rotatable_bonds()
        assert bonds == []

        methane = Molecule.from_smiles('C')
        bonds = methane.find_rotatable_bonds()
        assert bonds == []

        ethene = Molecule.from_smiles('C=C')
        bonds = ethene.find_rotatable_bonds()
        assert bonds == []

        terminal_forwards = '[*]~[*:1]-[X2H1,X3H2,X4H3:2]-[#1]'
        terminal_backwards = '[#1]-[X2H1,X3H2,X4H3:1]-[*:2]~[*]'
        # test removing terminal rotors
        toluene = Molecule.from_file(get_data_file_path('molecules/toluene.sdf'))
        bonds = toluene.find_rotatable_bonds()
        assert len(bonds) == 1
        assert toluene.atoms[bonds[0].atom1_index].atomic_number == 6
        assert toluene.atoms[bonds[0].atom2_index].atomic_number == 6

        # find terminal bonds forward
        bonds = toluene.find_rotatable_bonds(ignore_functional_groups=terminal_forwards)
        assert bonds == []

        # find terminal bonds backwards
        bonds = toluene.find_rotatable_bonds(ignore_functional_groups=terminal_backwards)
        assert bonds == []

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_to_rdkit_losing_aromaticity_(self):
        # test the example given in issue #513
        # <https://github.com/openforcefield/openforcefield/issues/513>
        smiles = "[H]c1c(c(c(c(c1OC2=C(C(=C(N3C2=C(C(=C3[H])C#N)[H])[H])F)[H])OC([H])([H])C([H])([H])N4C(=C(C(=O)N(C4=O)[H])[H])[H])[H])F)[H]"

        mol = Molecule.from_smiles(smiles)
        rdmol = mol.to_rdkit()

        # now make sure the aromaticity matches for each atom
        for (offatom, rdatom) in zip(mol.atoms, rdmol.GetAtoms()):
            assert offatom.is_aromatic is rdatom.GetIsAromatic()


        
        # TODO: Add test for higher bonds orders
        # TODO: Add test for aromaticity
        # TODO: Add test and molecule functionality for isotopes
        # TODO: Add read tests for MOL/SDF, SMI
        # TODO: Add read tests fpr multi-SMI files
        # TODO: Add read tests for both files and file-like objects
        # TODO: Add read/write tests for gzipped files
        # TODO: Add write tests for all formats



        
class TestAmberToolsToolkitWrapper:
    """Test the AmberToolsToolkitWrapper"""

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
                    reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_compute_partial_charges(self):
        """Test OpenEyeToolkitWrapper compute_partial_charges()"""
        toolkit_registry = ToolkitRegistry(toolkit_precedence=[AmberToolsToolkitWrapper, RDKitToolkitWrapper])

        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = Molecule.from_smiles(smiles, toolkit_registry=toolkit_registry)
        molecule.generate_conformers(toolkit_registry=toolkit_registry)

        # TODO: Implementation of these tests is pending a decision on the API for our charge model
        with pytest.raises(NotImplementedError) as excinfo:
            charge_model = 'notARealChargeModel'
            molecule.compute_partial_charges(toolkit_registry=toolkit_registry)#, charge_model=charge_model)

        # ['cm1', 'cm2']
        for charge_model in ['gas', 'mul', 'bcc']:
            with pytest.raises(NotImplementedError) as excinfo:
                molecule.compute_partial_charges(toolkit_registry=toolkit_registry)#, charge_model=charge_model)
                charge_sum = 0 * unit.elementary_charge
                for pc in molecule._partial_charges:
                    charge_sum += pc
                assert charge_sum < 0.01 * unit.elementary_charge

        # For now, just test AM1-BCC while the SMIRNOFF spec for other charge models gets worked out
        molecule.compute_partial_charges_am1bcc(toolkit_registry=toolkit_registry)  # , charge_model=charge_model)
        charge_sum = 0 * unit.elementary_charge
        for pc in molecule._partial_charges:
            charge_sum += pc
        assert charge_sum < 0.002 * unit.elementary_charge



    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
                        reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_compute_partial_charges_net_charge(self):
        """Test OpenEyeToolkitWrapper compute_partial_charges() on a molecule with a net +1 charge"""
        toolkit_registry = ToolkitRegistry(toolkit_precedence=[AmberToolsToolkitWrapper, RDKitToolkitWrapper])
        smiles = '[H]C([H])([H])[N+]([H])([H])[H]'
        molecule = Molecule.from_smiles(smiles, toolkit_registry=toolkit_registry)
        molecule.generate_conformers(toolkit_registry=toolkit_registry)


        with pytest.raises(NotImplementedError) as excinfo:
            charge_model = 'notARealChargeModel'
            molecule.compute_partial_charges(toolkit_registry=toolkit_registry)#, charge_model=charge_model)

        # TODO: Figure out why ['cm1', 'cm2'] fail
        for charge_model in  ['gas', 'mul', 'bcc']:
            with pytest.raises(NotImplementedError) as excinfo:
                molecule.compute_partial_charges(toolkit_registry=toolkit_registry)#, charge_model=charge_model)
                charge_sum = 0 * unit.elementary_charge
                for pc in molecule._partial_charges:
                    charge_sum += pc
                assert 0.99 * unit.elementary_charge < charge_sum < 1.01 * unit.elementary_charge

        # For now, I'm just testing AM1-BCC (will test more when the SMIRNOFF spec for other charges is finalized)
        molecule.compute_partial_charges_am1bcc(toolkit_registry=toolkit_registry)
        charge_sum = 0 * unit.elementary_charge
        for pc in molecule._partial_charges:
            charge_sum += pc
        assert 0.999 * unit.elementary_charge < charge_sum < 1.001 * unit.elementary_charge

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
                        reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_assign_fractional_bond_orders(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders()"""

        toolkit_registry = ToolkitRegistry(toolkit_precedence=[AmberToolsToolkitWrapper, RDKitToolkitWrapper])
        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = toolkit_registry.call('from_smiles', smiles)
        for bond_order_model in ['am1-wiberg']:
            molecule.assign_fractional_bond_orders(toolkit_registry=toolkit_registry, bond_order_model=bond_order_model)
            # TODO: Add test for equivalent Wiberg orders for equivalent bonds

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
                        reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_assign_fractional_bond_orders_neutral_charge_mol(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders() for neutral and charged molecule.
        Also tests using existing conformers"""

        toolkit_registry = ToolkitRegistry(toolkit_precedence=[AmberToolsToolkitWrapper, RDKitToolkitWrapper])
        # Reading neutral molecule from file
        filename = get_data_file_path('molecules/CID20742535_neutral.sdf')
        molecule1 = Molecule.from_file(filename)
        # Reading negative molecule from file
        filename = get_data_file_path('molecules/CID20742535_anion.sdf')
        molecule2 = Molecule.from_file(filename)

        # Checking that only one additional bond is present in the neutral molecule
        assert (len(molecule1.bonds) == len(molecule2.bonds) + 1)

        for bond_order_model in ['am1-wiberg']:
            molecule1.assign_fractional_bond_orders(toolkit_registry=toolkit_registry,
                                                    bond_order_model=bond_order_model,
                                                    use_conformers=molecule1.conformers)

            for i in molecule1.bonds:
                if i.is_aromatic:
                    # Checking aromatic bonds
                    assert (1.05 < i.fractional_bond_order < 1.65)
                elif (i.atom1.atomic_number == 1 or i.atom2.atomic_number == 1):
                    # Checking bond order of C-H or O-H bonds are around 1
                    assert (0.85 < i.fractional_bond_order < 1.05)
                elif (i.atom1.atomic_number == 8 or i.atom2.atomic_number == 8):
                    # Checking C-O single bond
                    wbo_C_O_neutral = i.fractional_bond_order
                    assert (1.0 < wbo_C_O_neutral < 1.5)
                else:
                    # Should be C-C single bond
                    assert (i.atom1_index == 4 and i.atom2_index == 6) or (i.atom1_index == 6 and i.atom2_index == 4)
                    wbo_C_C_neutral = i.fractional_bond_order
                    assert (1.0 < wbo_C_C_neutral < 1.3)

            molecule2.assign_fractional_bond_orders(toolkit_registry=toolkit_registry,
                                                    bond_order_model=bond_order_model,
                                                    use_conformers=molecule2.conformers)
            for i in molecule2.bonds:
                if i.is_aromatic:
                    # Checking aromatic bonds
                    assert (1.05 < i.fractional_bond_order < 1.65)

                elif (i.atom1.atomic_number == 1 or i.atom2.atomic_number == 1):
                    # Checking bond order of C-H or O-H bonds are around 1
                    assert (0.85 < i.fractional_bond_order < 1.05)
                elif (i.atom1.atomic_number == 8 or i.atom2.atomic_number == 8):
                    # Checking C-O single bond
                    wbo_C_O_anion = i.fractional_bond_order
                    assert (1.3 < wbo_C_O_anion < 1.8)
                else:
                    # Should be C-C single bond
                    assert (i.atom1_index == 4 and i.atom2_index == 6) or (i.atom1_index == 6 and i.atom2_index == 4)
                    wbo_C_C_anion = i.fractional_bond_order
                    assert (1.0 < wbo_C_C_anion < 1.3)

            # Wiberg bond order of C-C single bond is higher in the anion
            assert (wbo_C_C_anion > wbo_C_C_neutral)
            # Wiberg bond order of C-O bond is higher in the anion
            assert (wbo_C_O_anion > wbo_C_O_neutral)

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
                        reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_assign_fractional_bond_orders_charged(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders() on a molecule with net charge +1"""

        toolkit_registry = ToolkitRegistry(toolkit_precedence=[AmberToolsToolkitWrapper, RDKitToolkitWrapper])
        smiles = '[H]C([H])([H])[N+]([H])([H])[H]'
        molecule = toolkit_registry.call('from_smiles', smiles)
        for bond_order_model in ['am1-wiberg']:
            molecule.assign_fractional_bond_orders(toolkit_registry=toolkit_registry,
                                                    bond_order_model=bond_order_model)
            # TODO: Add test for equivalent Wiberg orders for equivalent bonds

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
                        reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_assign_fractional_bond_orders_invalid_method(self):
        """
        Test that AmberToolsToolkitWrapper.assign_fractional_bond_orders() raises the
        correct error if an invalid charge model is provided
        """

        toolkit_registry = ToolkitRegistry(toolkit_precedence=[AmberToolsToolkitWrapper, RDKitToolkitWrapper])
        smiles = '[H]C([H])([H])[N+]([H])([H])[H]'
        molecule = toolkit_registry.call('from_smiles', smiles)

        expected_error = "Bond order model 'not a real charge model' is not supported by " \
                         "AmberToolsToolkitWrapper. Supported models are ([[]'am1-wiberg'[]])"
        with pytest.raises(ValueError, match=expected_error) as excinfo:
            molecule.assign_fractional_bond_orders(toolkit_registry=AmberToolsToolkitWrapper(),
                                                   bond_order_model='not a real charge model')

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
                        reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_assign_fractional_bond_orders_double_bond(self):
        """Test OpenEyeToolkitWrapper assign_fractional_bond_orders() on a molecule with a double bond"""

        toolkit_registry = ToolkitRegistry(toolkit_precedence=[AmberToolsToolkitWrapper, RDKitToolkitWrapper])
        smiles = r'C\C(F)=C(/F)C[C@@](C)(Cl)Br'
        molecule = toolkit_registry.call('from_smiles', smiles)
        for bond_order_model in ['am1-wiberg']:
            molecule.assign_fractional_bond_orders(toolkit_registry=toolkit_registry,
                                                   bond_order_model=bond_order_model)
            # TODO: Add test for equivalent Wiberg orders for equivalent bonds

        double_bond_has_wbo_near_2 = False
        for bond in molecule.bonds:
            if bond.bond_order == 2:
                if 1.75 < bond.fractional_bond_order < 2.25:
                    double_bond_has_wbo_near_2 = True
        assert double_bond_has_wbo_near_2


class TestToolkitRegistry:
    """Test the ToolkitRegistry"""

    @pytest.mark.skipif(not OpenEyeToolkitWrapper.is_available(), reason='OpenEye Toolkit not available')
    def test_register_openeye(self):
        """Test creation of toolkit registry with OpenEye toolkit"""
        # Test registration of OpenEyeToolkitWrapper
        toolkit_precedence = [OpenEyeToolkitWrapper]
        registry = ToolkitRegistry(toolkit_precedence=toolkit_precedence, register_imported_toolkit_wrappers=False)
        #registry.register_toolkit(OpenEyeToolkitWrapper)
        assert set([type(c) for c in registry.registered_toolkits]) == set([OpenEyeToolkitWrapper])

        # Test ToolkitRegistry.resolve()
        assert registry.resolve('to_smiles') == registry.registered_toolkits[0].to_smiles

        # Test ToolkitRegistry.call()
        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = registry.call('from_smiles', smiles)
        smiles2 = registry.call('to_smiles', molecule)
        assert smiles == smiles2

    @pytest.mark.skipif(not RDKitToolkitWrapper.is_available(), reason='RDKit Toolkit not available')
    def test_register_rdkit(self):
        """Test creation of toolkit registry with RDKit toolkit"""
        # Test registration of RDKitToolkitWrapper
        toolkit_precedence = [RDKitToolkitWrapper]
        registry = ToolkitRegistry(toolkit_precedence=toolkit_precedence,
                                   register_imported_toolkit_wrappers=False)
        #registry.register_toolkit(RDKitToolkitWrapper)
        assert set([ type(c) for c in registry.registered_toolkits]) == set([RDKitToolkitWrapper])

        # Test ToolkitRegistry.resolve()
        assert registry.resolve('to_smiles') == registry.registered_toolkits[0].to_smiles

        # Test ToolkitRegistry.call()
        smiles = '[H][C]([H])([H])[C]([H])([H])[H]'
        molecule = registry.call('from_smiles', smiles)
        smiles2 = registry.call('to_smiles', molecule)
        assert smiles == smiles2

    @pytest.mark.skipif(
        not RDKitToolkitWrapper.is_available() or not AmberToolsToolkitWrapper.is_available(),
        reason='RDKitToolkit and AmberToolsToolkit not available')
    def test_register_ambertools(self):
        """Test creation of toolkit registry with AmberToolsToolkitWrapper and RDKitToolkitWrapper
        """
        # Test registration of AmberToolsToolkitWrapper
        toolkit_precedence = [AmberToolsToolkitWrapper, RDKitToolkitWrapper]
        registry = ToolkitRegistry(toolkit_precedence=toolkit_precedence,
                                   register_imported_toolkit_wrappers=False)
        #registry.register_toolkit(AmberToolsToolkitWrapper)
        assert set([ type(c) for c in registry.registered_toolkits]) == set([AmberToolsToolkitWrapper,RDKitToolkitWrapper])

        # Test ToolkitRegistry.resolve()
        registry.resolve('compute_partial_charges')
        assert registry.resolve('compute_partial_charges') == registry.registered_toolkits[0].compute_partial_charges

        # Test ToolkitRegistry.call()
        registry.register_toolkit(RDKitToolkitWrapper)
        smiles = '[H]C([H])([H])C([H])([H])[H]'
        molecule = registry.call('from_smiles', smiles)
        #partial_charges = registry.call('compute_partial_charges', molecule)

