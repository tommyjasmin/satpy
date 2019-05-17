#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Satpy developers
#
#
# This file is part of Satpy.
#
# Satpy is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Satpy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Satpy.  If not, see <http://www.gnu.org/licenses/>.

"""Vaisala Global Lightning Dataset 360 reader

Vaisala Global Lightning Dataset GLD360 is data as a service
that provides real-time lightning data for accurate and early
detection and tracking of severe weather. The data provided is
generated by a Vaisala owned and operated world-wide lightning
detection sensor network.

References:
- [GLD360] https://www.vaisala.com/en/products/data-subscriptions-and-reports/data-sets/gld360

"""

import logging
import pandas as pd
import dask.array as da
import xarray as xr

from satpy import CHUNK_SIZE
from satpy.readers.file_handlers import BaseFileHandler

logger = logging.getLogger(__name__)


class VaisalaGLD360TextFileHandler(BaseFileHandler):
    """ASCII reader for Vaisala GDL360 data."""

    def __init__(self, filename, filename_info, filetype_info):
        super(VaisalaGLD360TextFileHandler, self).__init__(filename, filename_info, filetype_info)

        names = ['date', 'time', 'latitude', 'longitude', 'power', 'unit']
        types = ['str', 'str', 'float', 'float', 'float', 'str']
        dtypes = dict(zip(names, types))
        # Combine 'date' and 'time' into a datetime object
        parse_dates = {'datetime': ['date', 'time']}

        self.data = pd.read_csv(filename, delim_whitespace=True, header=None,
                                names=names, dtype=dtypes, parse_dates=parse_dates)

    @property
    def start_time(self):
        return self.data['datetime'].iloc[0]

    @property
    def end_time(self):
        return self.data['datetime'].iloc[-1]

    def get_dataset(self, dataset_id, dataset_info):
        """Load a dataset."""
        xarr = xr.DataArray(da.from_array(self.data[dataset_id.name],
                                          chunks=CHUNK_SIZE), dims=["y"])

        # Add time, longitude, and latitude as non-dimensional y-coordinates
        xarr['time'] = ('y', self.data['datetime'])
        xarr['longitude'] = ('y', self.data['longitude'])
        xarr['latitude'] = ('y', self.data['latitude'])

        if dataset_id.name == 'power':
            # Check that units in the file match the unit specified in the 
            # reader yaml-file
            if not (self.data.unit == dataset_info['units']).all():
                raise ValueError('Inconsistent units found in file!')
        xarr.attrs.update(dataset_info)

        return xarr
