/* Portable host-verified core. No HAL, ISR, SD/Flash queue or valve control. */
#include "integer_diagnosis.h"
#include <string.h>
#include <limits.h>
_Static_assert(sizeof(uint32_t)==4 && sizeof(int64_t)==8, "fixed widths required");
_Static_assert(sizeof(CandidateStorage) <= 8192, "candidate slots exceed 8 KiB");
static uint32_t round_even(uint64_t num, uint32_t den) {
    uint64_t q=num/den, r=num%den;
    return (uint32_t)(q + (2*r>den || (2*r==den && (q&1))));
}
int diag_init(DiagState *s, const DiagConfig *c) {
    unsigned i;
    if (!s || !c || c->numeric>1 || c->approved>1 || c->rapid_available>1) return 0;
    if (c->rapid_available && !c->numeric) return 0;
    if (c->numeric) {
        if (c->main_leak_micro>8000000u || c->rapid_leak_micro>8000000u ||
            c->main_restriction_micro>1000000000u || c->rapid_restriction_micro>1000000000u ||
            c->r0_micro < -1000000000 || c->r0_micro > 1000000000 ||
            (int64_t)c->r0_micro+c->main_restriction_micro > 1000000000LL ||
            (int64_t)c->r0_micro+c->rapid_restriction_micro > 1000000000LL) return 0;
        for (i=0;i<DIAG_POINTS;i++) {
            if (!c->predicted_micro[i] || c->predicted_micro[i]>50000000u ||
                (i && c->predicted_micro[i]<c->predicted_micro[i-1])) return 0;
        }
    }
    memset(s,0,sizeof(*s)); s->config=c;s->last_status=255;return 1;
}
uint32_t diag_predict(const DiagConfig *c,int32_t p1_sum,uint32_t n) {
    uint32_t offset=(uint32_t)(p1_sum-1000*(int32_t)n),den=50*n;
    uint32_t i=offset/den,rem=offset%den;
    if (i>=DIAG_POINTS-1) return c->predicted_micro[DIAG_POINTS-1];
    return round_even((uint64_t)c->predicted_micro[i]*(den-rem)+
                      (uint64_t)c->predicted_micro[i+1]*rem,den);
}
uint8_t diag_flags(const DiagConfig *c,int32_t p0_sum,int32_t p1_sum,
                   uint32_t d,uint32_t n,int rapid) {
    uint32_t pred=diag_predict(c,p1_sum,n);
    uint32_t leak=rapid?c->rapid_leak_micro:c->main_leak_micro;
    uint32_t restriction=rapid?c->rapid_restriction_micro:c->main_restriction_micro;
    int64_t l=(int64_t)d*1000000000000LL-(int64_t)9*n*pred*(1000000LL+leak);
    int64_t r=(int64_t)(p0_sum-p1_sum)*81*n*1000000LL-
              (int64_t)100*d*d*((int64_t)c->r0_micro+restriction);
    return (uint8_t)((l>0) + 2*(r>0));
}
static const DiagSample *back(const DiagState *s,unsigned k) {
    return &s->ring[((unsigned)s->head+10u-k)%11u];
}
static int window(const DiagState *s,unsigned n,int32_t *sum0,int32_t *sum1,uint32_t *delta) {
    unsigned k;const DiagSample *last=back(s,0);
    *sum0=*sum1=0;*delta=0;
    if (s->size<n+1) return 0;
    for(k=0;k<n;k++) {
        const DiagSample *p=back(s,k),*prev=back(s,k+1);
        if(p->issue || p->p1<=1000 || p->count<prev->count) return 0;
        *sum0+=p->p0;*sum1+=p->p1;
    }
    *delta=last->count-back(s,n)->count;
    return 2*(*delta)>9*n;
}
int diag_update(DiagState *s,uint32_t t,uint32_t count,int32_t p0,int32_t p1,uint8_t issue,DiagOutput *o) {
    int32_t a,b;uint32_t d;int main_valid,rapid_valid,pressure_ok,ready,counter_ready;
    uint8_t label=0,positive=0,reason=0,status;
    if (!s || !s->config || !o || issue>3 || t>=4294967u ||
        (!s->started && t!=0) || (s->started && t!=s->last_t+1)) return 0;
    if (issue==0 && (p0<0 || p0>20000 || p1<0 || p1>20000)) return 0;
    if (s->started && count>=s->last_count && count-s->last_count>DIAG_MAX_DELTA) return 0;
    if (!s->started && count>DIAG_MAX_DELTA) return 0;
    memset(o,0,sizeof(*o));o->main_label=-1;o->flow_milli=DIAG_MISSING;
    if (s->started && count<s->last_count) {s->counter_run=0;s->pressure_run=0;reason=3;}
    if(s->counter_run<11) s->counter_run++;
    pressure_ok=issue==0;
    if(pressure_ok) {if(s->pressure_run<10) s->pressure_run++;}
    else {s->pressure_run=0;reason=issue==1?1:issue==2?2:4;}
    s->ring[s->head]=(DiagSample){count,p0,p1,issue};s->head=(uint8_t)((s->head+1u)%11u);
    if(s->size<11) s->size++;
    s->started=1;s->last_t=t;s->last_count=count;
    ready=s->pressure_run>=10;counter_ready=s->counter_run>=11;
    if(counter_ready) {
        d=count-back(s,10)->count;o->flow_milli=(int32_t)round_even((uint64_t)d*1000,90);
    }
    if(t<130) {o->status=4;o->pattern=4;return 1;}
    main_valid=ready && counter_ready && window(s,10,&a,&b,&d) && s->config->numeric;
    status=main_valid?0:!s->config->numeric?2:!pressure_ok?3:(!ready || !counter_ready)?4:5;
    if(main_valid) label=diag_flags(s->config,a,b,d,10,0);
    if(!main_valid || !label) {s->pending=0;s->confirmed=0;s->active=0;}
    else if(label!=s->pending) {s->pending=label;s->confirmed=1;}
    else if(s->confirmed<5) s->confirmed++;
    if(main_valid && label && s->confirmed>=5 && s->active!=label) {
        s->active=label;
        if(s->config->approved) o->event_mask|=(uint8_t)(1u<<(label==1?4:label==2?5:6));
    }
    rapid_valid=s->config->numeric && s->config->rapid_available && window(s,3,&a,&b,&d);
    if(rapid_valid) positive=diag_flags(s->config,a,b,d,3,1)!=0;
    if(!positive) {s->rapid_pending=0;s->rapid_active=0;}
    else if(s->rapid_pending<2) s->rapid_pending++;
    if(s->rapid_pending>=2 && !s->rapid_active) {
        s->rapid_active=1;if(s->config->approved) o->event_mask|=1u<<3;
    }
    o->status=s->config->approved?status:1;
    o->pattern=o->status?4:(s->pending==s->active && s->confirmed>=5?s->active:0);
    o->main_label=main_valid?(int8_t)label:-1;
    o->rapid_valid=(uint8_t)(rapid_valid && s->config->approved);
    o->rapid_active=(uint8_t)(o->rapid_valid && s->rapid_active);
    o->rapid_positive=(uint8_t)(positive && s->config->approved);
    if(o->status!=s->last_status) {o->event_mask|=1u<<1;s->last_status=o->status;}
    if(reason && s->config->approved && s->config->numeric) {
        o->event_mask|=1u<<2;o->quality_reason=reason;
    }
    return 1;
}
#ifdef BUILD_HARNESS
#include <stdio.h>
#include <inttypes.h>
int main(void) {
    DiagConfig c;DiagState s;DiagOutput o;char op;unsigned numeric,approved,rapid;
    uint32_t t,count,n,d;int32_t a,b;unsigned issue,i;int is_rapid;
    memset(&c,0,sizeof(c));memset(&s,0,sizeof(s));
    while(scanf(" %c",&op)==1) {
        if(op=='M') {printf("%zu %zu %zu %zu\n",sizeof(DiagState),sizeof(DiagConfig),sizeof(CandidateSlot),sizeof(CandidateStorage));}
        else if(op=='C') {
            if(scanf("%u %u %u %"SCNd32" %"SCNu32" %"SCNu32" %"SCNu32" %"SCNu32,
                     &numeric,&approved,&rapid,&c.r0_micro,&c.main_leak_micro,&c.main_restriction_micro,&c.rapid_leak_micro,&c.rapid_restriction_micro)!=8) return 2;
            c.numeric=(uint8_t)numeric;c.approved=(uint8_t)approved;c.rapid_available=(uint8_t)rapid;
            for(i=0;i<DIAG_POINTS;i++) if(scanf("%"SCNu32,&c.predicted_micro[i])!=1) return 2;
            printf("%s\n",diag_init(&s,&c)?"OK":"ERR");
        } else if(op=='U') {
            if(scanf("%"SCNu32" %"SCNu32" %"SCNd32" %"SCNd32" %u",&t,&count,&a,&b,&issue)!=5) return 2;
            if(issue>3 || !diag_update(&s,t,count,a,b,(uint8_t)issue,&o)) puts("ERR");
            else printf("%u %u %u %u %u %d %u %u %"PRId32"\n",o.status,o.pattern,o.rapid_valid,o.rapid_active,o.rapid_positive,o.main_label,o.event_mask,o.quality_reason,o.flow_milli);
        } else if(op=='F') {
            if(scanf("%"SCNd32" %"SCNd32" %"SCNu32" %"SCNu32" %d",&a,&b,&d,&n,&is_rapid)!=5) return 2;
            if(!c.numeric || (n!=3 && n!=10) || b<1000*(int32_t)n || b>20000*(int32_t)n || a<0 || a>20000*(int32_t)n || d>450*n) puts("ERR");
            else printf("%u\n",diag_flags(&c,a,b,d,n,is_rapid));
        } else return 2;
    }
    return 0;
}
#endif
