"""
Unit tests for landlab.components.snow.meteorology

@author Tian Gan  Sept 2023
"""

from datetime import datetime

import numpy as np
import pytest
from numpy.testing import assert_almost_equal

from landlab import RasterModelGrid
from landlab.components import Meteorology


def test_create_fields():
    """check to make sure the right fields are created"""

    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    Meteorology(grid, start_datetime="2023-01-01 12:00:00")

    assert len(grid.at_node.keys()) == 35
    assert_almost_equal(grid.at_node["atmosphere_bottom_air__temperature"], 1)
    assert_almost_equal(grid.at_node["land_surface__temperature"], -1)
    assert_almost_equal(grid.at_node["land_surface__latitude"], 40)
    assert_almost_equal(grid.at_node["land_surface__longitude"], -105)
    assert_almost_equal(grid.at_node["land_surface__aspect_angle"], 0)
    assert_almost_equal(grid.at_node["land_surface__slope_angle"], 0)
    assert_almost_equal(grid.at_node["snowpack__depth"], 0)
    assert_almost_equal(grid.at_node["land_surface__albedo"], 0.3)
    assert_almost_equal(grid.at_node["land_surface__emissivity"], 0.98)
    assert_almost_equal(
        grid.at_node["atmosphere_aerosol_dust__reduction_of_transmittance"], 0.0
    )
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air__brutsaert_emissivity_canopy_factor"], 0
    )
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air__brutsaert_emissivity_cloud_factor"], 0
    )
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_water-vapor__relative_saturation"], 0.5
    )
    assert_almost_equal(grid.at_node["atmosphere_bottom_air__pressure"], 1000)
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_flow__log_law_roughness_length"], 0.02
    )
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_flow__speed_reference_height"], 2
    )
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_flow__reference-height_speed"], 3
    )


def test_assign_parameters():
    """Test when parameters are updated"""

    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    with pytest.raises(ValueError):
        met = Meteorology(grid, start_datetime="23/01/0112:00:00")

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00")

    # constants
    assert met._g == np.float64(9.81)
    assert met._kappa == np.float64(0.408)
    assert met._Lv == np.float64(2500000)
    assert met._Lf == np.float64(334000)
    assert met._sigma == np.float64(5.67e-8)
    assert met._C_to_K == np.float64(273.15)

    assert met._one_seventh == np.float64(1) / 7
    assert met._hours_per_day == np.float64(24)
    assert met._latent_heat_constant == np.float64(0.662)

    # parameters
    assert met._datetime_obj == datetime(2023, 1, 1, 12, 0)
    assert met._GMT_offset == 0
    assert met._rho_H2O == 1000
    assert met._rho_air == 1.2614
    assert met._Cp_air == 1005.7
    assert not met._satterlund

    with pytest.raises(AssertionError):
        met.rho_H2O = -1

    with pytest.raises(AssertionError):
        met.rho_air = -1

    with pytest.raises(AssertionError):
        met.Cp_air = -1


def test_update_bulk_richardson_number():
    """test Ri"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00")
    met.update_bulk_richardson_number()

    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_flow__bulk_richardson_number"], -0.0159037
    )


def test_update_bulk_aero_conductance():
    """test Dn, Dh, De"""
    # neutral condition (T_air == T_surf)
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", 1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00")
    met.update_bulk_aero_conductance()

    assert_almost_equal(
        grid.at_node[
            "atmosphere_bottom_air__neutral_bulk_heat_aerodynamic_conductance"
        ],
        0.02354779,
    )  # Dn
    assert_almost_equal(
        grid.at_node[
            "atmosphere_bottom_air__bulk_sensible_heat_aerodynamic_conductance"
        ],
        0.02354779,
    )  # Dh
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air__bulk_latent_heat_aerodynamic_conductance"],
        0.02354779,
    )  # De

    # not neutral condition
    grid = RasterModelGrid((2, 2))
    grid.add_field(
        "atmosphere_bottom_air__temperature", np.array([1.0, 1.0, 1.0, 1.0]), at="node"
    )
    grid.add_field(
        "land_surface__temperature", np.array([1.0, -1.0, 2.0, 2.0]), at="node"
    )
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00")
    met.update_bulk_richardson_number()
    met.update_bulk_aero_conductance()

    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_flow__bulk_richardson_number"],
        np.array([0, -0.0159037, 0.00795185, 0.00795185]),
    )  # Ri
    assert_almost_equal(
        grid.at_node[
            "atmosphere_bottom_air__neutral_bulk_heat_aerodynamic_conductance"
        ],
        0.0235478,
    )  # Dn
    assert_almost_equal(
        grid.at_node[
            "atmosphere_bottom_air__bulk_sensible_heat_aerodynamic_conductance"
        ],
        np.array([0.0235478, 0.02729276, 0.02181324, 0.02181324]),
    )  # Dh
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air__bulk_latent_heat_aerodynamic_conductance"],
        np.array([0.0235478, 0.02729276, 0.02181324, 0.02181324]),
    )  # De


def test_update_sensible_heat_flux():
    """test Qh"""
    grid = RasterModelGrid((2, 2))
    grid.add_field(
        "atmosphere_bottom_air__temperature", np.array([1.0, 1.0, 1.0, 1.0]), at="node"
    )
    grid.add_field(
        "land_surface__temperature", np.array([1.0, -1.0, 2.0, 2.0]), at="node"
    )
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00")
    met.update_bulk_richardson_number()
    met.update_bulk_aero_conductance()
    met.update_sensible_heat_flux()

    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_land_net-sensible-heat__energy_flux"],
        np.array([0.0, 69.2466541, -27.6720539, -27.6720539]),
    )  # Qh


def test_update_saturation_vapor_pressure():
    """test e_sat_air, e_sat_surf"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    # Brutsaert method
    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=False)

    met.update_saturation_vapor_pressure(MBAR=False, SURFACE=False)
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_water-vapor__saturated_partial_pressure"],
        0.6570069,
    )  # e_sat_air

    met.update_saturation_vapor_pressure(MBAR=True, SURFACE=True)
    assert_almost_equal(
        grid.at_node["land_surface_air_water-vapor__saturated_partial_pressure"],
        5.678657,
    )  # e_sat_surf

    # Satterlund method
    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=True)

    met.update_saturation_vapor_pressure(MBAR=False, SURFACE=False)
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_water-vapor__saturated_partial_pressure"],
        0.65630758,
    )  # e_sat_air

    met.update_saturation_vapor_pressure(MBAR=True, SURFACE=True)
    assert_almost_equal(
        grid.at_node["land_surface_air_water-vapor__saturated_partial_pressure"],
        5.6758734,
    )  # e_sat_surf


def test_update_vapor_pressure():
    """test e_air , e_surf"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )

    # Brutsaert method
    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=False)

    met.update_saturation_vapor_pressure()
    met.update_vapor_pressure()
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_water-vapor__partial_pressure"], 0.26280276
    )  # e_air

    met.update_saturation_vapor_pressure(SURFACE=True)
    met.update_vapor_pressure(SURFACE=True)
    assert_almost_equal(
        grid.at_node["land_surface_air_water-vapor__partial_pressure"], 0.22714628
    )  # e_surf

    # Satterlund method
    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=True)

    met.update_saturation_vapor_pressure()
    met.update_vapor_pressure()
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_water-vapor__partial_pressure"], 0.262523032
    )  # e_air

    met.update_saturation_vapor_pressure(SURFACE=True)
    met.update_vapor_pressure(SURFACE=True)
    assert_almost_equal(
        grid.at_node["land_surface_air_water-vapor__partial_pressure"], 0.227034936
    )  # e_surf


def test_update_dew_point():
    """test T_dew"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=False)
    met.update_saturation_vapor_pressure(MBAR=True)
    met.update_vapor_pressure()
    met.update_dew_point()
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_water-vapor__dew_point_temperature"],
        -11.11746824,
    )  # T_dew


def update_precipitable_water_content():
    """test W_p"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=False)
    met.update_saturation_vapor_pressure(MBAR=True)
    met.update_vapor_pressure()
    met.update_dew_point()
    met.update_precipitable_water_content()
    assert_almost_equal(
        grid.at_node["atmosphere_air-column_water-vapor__liquid-equivalent_depth"],
        0.56593058,
    )  # W_p


def test_update_latent_heat_flux():
    """test Qe"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=False)
    met.update_bulk_richardson_number()
    met.update_bulk_aero_conductance()
    met.update_saturation_vapor_pressure(MBAR=True)  # e_sat_air
    met.update_saturation_vapor_pressure(MBAR=True, SURFACE=True)  # e_sat_surf
    met.update_vapor_pressure()  # e_air
    met.update_precipitable_water_content()  # W_p
    met.update_dew_point()  # T_dew
    met.update_vapor_pressure(SURFACE=True)  # e_surf
    met.update_latent_heat_flux()  # Qe

    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_land_net-latent-heat__energy_flux"],
        20.31593647,
    )  # Qe


def test_update_conduction_heat_flux():
    """test Qc"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00")
    met.update_conduction_heat_flux()
    assert_almost_equal(
        grid.at_node["snowpack_land_surface_net-conduction-heat__energy_flux"], 0
    )  # Qc


def test_update_advection_heat_flux():
    """test Qa"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00")
    met.update_advection_heat_flux()
    assert_almost_equal(
        grid.at_node["snowpack_land_surface_net-advection-heat__energy_flux"], 0
    )  # Qa


def test_update_julian_day():  # TODO: double this calculation
    """test julian_day"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_field(
        "land_surface__longitude", np.array([-75.0, -95.0, -105.0, -125.0]), at="node"
    )

    met = Meteorology(
        grid,
        start_datetime="2023-01-01 12:00:00",
        GMT_offset=np.array([-5, -6, -7, -8]),
    )

    dt = 60 * 60 * 48  # 48 hr
    met.update_julian_day(dt)

    assert met._julian_day == 2.5
    assert_almost_equal(
        met._TSN_offset, np.array([0.07271961, -0.26061373, 0.07271961, -0.26061373])
    )  # TSN_offset


def test_update_net_shortwave_radiation():
    """test Qn_SW"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_cloud_factor", 0.5, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_canopy_factor", 0.7, at="node"
    )
    dt = 60 * 60 * 48  # 48hr

    met = Meteorology(
        grid, start_datetime="2023-01-01 12:00:00", GMT_offset=-7, satterlund=False
    )

    met.update_saturation_vapor_pressure(MBAR=True)
    met.update_vapor_pressure()
    met.update_dew_point()
    met.update_precipitable_water_content()

    met.update_julian_day(dt)
    met.update_net_shortwave_radiation()

    assert_almost_equal(
        grid.at_node["land_surface_net-shortwave-radiation__energy_flux"], 537.4501879
    )  # Qn_SW


def test_update_em_air():
    """test em_air"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_cloud_factor", 0.5, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_canopy_factor", 0.7, at="node"
    )

    # Brutsaert method
    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=False)
    met.update_saturation_vapor_pressure(MBAR=True, SURFACE=False)
    met.update_vapor_pressure(SURFACE=False)
    met.update_em_air()

    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air__emissivity"], 0.90170103
    )  # em_air

    # Satterlund method
    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=True)
    met.update_saturation_vapor_pressure(MBAR=True, SURFACE=False)
    met.update_vapor_pressure(SURFACE=False)
    met.update_em_air()

    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air__emissivity"], 0.73468296
    )  # em_air


def test_update_net_longwave_radiation():
    """test Qn_LW"""
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_cloud_factor", 0.5, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_canopy_factor", 0.7, at="node"
    )

    met = Meteorology(grid, start_datetime="2023-01-01 12:00:00", satterlund=False)
    met.update_saturation_vapor_pressure(MBAR=True, SURFACE=False)
    met.update_vapor_pressure(SURFACE=False)
    met.update_em_air()
    met.update_net_longwave_radiation()

    assert_almost_equal(
        grid.at_node["land_surface_net-longwave-radiation__energy_flux"], -21.79438345
    )  # Qn_LW


def test_update_net_energy_flux():
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_cloud_factor", 0.5, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_canopy_factor", 0.7, at="node"
    )
    dt = 60 * 60 * 48  # 48hr

    met = Meteorology(
        grid, start_datetime="2023-01-01 12:00:00", GMT_offset=-7, satterlund=False
    )

    met.update_bulk_richardson_number()  # Ri
    met.update_bulk_aero_conductance()  # Dn, Dh, De
    met.update_sensible_heat_flux()  # Qh
    met.update_saturation_vapor_pressure(MBAR=True)  # e_sat_air
    met.update_saturation_vapor_pressure(MBAR=True, SURFACE=True)  # e_sat_surf
    met.update_vapor_pressure()  # e_air
    met.update_dew_point()  # T_dew
    met.update_precipitable_water_content()  # W_p
    met.update_vapor_pressure(SURFACE=True)  # e_surf
    met.update_latent_heat_flux()  # Qe
    met.update_conduction_heat_flux()  # Qc
    met.update_advection_heat_flux()  # Qa
    met.update_julian_day(dt)  # julian_day
    met.update_net_shortwave_radiation()  # Qn_SW
    met.update_em_air()  # em_air
    met.update_net_longwave_radiation()  # Qn_LW
    met.update_net_energy_flux()  # Q_sum

    assert_almost_equal(
        grid.at_node["land_surface_net-total-energy__energy_flux"], 605.21839499
    )  # Q_sum


def test_run_multiple_steps():
    """test to run multiple steps"""

    # step 1: run one step with default setting
    grid = RasterModelGrid((2, 2))
    grid.add_full("atmosphere_bottom_air__temperature", 1, at="node")
    grid.add_full("land_surface__temperature", -1, at="node")
    grid.add_full("land_surface__latitude", 40, at="node")
    grid.add_full("land_surface__longitude", -105, at="node")
    grid.add_full(
        "atmosphere_bottom_air_water-vapor__relative_saturation", 0.4, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_cloud_factor", 0.5, at="node"
    )
    grid.add_full(
        "atmosphere_bottom_air__brutsaert_emissivity_canopy_factor", 0.7, at="node"
    )
    dt = 60 * 60 * 48  # 48hr

    met = Meteorology(
        grid, start_datetime="2023-01-01 12:00:00", GMT_offset=-7, satterlund=False
    )
    met.run_one_step(dt)

    assert_almost_equal(
        grid.at_node["land_surface_net-shortwave-radiation__energy_flux"], 537.4501879
    )  # Qn_SW
    assert_almost_equal(
        grid.at_node["land_surface_net-longwave-radiation__energy_flux"], -21.79438345
    )  # Qn_LW
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_land_net-sensible-heat__energy_flux"],
        69.2466541,
    )  # Qh
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_land_net-latent-heat__energy_flux"],
        20.31593647,
    )  # Qe
    assert_almost_equal(
        grid.at_node["snowpack_land_surface_net-conduction-heat__energy_flux"], 0
    )  # Qc
    assert_almost_equal(
        grid.at_node["snowpack_land_surface_net-advection-heat__energy_flux"], 0
    )  # Qa
    assert_almost_equal(
        grid.at_node["land_surface_net-total-energy__energy_flux"], 605.21839499
    )  # Q_sum

    # step2: change input values
    grid.at_node["atmosphere_bottom_air__temperature"].fill(2)
    grid.at_node["land_surface__temperature"].fill(-2)
    grid.at_node["snowpack__depth"].fill(0.02)
    grid.at_node["land_surface__albedo"].fill(0.9)
    grid.at_node["land_surface__emissivity"].fill(0.70)
    grid.at_node["atmosphere_aerosol_dust__reduction_of_transmittance"].fill(0.02)
    grid.at_node["atmosphere_bottom_air__brutsaert_emissivity_canopy_factor"].fill(0.02)
    grid.at_node["atmosphere_bottom_air__brutsaert_emissivity_cloud_factor"].fill(0.02)
    grid.at_node["atmosphere_bottom_air_water-vapor__relative_saturation"].fill(0.3)
    grid.at_node["atmosphere_bottom_air__pressure"].fill(1001)
    grid.at_node["atmosphere_bottom_air_flow__log_law_roughness_length"].fill(0.04)
    grid.at_node["atmosphere_bottom_air_flow__speed_reference_height"].fill(10)
    grid.at_node["atmosphere_bottom_air_flow__reference-height_speed"].fill(5)

    met.run_one_step(dt)

    assert_almost_equal(
        grid.at_node["land_surface_net-shortwave-radiation__energy_flux"], 567.3765643
    )  # Qn_SW
    assert_almost_equal(
        grid.at_node["land_surface_net-longwave-radiation__energy_flux"], -72.29069181
    )  # Qn_LW
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_land_net-sensible-heat__energy_flux"],
        217.72253814,
    )  # Qh
    assert_almost_equal(
        grid.at_node["atmosphere_bottom_air_land_net-latent-heat__energy_flux"],
        47.94515872,
    )  # Qe
    assert_almost_equal(
        grid.at_node["snowpack_land_surface_net-conduction-heat__energy_flux"], 0
    )  # Qc
    assert_almost_equal(
        grid.at_node["snowpack_land_surface_net-advection-heat__energy_flux"], 0
    )  # Qa
    assert_almost_equal(
        grid.at_node["land_surface_net-total-energy__energy_flux"], 760.75356934
    )  # Q_sum
