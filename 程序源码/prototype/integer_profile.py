"""Shared numeric configuration, independent of review/test entry points."""
import numpy as np


def profile(monitor, reference):
    c = monitor.node.context
    if c is None:
        return dict(numeric=0, approved=int(monitor.approved), rapid_available=0,
                    r0=0, main=[0,0], rapid=[0,0], lut=[0]*381)
    pressures = np.arange(10,200.01,.5)
    values = c['gain']*reference['a_l_min']*(pressures/100)**reference['n_fitted']
    main = np.maximum([.06,.6],6*c['scale'])
    rapid = monitor.rapid.threshold
    return dict(numeric=1, approved=int(monitor.approved), rapid_available=int(rapid is not None),
                r0=round(c['r0']*1000000), main=[round(x*1000000) for x in main],
                rapid=[round(x*1000000) for x in rapid] if rapid is not None else [0,0],
                lut=[round(x*1000000) for x in values])


def config_command(c):
    return 'C '+' '.join(map(str,[c['numeric'],c['approved'],c['rapid_available'],c['r0'],
                                 *c['main'],*c['rapid'],*c['lut']]))
