"""Conditional interface arithmetic; unknown component gates remain unverified."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/interface_review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    spec=json.loads((OUT/'interface_spec.json').read_text(encoding='utf-8'));p=spec['pressure'];f=spec['flow'];power=spec['power_design_allowances_ma_not_measured'];r=spec['radio']
    pins=[v['pin'] for v in spec['pins']];assert len(pins)==len(set(pins))==17
    assert all(v['logic_v']==3.3 for v in spec['pins'])
    vmin=p['current_min_ma']/1000*p['shunt_ohm'];vmax=p['current_max_ma']/1000*p['shunt_ohm'];heat=(p['current_max_ma']/1000)**2*p['shunt_ohm']
    assert vmax<p['adc_vdd'] and heat<p['shunt_power_rating_w_candidate']
    bad22=.022*p['shunt_ohm'];assert math.isclose(bad22,p['adc_vdd'])
    i3=sum(power[x] for x in ['mcu_3v3','sd_3v3','adc_buffer_3v3','other_3v3']);i5=power['radio_5v']+power['flow_5v']+i3*3.3/(5*power['buck_efficiency_assumption'])
    assert i3*power['design_reserve_factor']<=power['node_3v3_rating_candidate_ma'] and i5*power['design_reserve_factor']<=power['node_5v_rating_candidate_ma']
    budget=spec['budget_caps_cny_not_quotes'];assert sum(budget.values())==2000;other=sum(budget.values())-budget['two_pressure_transmitters']
    paired_conversion_ms=2000/p['adc_data_rate_sps_candidate'];press_mid_skew_ms=1000/p['adc_data_rate_sps_candidate']
    result={'date':'2026-10-04','status':'conditional_arithmetic_passed_build_and_procurement_unverified','physical_data':False,'pin_assignment_count':17,'pin_conflicts':[],'normal_shunt_v':[vmin,vmax],'normal_shunt_dissipation_w':heat,'shunt_power_factor_at_normal_current':p['shunt_power_rating_w_candidate']/heat,'fault_22ma_shunt_v':bad22,'fault_22ma_at_adc_supply_rail_requires_protection':True,'adc_lsb_pressure_kpa':(2*p['adc_pga_v']/65536)/((vmax-vmin)/p['range_kpa']),'two_conversion_nominal_ms_excluding_bus_and_oscillator':paired_conversion_ms,'p0_p1_nominal_midpoint_skew_ms':press_mid_skew_ms,'flow_max_pulse_hz':f['range_l_min'][1]*f['pulses_per_litre']/60,'flow_min_pulses_per_10s':f['range_l_min'][0]*f['pulses_per_litre']*f['counter_window_s']/60,'flow_10s_step_l_min':60/(f['pulses_per_litre']*f['counter_window_s']),'node_3v3_allowance_ma':i3,'node_5v_equivalent_allowance_ma':i5,'node_3v3_with_reserve_ma':i3*power['design_reserve_factor'],'node_5v_with_reserve_ma':i5*power['design_reserve_factor'],'budget_cap_cny':sum(budget.values()),'other_budget_cap_cny':other,'pressure_price_sensitivity':[{'hypothetical_unit_price_cny':price,'total_with_other_cap_cny':other+2*price,'within_2000':other+2*price<=2000} for price in [300,340,500,800]],'uart_one_event_ms':44*10/r['uart_baud']*1000,'uart_one_ack_ms':24*10/r['uart_baud']*1000,'event_fits_candidate_64b_subpacket':44<=r['packet_limit_bytes_candidate'],'unverified_gates':spec['release_gates'],'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),OUT/'interface_spec.json',ROOT/'simulation/diagnosis_review/protocol.json',ROOT/'simulation/hardware_results/summary.json']}}
    (OUT/'hardware_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print('17 unique pins; 0.6—3.0V normal; 22mA reaches ADC rail; candidate supply allowance and conditional 2000CNY cap checked. Build gates remain open.')
if __name__=='__main__':main()
