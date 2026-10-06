/* Host bridge for rejected counter endpoints. Frozen core stays unchanged. */
#include "integer_diagnosis.h"
#include <stdio.h>
#include <inttypes.h>
#include <string.h>
int main(void) {
    DiagState state;DiagConfig cfg;DiagOutput out;
    char op;unsigned numeric,approved,rapid,issue,trusted,i;
    uint32_t t,count;int32_t p0,p1;uint8_t previous;
    memset(&state,0,sizeof(state));memset(&cfg,0,sizeof(cfg));
    while(scanf(" %c",&op)==1) {
        if(op=='C') {
            if(scanf("%u %u %u %"SCNd32" %"SCNu32" %"SCNu32" %"SCNu32" %"SCNu32,
                     &numeric,&approved,&rapid,&cfg.r0_micro,&cfg.main_leak_micro,&cfg.main_restriction_micro,&cfg.rapid_leak_micro,&cfg.rapid_restriction_micro)!=8) return 2;
            if(numeric>1 || approved>1 || rapid>1) return 2;
            cfg.numeric=(uint8_t)numeric;cfg.approved=(uint8_t)approved;cfg.rapid_available=(uint8_t)rapid;
            for(i=0;i<DIAG_POINTS;i++) if(scanf("%"SCNu32,&cfg.predicted_micro[i])!=1) return 2;
            puts(diag_init(&state,&cfg)?"OK":"ERR");
        } else if(op=='U') {
            if(scanf("%"SCNu32" %"SCNu32" %"SCNd32" %"SCNd32" %u %u",&t,&count,&p0,&p1,&issue,&trusted)!=6) return 2;
            previous=state.last_status;
            if(trusted>1 || issue>3) puts("ERR");
            else {
                if(!trusted) {count=state.last_count;issue=3;p0=p1=DIAG_MISSING;}
                if(!diag_update(&state,t,count,p0,p1,(uint8_t)issue,&out)) puts("ERR");
                else {
                    if(!trusted) {
                        /* The late endpoint cannot be a future interval start. */
                        state.size=0;state.counter_run=0;state.pressure_run=0;
                        out.flow_milli=DIAG_MISSING;
                    }
                    printf("%u %u %u %u %u %d %u %u %"PRId32" %u %"PRIu32"\n",
                           out.status,out.pattern,out.rapid_valid,out.rapid_active,out.rapid_positive,
                           out.main_label,out.event_mask,out.quality_reason,out.flow_milli,previous,count);
                }
            }
        } else return 2;
        fflush(stdout);
    }
    return 0;
}
