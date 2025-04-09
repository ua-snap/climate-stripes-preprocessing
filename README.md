# climate-stripes-preprocessing

## Setup

Download Berkeley Earth's "Global Monthly Land + Ocean, Average Temperature with Air Temperatures at Sea Ice" dataset:

```bash
wget 'https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/Global/Gridded/Land_and_Ocean_LatLong1.nc'
```

## Run

```bash
python annual_means.py
```

This will produce a `combined_anomalies.nc` NetCDF file full of the annual means of temperature anomalies.