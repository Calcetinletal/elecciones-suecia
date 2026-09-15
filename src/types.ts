import type { FeatureCollection, Geometry } from 'geojson';
export interface District {
 district_id:string;district_name:string;municipality_code:string;municipality_name:string;county_code:string;county_name:string;
 population:number|null;eligible_voters:number|null;valid_votes:number|null;ballots_cast:number|null;turnout_pct:number|null;
 foreign_background_pct:number|null;foreign_born_pct:number|null;foreign_citizens_pct:number|null;
 higher_education_pct:number|null;employment_pct:number|null;median_income:number|null;
 winning_party:string|null;winning_party_pct:number|null;winning_party_tie:boolean;
 demography_method:string;demography_year:number;geometry_year:number;demography_geometry_year:number;employment_year:number;
 demography_coverage:number;demography_data_coverage:number;dominant_overlap_share:number;source_allocation_coverage:number;coverage_quality:string;
 [key:string]:string|number|boolean|null;
}
export type GeoData=FeatureCollection<Geometry,{district_id:string;[key:string]:unknown}>;
export interface YearEntry {year:number;status:string;district_count:number;table?:string;geometry?:string;downloaded_at?:string;source_updated_at?:string;reported_district_count?:number;pending_district_count?:number;}
export interface Manifest {schema_version:number;years:YearEntry[];}
export type View='electoral'|'demography'|'bivariate'|'dominant'|'compare';
export interface State {year:number;view:View;metric:string;electionMetric:string;party:string;county:string;municipality:string;district:string;band:string;weight:string;locale:string;quality:string;size:string;analysisY:string;lng:number;lat:number;zoom:number;}
