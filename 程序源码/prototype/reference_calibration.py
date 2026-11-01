"""Host-only candidate reference fit; never silently approve a healthy node."""
import csv,io,math
import numpy as np
def fit_reference(text):
    if not isinstance(text,str) or len(text)>12000:raise ValueError('标定 CSV 过长或格式错误')
    reader=csv.DictReader(io.StringIO(text.strip()))
    columns=['p0_kpa','p1_kpa','q_l_min']
    if not reader.fieldnames or any(k not in reader.fieldnames for k in columns):raise ValueError('表头须包含 p0_kpa,p1_kpa,q_l_min')
    try:rows=np.asarray([[float(row[k]) for k in columns] for row in reader],dtype=float)
    except (TypeError,ValueError,KeyError):raise ValueError('标定数据须为数值，缺测不能用于参照拟合') from None
    if rows.ndim!=2 or not 9<=len(rows)<=200:raise ValueError('需要 9—200 组独立健康标定记录')
    if not np.isfinite(rows).all():raise ValueError('不能使用 NaN 或无穷标定')
    p0,p1,q=rows.T
    if not ((p0>=p1)&(p0<=200)&(p1>=10)&(q>.5)&(q<=50)).all():raise ValueError('标定须满足 200≥P0≥P1≥10 kPa，0.5<Q≤50 L/min')
    if np.ptp(p1)<20 or len(set(np.round(p1/5)))<3:raise ValueError('下游压力跨度至少 20 kPa，覆盖至少三个 5 kPa 压力档')
    x=np.log(p1/100);y=np.log(q);design=np.column_stack([np.ones(len(x)),x]);coef=np.linalg.lstsq(design,y,rcond=None)[0]
    a=float(np.exp(coef[0]));n=float(coef[1])
    if not -.05<=n<=1.2:raise ValueError('拟合指数超出本工具核查范围，请检查标定工况与数据')
    predicted=a*(p1/100)**n;residual=q/predicted-1
    resistance=(p0-p1)/q**2;r0=float(np.median(resistance))
    def mad(v):return float(1.4826*np.median(abs(v-np.median(v))))
    main=[max(.06,6*mad(residual)),max(.6,6*mad(resistance-r0))]
    lut=[round(float(a*(p/100)**n)*1e6) for p in np.arange(10,200.01,.5)]
    return dict(classification='candidate_reference_not_approved',physical_verified=False,
                points=len(rows),observed_p1_range_kpa=[float(p1.min()),float(p1.max())],
                a_l_min=a,n_fitted=n,r0=r0,relative_rmse=float(np.sqrt(np.mean(residual**2))),
                validation='in_sample_fit_only_not_independent_validation',
                profile=dict(numeric=1,approved=0,rapid_available=0,r0=round(r0*1e6),main=[round(v*1e6) for v in main],rapid=[0,0],lut=lut),
                note='拟合只生成候选配置，不切换运行参照。需独立确认健康状态、测试未参与拟合的工况，并另行标定短窗。')
