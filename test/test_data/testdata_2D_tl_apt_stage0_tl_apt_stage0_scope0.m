% scope metadata file version 0.3 March 2016
function scp=PsBead10um06_1_tl_apt_stage0_tl_apt_stage0_scope0()
scp.version=0.3;
scp.hint=1e-08;
scp.hoff=-6.61e-05;
scp.vgain=[2.4977e-06];
scp.voff=[0.016999];
scp.points_per_trace=5000;
scp.n_traces=6480;
scp.n_channels=1;
scp.format=2;
scp.dataname='PsBead10um06_1_tl_apt_stage0_tl_apt_stage0_scope0.dat';
% next line: n_averages meaning depends on scope and the multitrace capability, -1 means not implemented
scp.n_averages=5000;
% next line: multitraces=1 means off, -1 means undefined or not implemented, >1 is the number of traces
scp.multitraces=1000;
scp.channels={'F1'};
