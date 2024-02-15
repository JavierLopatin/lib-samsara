import xarray as xr
from datacube.utils import masking
# from pathlib import Path
from datacube.utils.cog import write_cog
import numpy as np
from odc.algo import to_f32, mask_cleanup

def write_to_cogs(img, dim=None, **kwargs):    
    if kwargs.get("overwrite") is None:
        kwargs["overwrite"] = True
    if kwargs.get("nodata") is None:
        kwargs["nodata"] = np.nan           
    if dim is None:
        write_cog(img, **kwargs)
    else:
        fname = kwargs["fname"]
        for i in img[dim].values:
            kwargs["fname"] = f"{fname}_dim-{dim}-{i}.tif"
            write_cog(img.sel({dim: i}), **kwargs)

            
def mask_and_calculate_ndvi(ds):
    reflectance_bands = ["red", "nir08"]
    quality_band = 'qa_pixel'
    good_pixel_flags = {
        "snow": "not_high_confidence",
        "cloud": "not_high_confidence",
        #"cirrus": "not_high_confidence",
        "cloud_shadow": "not_high_confidence",
        "nodata": False
    }

    cloud_free_mask = masking.make_mask(ds[quality_band], **good_pixel_flags)
    # Apply morphological processing on cloud mask
    # See: https://docs.digitalearthafrica.org/en/latest/sandbox/notebooks/Frequently_used_code/Cloud_and_pixel_quality_masking.html#Applying-morphological-processing-on-the-cloud-mask and https://docs.dea.ga.gov.au/notebooks/How_to_guides/Using_load_ard/
    filters = [("opening", 2),("dilation", 2)]
    cloud_free_mask = mask_cleanup(cloud_free_mask, mask_filters=filters)

    # Should morphological processing be applied to this mask as well?
    cloud_medium_conf_mask = masking.make_mask(ds[quality_band], cloud_confidence="medium")
    
    cloud_masks = cloud_free_mask + cloud_medium_conf_mask
    
    masked = ds[reflectance_bands].where(cloud_masks)
    masked = to_f32(masked, scale=0.0000275, offset=-0.2)
    ndvi = (masked.nir08 - masked.red) / (masked.nir08  + masked.red )
    ndvi = ndvi.where((ndvi > -1) & (ndvi < 1))
    ndvi.attrs = ds.attrs

    return ndvi

def xr_transform(xarray, levels, dtype = None):
    # Esta función reduce la resolución radiométrica de la imagen
    xr = xarray.copy()
    if dtype is None:
        dtype = xarray.dtype
    min = np.nanmin(xr.data)
    max = np.nanmax(xr.data)
    zi = (xr - min) / (max - min)
    li = (zi*(levels - 1))
    if xr.isnull().any().data == True:
         li = np.nan_to_num(li + 1)
    xr.data = li.round().astype(dtype)
    return(xr)


##---- Outputs para CSIRO

# def transform_breaks(stack, magnitudes, dates, ref_year=2016):
#     # TODO: modificar para cuando lleguen los datos con la fecha unix
#     ds2 = stack.where(stack.time.dt.year >= ref_year, drop=True)
#     bksi = (dates * 1000).round()
    
#     bks_ = xr.DataArray(np.nan, ds2.coords, ds2.dims)
#     bks_.attrs = ds2.attrs
    
#     times = ds2.time
#     timey = ((times.dt.year + (times.dt.dayofyear - 1) / 365) * 1000).round()
    
#     for i, t in enumerate(timey):
#         bks_[i, :, :] = xr.where(bksi.round(3) == t, magnitudes, np.nan)
        
#     return bks_


# def export_results(df, outpath="outs/reshape_test", filename="break00"):
#     for i, t in enumerate(df.time.dt.strftime("%Y-%m-%d").values):
#         mpath = Path(outpath) / t.replace("-", "")
#         mpath.mkdir(parents=True, exist_ok=True)
#         write_cog(df.isel(time=i), fname=mpath / f"{t}_{filename}.tif", nodata=np.nan, overwrite=True)