# climate-stripes-preprocessing

## Setup

### Berkeley Earth input data

Download Berkeley Earth's [0.25° x 0.25° High-Resolution Land and Ocean TAVG Gridded Data](https://berkeleyearth.org/high-resolution-data-access-page/) dataset. Authentication is required to access this dataset since it is currently in beta. Request access by [completing this form](https://docs.google.com/forms/d/e/1FAIpQLSf1gYL92ofpefzFN3v57keMP0dHZBcnK2tRiuNHJwK9m9sLjg/viewform). Place the downloaded Berkeley Earth dataset in `berkeley_earth/Global_TAVG_Gridded_0p25deg.nc`.

### CMIP6 input data

This script uses the same set of regridded CMIP6 NetCDF files that we use to ingest the `cmip6_monthly` Rasdaman coverage. Simply download the NetCDF files from Poseidon into a `cmip6` subdirectory like so:

```bash
scp -r poseidon.snap.uaf.edu:/workspace/Shared/Tech_Projects/rasdaman_production_datasets/cmip6_monthly cmip6
```

## Run

```bash
python calculate_and_combine.py
```

This will produce a `temperature_anomalies.nc` NetCDF file containing:

- The 1951-1980 mean temperature baseline used for Berkeley Earth temperature anomaly calculations.
- The 1951-1980 mean temperature baselines for each CMIP6 model, used to calculate their temperature anomalies.
- Annual mean temperature anomalies for the Berkeley Earth dataset from 1850 to near-present.
- Annual mean temperature anomalies for each CMIP6 model, with separate anomalies for each SSP provided by the model, from 2025-2100.

The `temperature_anomalies.nc` NetCDF file contains the data for both the `temperature_anomaly_baselines` and `temperature_anomaly_anomalies` coverages on Rasdaman.