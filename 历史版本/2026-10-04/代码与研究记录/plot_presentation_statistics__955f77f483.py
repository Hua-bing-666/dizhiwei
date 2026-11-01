"""Print-safe variant of the frozen count plot; values/intervals unchanged."""
from pathlib import Path
import hashlib,json
import plot_diagnosis_review as plots
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures/presentation_review'
plots.OUT=OUT;plots.records=[]
original_save=plots.save

def print_save(fig,name,question,series=(),annotations=()):
    assert name=='noise_outcomes'
    for ax in fig.axes:
        assert len(ax.patches)==8
        for i,patch in enumerate(ax.patches):
            patch.set_edgecolor('#25363b');patch.set_linewidth(.55)
            if i>=4:patch.set_hatch('///')
    legend=fig.legends[0]
    legend.legend_handles[0].set_edgecolor('#25363b')
    legend.legend_handles[1].set_hatch('///');legend.legend_handles[1].set_edgecolor('#25363b')
    original_save(fig,'noise_outcomes_print',question,series,annotations)

if __name__=='__main__':
    plots.save=print_save;plots.outcomes()
    source=[Path(__file__),ROOT/'scripts/plot_diagnosis_review.py',ROOT/'simulation/diagnosis_review/summary.json',ROOT/'application/figures/diagnosis_review/figure_provenance.json']
    data={'classification':'print_variant_same_frozen_simulation_counts_and_intervals','physical_data':False,'style_change':'Q comparator hatched bars and matching legend; no values or intervals changed','figures':plots.records,'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source}}
    (OUT/'statistics_provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
