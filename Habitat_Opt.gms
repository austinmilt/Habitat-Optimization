$title Projects at Barriers for General Metrics (Fishworks v6)

* DEFINE COMMAND-LINE OPTIONS

* input gdx
$if not set inputfile $set inputfile 'data.gdx'


* SETS AND DEFINITIONS

sets
    Metrics(*) 'metrics of conservation goals to be achieved by taking actions at barriers',
    Barriers(*) 'points at which actions can be taken',
    Projects(*) 'projects that can be undertaken at barriers'
    Dummy(Barriers) 'dummy barrier to set totalPropEfficiency of downstream barriers of roots to 1';

alias (Barriers, J, K);

sets
    Downstream(J, K) 'barrier immediately downstream of another';

parameters
    weight(Metrics) 'objective weight of goal',
    metricMax(Metrics, Barriers) 'maximum possible contribution to goal at a barrier',
    basePropEfficiency(Metrics, Barriers) 'base level efficiency of goal contribution at barrier that propogates to upstream barriers',
    baseSingleEfficiency(Metrics, Barriers) 'base level efficiency of goal contribution at barrier that affects only the reach above the barrier',
    projPropEfficiency(Metrics, Barriers, Projects) 'efficiency increase of delivering a goal at a barrier by doing a project that is affected by and effects up/downstream efficiencies',
    projSingleEfficiency(Metrics, Barriers, Projects) 'efficiency increase of delivering a goal at a barrier that affects only the delivery at that barrier and not others',
    projectCost(Barriers, Projects) 'cost of successfully completing project at barrier',
    cap(Metrics) 'minimum (or maximum) allowable value of each metric';

scalars
    budget 'total budget for spending on all projects',
    epsilon 'epsilon value for equality tests' / 1e-6 /;


* LOAD MODEL DATA
$GDXIN %inputfile%
$load Projects, Barriers, Metrics, Downstream, weight, metricMax, Dummy
$load basePropEfficiency, projPropEfficiency, projectCost, cap, budget
$load projSingleEfficiency
$GDXIN


* DEFINE DUMMY BARRIER PARAMETERS
metricMax(Metrics, Barriers)$(Dummy(Barriers)) = 0;
basePropEfficiency(Metrics, Barriers)$(Dummy(Barriers)) = 1;
baseSingleEfficiency(Metrics, Barriers)$(Dummy(Barriers)) = 0;
projPropEfficiency(Metrics, Barriers, Projects)$(Dummy(Barriers)) = 0;
projSingleEfficiency(Metrics, Barriers, Projects)$(Dummy(Barriers)) = 0;
projectCost(Barriers, Projects)$(Dummy(Barriers)) = budget + 1;


* CHECK DATA REQUIREMENTS
parameter possibleEfficiency(Metrics, Barriers) 'total possible efficiency at a barrier for a goal';
parameter cntEffOOB 'number of Goal/Barrier pairs for which the total possible efficiency is outside [0, 1], which violates assumptions';
possibleEfficiency(Metrics, Barriers) = baseSingleEfficiency(Metrics, Barriers) + basePropEfficiency(Metrics, Barriers) + sum(Projects, projPropEfficiency(Metrics, Barriers, Projects)) + sum(Projects, projSingleEfficiency(Metrics, Barriers, Projects));
cntEffOOB = sum((Metrics, Barriers)$((possibleEfficiency(Metrics, Barriers) > (1 + epsilon)) or (possibleEfficiency(Metrics, Barriers) < (0 - epsilon))), 1);
if (cntEffOOB > 0, abort 'Total possible efficiency for a goal at a barrier must be in the closed interval [0, 1].');


* VARIABLE AND EQUATION DECLARATIONS

free variable
    objective 'total weighted value across all goals',
    value(Metrics) 'value of a particular metric across all barriers',
    totalEfficiency(Metrics, Barriers) 'total efficiency of delivering a metric across all projects at a barrier',
    totalPropEfficiency(Metrics, Barriers) 'total efficiency of delivering a metric across all projects at a barrier that propogates up/down stream';

positive variable
    actionXeff(Metrics, Barriers, Projects) 'actionXeff(Metrics, Barriers, Projects) = actions(Barriers, Projects)*totalPropEfficiency(Metrics, Downstream(Barriers))';

binary variable
    actions(Barriers, Projects) 'Complete project at barrier: yes or no';


* EQUATION (MODEL) DEFINITION

equations
eq_objective 'maximize the weighted sum of metrics',
eq_value 'metric values at a barrier of all projects are the maximum possible value times the final efficiency at delivering that metric by all projects',
eq_totalEfficiency 'efficiency of delivering metrics at a barrier from both downstream and non-propogating actions',
eq_totalPropEfficiency 'efficiency of delivering metrics at barriers from all projects at and at downstream barriers',
cn_actionXeff_totalPropEfficiency 'part of equality constraint for actionXeff',
cn_actionXeff_actions 'part of equality constraint for actionXeff',
cn_actionXeff_effAndAction 'part of equality constraint for actionXeff',
cn_budget 'budget constraint';

eq_objective..
    objective =e= sum((Metrics), weight(Metrics) * value(Metrics));

eq_value(Metrics)..
    value(Metrics) =e= sum((Barriers), metricMax(Metrics, Barriers) * totalEfficiency(Metrics, Barriers));

eq_totalEfficiency(Metrics, Barriers)..
    totalEfficiency(Metrics, Barriers) =e= baseSingleEfficiency(Metrics, Barriers) + sum(Projects, projSingleEfficiency(Metrics, Barriers, Projects) * actions(Barriers, Projects)) + totalPropEfficiency(Metrics, Barriers);

eq_totalPropEfficiency(Metrics, J, K)$(Downstream(J,K) and (not Dummy(J)))..
    totalPropEfficiency(Metrics, J) =e= basePropEfficiency(Metrics, J) * totalPropEfficiency(Metrics, K) + sum(Projects, projPropEfficiency(Metrics, J, Projects) * actionXeff(Metrics, J, Projects));

cn_actionXeff_totalPropEfficiency(Metrics, J, Projects, K)$(Downstream(J,K) and (not Dummy(J)))..
    actionXeff(Metrics, J, Projects) =l= totalPropEfficiency(Metrics, K);

cn_actionXeff_actions(Metrics, Barriers, Projects)..
    actionXeff(Metrics, Barriers, Projects) =l= actions(Barriers, Projects);

cn_actionXeff_effAndAction(Metrics, J, Projects, K)$(Downstream(J,K) and (not Dummy(J)))..
    actionXeff(Metrics, J, Projects) =g= totalPropEfficiency(Metrics, K) + actions(J, Projects) - 1;

cn_budget..
    sum((Barriers, Projects), projectCost(Barriers, Projects) * actions(Barriers, Projects)) =l= budget;


model barrierModel /all/;


* SOLVE
option optcr = 1e-6;
barrierModel.optfile=1;
barrierModel.reslim = 3600;
barrierModel.holdfixed = 1;
barrierModel.limcol    = 0;
barrierModel.limrow    = 0;

* fix downstream efficiency of roots at 1 to avoid issues in referencing
totalPropEfficiency.fx(Metrics, Barriers)$(Dummy(Barriers)) = 1;

* set bounds on Metric values to meet caps
value.up(Metrics)$(weight(Metrics) lt 0) = cap(Metrics);
value.lo(Metrics)$(weight(Metrics) gt 0) = cap(Metrics);

solve barrierModel using mip max objective;
abort$(barrierModel.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';


* DISPLAY EXTRA RESULTS
set ActionsToPerform;
parameter RemainingBudget;
remainingBudget = budget - sum((Barriers, Projects), projectCost(Barriers, Projects) * actions.l(Barriers, Projects));
ActionsToPerform(Barriers, Projects) = yes$(actions.l(Barriers, Projects));
display ActionsToPerform;
display RemainingBudget;


* WRITE OUTPUT
$GDXOUT outfile
$unload ActionsToPerform RemainingBudget weight metricMax projPropEfficiency projSingleEfficiency basePropEfficiency projectCost cap
$GDXOUT
