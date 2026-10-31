import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


@pytest.mark.parametrize('years',[[2023],[2010,2023],[],[2022,2021],[2022,2022]])
def test_extension_rejects_invalid_years_before_file_access(tmp_path,years):
    from extend_2022 import load_prices
    with pytest.raises(ValueError):load_prices(years,cache=tmp_path/'absent',allow_2020_2022=True)


def test_extension_requires_explicit_opt_in(tmp_path):
    from extend_2022 import load_prices
    with pytest.raises(ValueError):load_prices([2020],cache=tmp_path/'absent',allow_2020_2022=False)


def test_extension_can_read_authorized_2022_without_other_years(tmp_path):
    from extend_2022 import load_prices
    base=int(np.datetime64('2022-01-01','m').astype(int))
    np.savez(tmp_path/'M1_2022.private.npz',base=base,bid=[100.,np.nan,101.],ask=[100.2,np.nan,101.2])
    mins,bid,ask=load_prices([2022],cache=tmp_path,allow_2020_2022=True)
    assert mins.tolist()==[base,base+2]
    np.testing.assert_allclose(bid,[100,101])
