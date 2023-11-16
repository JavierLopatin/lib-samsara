import numpy as np
import pytest
from ruptures import KernelCPD, pw_constant

import samsara.pelt as pelt


class TestPelt:
    @pytest.mark.parametrize(
        ("dates", "start_date", "expected"),
        [
            (
                np.array(
                    ["2006-07-13", "2007-01-13", "2010-08-13"], dtype="datetime64"
                ),
                "2006-09-05",
                np.array([1, 2]),
            )
        ],
    )
    def test_filter_index_by_date(self, dates, start_date, expected):
        res = pelt.filter_index_by_date(dates, start_date)
        assert res == pytest.approx(expected)

    @pytest.mark.parametrize(
        ("dates", "expected"),
        [
            (
                np.datetime64("2012-05-12"),
                2012.360656,
            ),
            (
                np.array(
                    ["2007-07-13", "2006-01-13", "2010-08-13"], dtype="datetime64"
                ),
                np.array([2007.528767, 2006.032877, 2010.613699]),
            ),
            (
                np.array(
                    ["2020-01-01", "2020-12-31", "2021-01-01", "2021-12-31"],
                    dtype="datetime64",
                ),
                np.array([2020.0, 2020.997267, 2021.0, 2021.997260]),
            ),
            (
                np.array(
                    [
                        "2000-05-12",
                        "2004-05-12",
                        "2008-05-12",
                        "2012-05-12",
                        "2016-05-12",
                        "2020-02-12",
                        "2020-05-12",
                        "2021-02-12",
                        "2021-05-12",
                    ],
                    dtype="datetime64",
                ),
                np.array(
                    [
                        2000.360656,
                        2004.360656,
                        2008.360656,
                        2012.360656,
                        2016.360656,
                        2020.114754,
                        2020.360656,
                        2021.115068,
                        2021.358904,
                    ]
                ),
            ),
        ],
    )
    def test_datetime_to_year_fraction(self, dates, expected):
        res = pelt.datetime_to_year_fraction(dates)
        assert res == pytest.approx(expected)

    @pytest.mark.parametrize(
        ("signal_breaks", "n_breaks", "start_date", "n_nan"),
        [
            (4, 3, None, 0),
            (7, 6, None, 4),
            (7, 6, "2010-05-20", 8),
            (6, 5, "2011-06-30", 10),
            (1, 6, None, 10),
            (1, 6, "2010-05-20", 12),
            (4, 4, None, 0),
        ],
    )
    def test_pixel_pelt(self, signal_breaks, n_breaks, start_date, n_nan):
        array = pw_constant(30, 1, signal_breaks, noise_std=2, seed=723)[0].reshape(30)
        dates = np.array([np.datetime64("2010-01-01") + 10 * i for i in range(30)])
        res = pelt.pixel_pelt(
            array=array,
            dates=dates,
            n_breaks=n_breaks,
            penalty=1,
            start_date=start_date,
        )
        assert res.shape == (n_breaks * 2,)
        assert np.count_nonzero(np.isnan(res)) == n_nan

    @pytest.mark.parametrize(
        ("n_breaks", "start_date", "n_nan"),
        [(3, None, 4), (4, None, 14), (3, "2007-03-28", 10)],
    )
    def test_block_pelt(
        self, pelt_signal, pelt_dates, pelt_year_fraction, n_breaks, start_date, n_nan
    ):
        array_shape = pelt_signal.shape
        algo_rpt = KernelCPD(kernel="rbf", min_size=3, jump=5)
        res = pelt.block_pelt(
            array=pelt_signal,
            dates=pelt_dates,
            year_fraction=pelt_year_fraction,
            n_breaks=n_breaks,
            penalty=1,
            start_date=start_date,
            algo_rpt=algo_rpt,
        )
        assert res.shape == (2 * n_breaks, array_shape[1], array_shape[2])
        assert np.count_nonzero(np.isnan(res)) == n_nan

    def test_block_pelt_int_breakidx(self):
        array = pw_constant(30, 1, 4, noise_std=2, seed=723)[0].reshape((30, 1, 1))
        dates = np.array([np.datetime64("2010-01-01") + 10 * i for i in range(30)])
        year_fraction = np.array(
            [
                2010.0,
                2010.02739726,
                2010.05479452,
                2010.08219178,
                2010.10958904,
                2010.1369863,
                2010.16438356,
                2010.19178082,
                2010.21917808,
                2010.24657534,
                2010.2739726,
                2010.30136986,
                2010.32876712,
                2010.35616438,
                2010.38356164,
                2010.4109589,
                2010.43835616,
                2010.46575342,
                2010.49315068,
                2010.52054795,
                2010.54794521,
                2010.57534247,
                2010.60273973,
                2010.63013699,
                2010.65753425,
                2010.68493151,
                2010.71232877,
                2010.73972603,
                2010.76712329,
                2010.79452055,
            ]
        )
        algo_rpt = KernelCPD(kernel="rbf", min_size=3, jump=5)
        res = pelt.block_pelt(
            array=array,
            dates=dates,
            year_fraction=year_fraction,
            n_breaks=4,
            penalty=1,
            start_date=None,
            algo_rpt=algo_rpt,
        )
        assert res.shape == (8, 1, 1)
        assert np.count_nonzero(np.isnan(res)) == 0

    @pytest.mark.parametrize(
        ("n_breaks", "start_date"),
        [(3, None), (4, None), (3, "2007-03-28")],
    )
    def test_pelt_xarray(self, pelt_signal_xarray, n_breaks, start_date):
        array_shape = pelt_signal_xarray.shape
        res = pelt.pelt(pelt_signal_xarray, n_breaks, 1, start_date, backend="xarray")
        assert res.shape == (array_shape[1], array_shape[2], 2 * n_breaks)

    @pytest.mark.parametrize(
        ("n_breaks", "start_date"),
        [(3, None), (4, None), (3, "2007-03-28")],
    )
    def test_pelt_dask(self, pelt_signal_xarray, n_breaks, start_date):
        array_shape = pelt_signal_xarray.shape
        res = pelt.pelt(pelt_signal_xarray, n_breaks, 1, start_date, backend="dask")
        assert res.shape == (2 * n_breaks, array_shape[1], array_shape[2])

    def test_pelt_model_error(self, pelt_signal_xarray):
        with pytest.raises(
            ValueError, match="Only rbf is accepted as kernel model for KernelCPD"
        ):
            pelt.pelt(pelt_signal_xarray, 5, 1, model="l1")

    def test_pelt_backend_error(self, pelt_signal_xarray):
        with pytest.raises(
            ValueError,
            match="Incorrect backend value. Only 'dask' and 'xarray' are accepted",
        ):
            pelt.pelt(pelt_signal_xarray, 5, 1, backend="other")
