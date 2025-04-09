#!/usr/bin/env python
import xarray as xr
import numpy as np

ds = xr.open_dataset("berkeley_earth/Land_and_Ocean_LatLong1.nc")

# Unused variables. Drop them to avoid unnecessary calculations.
ds = ds.drop_vars(["land_mask", "climatology"])

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

latitude = ds.latitude.data
longitude = ds.longitude.data
anomaly_data = np.zeros(
    (len(years), len(models), len(scenarios), len(latitude), len(longitude))
)

combined_ds = xr.Dataset(
    {
        "anomaly": (
            [
                "year",
                "model",
                "scenario",
                "latitude",
                "longitude",
            ],
            anomaly_data,
        )
    },
    coords={
        "year": years,
        "model": models,
        "scenario": scenarios,
        "latitude": latitude,
        "longitude": longitude,
    },
)

combined_ds["anomaly"].attrs["units"] = "Celsius delta from 1951-1980 baseline"

for year in years:
    year_month_intervals = [time for time in ds.time.values if f"{year}." in str(time)]
    annual_mean_anomaly = ds.sel(time=year_month_intervals)
    combined_ds["anomaly"].loc[
        dict(year=year, model="Berkeley-Earth", scenario="historical")
    ] = annual_mean_anomaly.temperature.mean(dim="time")


# Open example CMIP6 file to get grid information
cmip6_ds = xr.open_dataset("cmip6/tas_CESM2_historical_mon.nc")
lat = cmip6_ds.lat.data
lon = cmip6_ds.lon.data

combined_ds = combined_ds.sel(
    latitude=lat,
    longitude=lon,
    method="nearest",
)

for model in models[1:]:
    historical_cmip6_file = f"cmip6/tas_{model}_historical_mon.nc"
    historical_cmip6_ds = xr.open_dataset(historical_cmip6_file)
    historical_cmip6_ds = historical_cmip6_ds.transpose("time", "lat", "lon")
    historical_cmip6_baseline = historical_cmip6_ds.sel(
        time=slice("1950-01-01", "1980-12-31")
    ).mean(dim="time")
    historical_cmip6_ds.close()

    for scenario in scenarios[1:]:
        projected_cmip6_file = f"cmip6/tas_{model}_{scenario}_mon.nc"
        try:
            projected_cmip6_ds = xr.open_dataset(projected_cmip6_file)
        except:
            continue
        projected_cmip6_ds = projected_cmip6_ds.transpose("time", "lat", "lon")

        for year in range(2025, 2100 + 1):
            annual_mean = projected_cmip6_ds.sel(
                time=slice(f"{year}-01-01", f"{year}-12-31")
            )
            annual_mean = annual_mean.mean(dim="time")
            anomaly = annual_mean - historical_cmip6_baseline

            anomaly = xr.DataArray(
                anomaly.data,
                dims=["lat", "lon"],
                coords={"lat": lat, "lon": lon},
            )
            combined_ds["anomaly"].loc[
                dict(year=year, model=model, scenario=scenario)
            ] = anomaly

combined_ds.to_netcdf("combined_anomalies.nc", mode="w")
