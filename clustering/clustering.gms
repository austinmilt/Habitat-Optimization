

* DECLARE DATA
sets
    Targets 'targets for clustering' / fish1, fish2, fish3, fish4, fish5 /,
    Units 'units where targets are found' / shed1, shed2, shed3, shed4, shed5, shed6, shed7, shed8, shed9, shed10 /,
    Clusters 'possible clusters up to the number of targets' / 1*1000 /;

alias
    (Targets, T),
    (Units, U),
    (Clusters, C);

parameters
    performance(Targets) 'performance (e.g. swim speed) of targets' / fish1=1.0, fish2=1.0, fish3=2.0, fish4=2.0, fish5=2.0 /,
    distribution(Targets, Units) 'distribution of targets across units' /
        fish1.shed1=1, fish1.shed2=1, fish1.shed3=1, fish1.shed4=1, fish1.shed5=1,
        fish2.shed1=1, fish2.shed2=1, fish2.shed3=1, fish2.shed4=1, fish2.shed5=1,
        fish3.shed6=1, fish3.shed7=1, fish3.shed8=1, fish3.shed9=1, fish3.shed10=1,
        fish4.shed6=1, fish4.shed7=1, fish4.shed8=1, fish4.shed9=1, fish4.shed10=1,
        fish5.shed6=1, fish5.shed7=1, fish5.shed8=1, fish5.shed9=1, fish5.shed10=1/;

scalars
    weightPerformance 'weight in the objective function on performance' / 1.0 /,
    weightDistribution 'weight in the objective function on distribution' / 1.0 /,
    weightCluster 'weight in the objective function on number of clusters' / 1.0 /;



* DECLARE VARIABLES
parameter nT; nT = card(T);
parameter nU; nU = card(U);
integer variable N 'number of clusters';
binary variable x(Clusters, Units) 'whether each unit is included in a cluster';
binary variable y(Clusters, Targets) 'whether each target is included in a cluster';
free variable p(Clusters) 'performance (e.g. swim speed) chosen for each cluster';
free variable pError(Clusters) 'performance error';
free variable dError(Clusters) 'distribution error';
free variable objective 'objective value';
positive variable yByp(Clusters, Targets) 'yByp = y*p^2';
positive variable yBypp(Clusters, Targets) 'yBypp = y*(p(C)-performance)^2';
positive variable yByxx(Clusters, Targets, Units) 'yByxx = y*(1-distribution-x(C,U))^2';
positive variable yByp_By_yBypp(Clusters);



* DECLARE EQUATIONS
equations
eq_objective 'minimize difference in swim speeds, maximize overlap of distribution, minimize number of clusters',
eq_performance(Clusters) 'calculation of performance error',
eq_distribution(Clusters) 'calculateion of distribution error',
cn_y(Targets) 'ensure each target belongs to exactly one cluster',
cn_yByp_y(Clusters, Targets) 'constrain yByp to be <= y',
cn_yByp_p(Clusters, Targets) 'constrain yByp to be <= p^2',
cn_yBypp_y(Clusters, Targets) 'constrain yBypp to be <= y',
cn_yBypp_pp(Clusters, Targets) 'constrain yBypp to be <= (p(C)-performance)^2',
cn_yByxx_y(Clusters, Targets, Units) 'constrain yByxx to be <= y',
cn_yByxx_xx(Clusters, Targets, Units) 'constrain yByxx to be <= (1-distribution-x(C,U))^2',
cn_yByp_By_yBypp_yByp(Clusters),
cn_yByp_By_yBypp_yBypp(Clusters);



* DEFINE EQUATIONS
eq_objective..
    objective =e= sum(C$(ord(C) le N), weightPerformance*yByp_By_yBypp(C) - weightDistribution*dError(C)) + weightCluster*(N/nT);

eq_distribution(C)$(ord(C) le N)..
    dError(C) =e= (1 / (nU*nT)) * sum((T,U), yByxx(C,T,U));

cn_y(T)..
    sum(C$(ord(C) le N), y(C,T)) =e= 1;

cn_yByp_y(C,T)$(ord(C) le N)..
    yByp(C,T) =l= y(C,T);

cn_yByp_p(C,T)$(ord(C) le N)..
    yByp(C,T) =l= power(performance(T), 2);

cn_yBypp_y(C,T)$(ord(C) le N)..
    yBypp(C,T) =l= y(C,T);

cn_yBypp_pp(C,T)$(ord(C) le N)..
    yBypp(C,T) =l= power((performance(T) - p(C)), 2);

cn_yByp_By_yBypp_yByp(C)$(ord(C) le N)..
    yByp_By_yBypp(C) =l= 1 / sum(T, yByp(C,T));

cn_yByp_By_yBypp_yBypp(C)$(ord(C) le N)..
    yByp_By_yBypp(C) =l= sum(T, yBypp(C,T));

cn_yByxx_y(C,T,U)$(ord(C) le N)..
    yByxx(C,T,U) =l= y(C,T);

cn_yByxx_xx(C,T,U)$(ord(C) le N)..
    yByxx(C,T,U) =l= power((1 - distribution(T,U) - x(C,U)), 2);


model clustering /all/;


* ADDITIONAL CONSTRAINTS
N.up = sum(Targets, 1);
N.lo = 0;
p.up(C) = smax(T, performance(T));
p.lo(C) = smin(T, performance(T));


* SOLVE
solve clustering using mip min objective;
abort$(clustering.SolveStat = %SolveStat.UserInterrupt%) 'Job interrupted by user';


* DISPLAY
display y.l;
display x.l;
display p.l


