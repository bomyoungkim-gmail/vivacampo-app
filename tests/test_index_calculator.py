import numpy as np

from worker.pipeline.index_calculator import IndexCalculator


def test_ndvi_range():
    red = np.array([[0.1, 0.2], [0.3, 0.4]])
    nir = np.array([[0.6, 0.4], [0.2, 0.1]])
    ndvi = IndexCalculator.ndvi(red, nir)
    assert np.all(ndvi <= 1)
    assert np.all(ndvi >= -1)


def test_ndwi_range():
    green = np.array([[0.1, 0.2], [0.3, 0.4]])
    nir = np.array([[0.6, 0.4], [0.2, 0.1]])
    ndwi = IndexCalculator.ndwi(green, nir)
    assert np.all(ndwi <= 1)
    assert np.all(ndwi >= -1)


def test_ndmi_range():
    nir = np.array([[0.6, 0.4], [0.2, 0.1]])
    swir = np.array([[0.1, 0.2], [0.3, 0.4]])
    ndmi = IndexCalculator.ndmi(nir, swir)
    assert np.all(ndmi <= 1)
    assert np.all(ndmi >= -1)


def test_savi_range():
    red = np.array([[0.1, 0.2], [0.3, 0.4]])
    nir = np.array([[0.6, 0.4], [0.2, 0.1]])
    savi = IndexCalculator.savi(red, nir)
    assert np.all(savi <= 1)
    assert np.all(savi >= -1)


def test_rvi_range():
    vv = np.array([[0.2, 0.2], [0.2, 0.2]])
    vh = np.array([[0.1, 0.1], [0.1, 0.1]])
    rvi = IndexCalculator.rvi(vv, vh)
    assert np.all(rvi >= 0)
    assert np.all(rvi <= 1)


def test_radar_ratio():
    vv = np.array([[2.0, 4.0]])
    vh = np.array([[1.0, 2.0]])
    ratio = IndexCalculator.radar_ratio(vv, vh)
    assert np.allclose(ratio, np.array([[0.5, 0.5]]))


def test_mask_clouds_resizes_and_masks():
    data = np.array([[1.0, 2.0], [3.0, 4.0]])
    scl = np.array([[0]])  # invalid class, will expand to 2x2
    masked = IndexCalculator.mask_clouds(data, scl)
    assert np.isnan(masked).all()

    scl_ok = np.array([[4]])  # vegetation class
    unmasked = IndexCalculator.mask_clouds(data, scl_ok)
    assert np.isfinite(unmasked).all()
