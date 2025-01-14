clear
close all

%% pierre's
A = readtable('GHOST_example.dat','VariableNamingRule','preserve')
data = table2array(A);
figure; plot(data)

%% time domain
B = readtable('time_test.dat');
data2 = table2array(B);
figure; plot(data2)
