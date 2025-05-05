#!/usr/bin/env python
import xarray as xr
import numpy as np

berkeley_ds = xr.open_dataset("berkeley_earth/Global_TAVG_Gridded_0p25deg.nc")

# Get all time intervals in the dataset that start with the most recent year.
most_recent_year = str(berkeley_ds.time[-1].values).split(".")[0]
year_month_intervals = [
    time for time in berkeley_ds.time.values if str(time).startswith(most_recent_year)
]

# Warn user and drop most recent year if it does not have 12 months.
if len(year_month_intervals) != 12:
    berkeley_ds = berkeley_ds.sel(
        time=berkeley_ds.time.values[
            ~np.isin(berkeley_ds.time.values, year_month_intervals)
        ]
    )
    print(
        f"Most recent year ({most_recent_year}) does not have 12 months. "
        f"Dropping {most_recent_year} from the Berkeley Earth dataset."
    )

years = range(1850, 2100 + 1)
models = [
    "Berkeley-Earth",
    "CESM2",
    "CNRM-CM6-1-HR",
    "EC-Earth3-Veg",
    "GFDL-ESM4",
    "HadGEM3-GC31-LL",
    "HadGEM3-GC31-MM",
    "KACE-1-0-G",
    "MIROC6",
    "MPI-ESM1-2-HR",
    "MRI-ESM2-0",
    "NorESM2-MM",
    "TaiESM1",
]
scenarios = ["historical", "ssp126", "ssp245", "ssp370", "ssp585"]

# Open example CMIP6 file to get minimum latitude.
cmip6_ds = xr.open_dataset("cmip6/tas_CESM2_historical_mon.nc")
min_lat = cmip6_ds.lat.min().values

# Crop the berkeley_ds to the same latitude as CMIP6 data.
berkeley_ds = berkeley_ds.sel(latitude=slice(min_lat, None))

# Use resolution of cropped berkeley_ds for combined dataset.
latitude = berkeley_ds.latitude.data
longitude = berkeley_ds.longitude.data

baseline_data = np.full(
    (len(models), len(latitude), len(longitude)),
    -9999.0,
    dtype=np.float32,
)

anomaly_data = np.full(
    (len(models), len(scenarios), len(years), len(latitude), len(longitude)),
    -9999.0,
    dtype=np.float32,
)

combined_ds = xr.Dataset(
    {
        "baseline": (
            [
                "model",
                "latitude",
                "longitude",
            ],
            baseline_data,
        ),
        "anomaly": (
            [
                "model",
                "scenario",
                "year",
                "latitude",
                "longitude",
            ],
            anomaly_data,
        ),
    },
    coords={
        "model": models,
        "scenario": scenarios,
        "year": years,
        "latitude": latitude,
        "longitude": longitude,
    },
)

berkeley_baseline = berkeley_ds.climatology.mean(dim="month_number")
combined_ds["baseline"].loc[dict(model="Berkeley-Earth")] = berkeley_baseline

for year in years:
    year_month_intervals = [
        time for time in berkeley_ds.time.values if f"{year}." in str(time)
    ]
    monthly_values = berkeley_ds.sel(time=year_month_intervals)
    combined_ds["anomaly"].loc[
        dict(year=year, model="Berkeley-Earth", scenario="historical")
    ] = monthly_values.temperature.mean(dim="time")

combined_ds["baseline"].attrs["units"] = "1951-1980 baseline (°C)"
combined_ds["anomaly"].attrs["units"] = "Delta from 1951-1980 baseline (°C)"

for model in models[1:]:
    historical_cmip6_file = f"cmip6/tas_{model}_historical_mon.nc"
    historical_cmip6_ds = xr.open_dataset(historical_cmip6_file)
    historical_cmip6_ds = historical_cmip6_ds.transpose("time", "lat", "lon")
    cmip6_baseline = historical_cmip6_ds.sel(
        time=slice("1951-01-01", "1980-12-31")
    ).mean(dim="time")
    historical_cmip6_ds.close()

    # Regrid cmip6_baseline to match resolution of combined_ds.
    cmip6_baseline_regridded = cmip6_baseline.interp(
        lat=latitude, lon=longitude, method="nearest"
    )

    # Rename lat/lon to latitude/longitude to match combined_ds.
    cmip6_baseline_regridded = cmip6_baseline_regridded.rename(
        {"lat": "latitude", "lon": "longitude"}
    )

    combined_ds["baseline"].loc[dict(model=model)] = (
        cmip6_baseline_regridded.to_array().squeeze()
    )

    for scenario in scenarios[1:]:
        projected_cmip6_file = f"cmip6/tas_{model}_{scenario}_mon.nc"

        # Ignore files that do not exist and and keep these invalid
        # model/scenario combinations filled in with -9999.0.
        try:
            projected_cmip6_ds = xr.open_dataset(projected_cmip6_file)
        except:
            continue

        # Transpose dimensions to match the combined_ds.
        projected_cmip6_ds = projected_cmip6_ds.transpose("time", "lat", "lon")

        for year in range(2025, 2100 + 1):
            monthly_values = projected_cmip6_ds.sel(
                time=slice(f"{year}-01-01", f"{year}-12-31")
            )
            annual_means = monthly_values.mean(dim="time")
            anomalies = annual_means - cmip6_baseline

            # Regrid anomalies to match resolution of combined_ds.
            anomalies_regridded = anomalies.interp(
                lat=latitude, lon=longitude, method="nearest"
            )

            anomalies_regridded = xr.DataArray(
                anomalies_regridded.data,
                dims=["lat", "lon"],
                coords={"lat": latitude, "lon": longitude},
            )

            combined_ds["anomaly"].loc[
                dict(year=year, model=model, scenario=scenario)
            ] = anomalies_regridded

        projected_cmip6_ds.close()

# Transpose latitude/longitude dimensions for Rasdaman WMS compatibility.
combined_ds = combined_ds.transpose(
    "model", "scenario", "year", "longitude", "latitude"
)

# Sort latitude from high to low for Rasdaman compatibility.
combined_ds = combined_ds.sortby(combined_ds.latitude, ascending=False)

combined_ds.to_netcdf(
    "temperature_anomalies.nc", mode="w", encoding={"anomaly": {"_FillValue": -9999.0}}
)
