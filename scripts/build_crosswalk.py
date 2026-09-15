"""Real polygon intersections, with population-grid mass; never centroid assignment."""
from common import *
import argparse
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely

def population_mass(polygons, grid):
    mass=np.zeros(len(polygons))
    for start in range(0,len(polygons),1000):
        part=polygons.geometry.iloc[start:start+1000]
        left,right=grid.sindex.query(part,predicate='intersects')
        if len(left):
            area=shapely.area(shapely.intersection(part.to_numpy()[left],grid.geometry.to_numpy()[right]))
            contribution=area*grid['density'].to_numpy()[right]
            mass[start:start+len(part)]=np.bincount(left,weights=contribution,minlength=len(part))
    return mass

def build(deso,districts,grid=None):
    for g in [deso,districts]:
        if g.crs is None: raise ValueError('CRS must be explicit')
    d=deso[['deso_id','geometry']].to_crs(3006).copy();v=districts[['district_id','geometry']].to_crs(3006).copy()
    d.geometry=d.geometry.make_valid();v.geometry=v.geometry.make_valid()
    d['source_area']=d.area
    pieces=gpd.overlay(d,v,how='intersection',keep_geom_type=True)
    pieces=pieces[pieces.area>1e-6].reset_index(drop=True)
    pieces['overlap_area']=pieces.area
    if grid is not None:
        grid=grid.to_crs(3006).copy()
        if (grid.population<0).any() or grid.population.isna().any(): raise ValueError('Invalid grid population')
        grid['density']=grid.population/grid.area
        print('Calculating grid mass for DeSO and intersections',flush=True)
        source_mass=pd.Series(population_mass(d,grid),index=d.deso_id)
        pieces['mass']=population_mass(pieces,grid)
        pieces['source_mass']=pieces.deso_id.map(source_mass)
        fallback=pieces.source_mass<=0
        pieces['weight']=np.where(fallback,pieces.overlap_area/pieces.source_area,pieces.mass/pieces.source_mass)
        pieces['method']=np.where(fallback,'areal_estimate','population_weighted_estimate')
    else:
        pieces['weight']=pieces.overlap_area/pieces.source_area;pieces['method']='areal_estimate'
    pieces['district_area']=pieces.district_id.map(pd.Series(v.area.to_numpy(),index=v.district_id))
    return pieces.drop(columns='geometry')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--areal',action='store_true',help='Explicitly use area weights instead of official 2022 grid');args=parser.parse_args()
    d=gpd.read_file(RAW/'scb/deso_2018.gpkg').rename(columns={'desokod':'deso_id'})
    v=gpd.read_parquet(PROCESSED/'boundaries_2022.parquet')
    grid=None if args.areal else gpd.read_file(RAW/'scb/grid_2022.gpkg',columns=['beftotalt']).rename(columns={'beftotalt':'population'})
    cw=build(d,v,grid)
    cw.to_parquet(PROCESSED/'crosswalk_2022.parquet',index=False)
    sums=cw.groupby('deso_id').weight.sum()
    write_json(PROCESSED/'crosswalk_quality.json',{'intersections':len(cw),'source_weight_min':float(sums.min()),'source_weight_max':float(sums.max()),'sources_below_99pct':sums[sums<.99].to_dict(),'sources_above_101pct':sums[sums>1.01].to_dict(),'fallback_intersections':int((cw.method=='areal_estimate').sum())})
    print('Crosswalk:',len(cw),'intersections. Source weight range',sums.min(),sums.max(),flush=True)
if __name__=='__main__': main()
