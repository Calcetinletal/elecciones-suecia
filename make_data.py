"""Run the audited 2022 offline pipeline, using immutable cached originals."""
from pathlib import Path
import argparse,subprocess,sys
ROOT=Path(__file__).resolve().parent
STEPS=['download_election_2022.py','download_boundaries_2022.py','download_demography.py','normalize_data.py','build_crosswalk.py','build_dataset.py','simplify_geometries.py','verify_sample.py','validate_data.py','build_provenance.py','build_cartogram_geography.py']
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--from-step',choices=STEPS,help='Resume after a failed step, using existing processed prerequisites');args=parser.parse_args()
    start=STEPS.index(args.from_step) if args.from_step else 0
    for step in STEPS[start:]:
        print('\nRunning '+step,flush=True)
        subprocess.run([sys.executable,str(ROOT/'scripts'/step)],cwd=ROOT,check=True)
if __name__=='__main__':main()
