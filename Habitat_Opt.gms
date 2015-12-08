$title Projects at Barriers for General Goals (Fishworks v6)

* DEFINE COMMAND-LINE OPTIONS

* input gdx
$if not set inputfile $set inputfile 'data.gdx'


* SETS AND DEFINITIONS

sets
    Goals(*) 'conservation goals to be achieved by taking actions at barriers',
    Barriers(*) 'points at which actions can be taken',
    Projects(*) 'projects that can be undertaken at barriers'
    Dummy(Barriers) 'dummy barrier to set totalPropEfficiency of downstream barriers of roots to 1';

alias (Barriers, J, K);

sets
    Downstream(J, K) 'barrier immediately downstream of another';

parameters
    weight(Goals) 'objective weight of goal',
    maxBenefit(Goals, Barriers) 'maximum possible contribution to goal at a barrier',
    baseEfficiency(Goals, Barriers) 'base level efficiency of goal contribution at barrier',
    projPropEfficiency(Goals, Barriers, Projects) 'efficiency increase of delivering a goal at a barrier by doing a project that is affected by and effects up/downstream efficiencies',
    projSingleEfficiency(Goals, Barriers, Projects) 'efficiency increase of delivering a goal at a barrier that affects only the delivery at that barrier and not others',
    projectCost(Barriers, Projects) 'cost of successfully completing project at barrier',
    cap(Goals) 'minimum (or maximum) allowable value of each goals total benefit';

scalars
    budget 'total budget for spending on all projects',
    epsilon 'epsilon value for equality tests' / 1e-6 /;


* LOAD MODEL DATA
$GDXIN %inputfile%
$load Projects, Barriers, Goals, Downstream, weight, maxBenefit, Dummy
$load baseEfficiency, projPropEfficiency, projectCost, cap, budget
$load projSingleEfficiency
$GDXIN


* DEFINE DUMMY BARRIER PARAMETERS
maxBenefit(Goals, Barriers)$(Dummy(Barriers)) = 0;
baseEfficiency(Goals, Barriers)$(Dummy(Barriers)) = 1;
projPropEfficiency(Goals, Barriers, Projects)$(Dummy(Barriers)) = 0;
projSingleEfficiency(Goals, Barriers, Projects)$(Dummy(Barriers)) = 0;
projectCost(Barriers, Projects)$(Dummy(Barriers)) = budget + 1;


* CHECK DATA REQUIREMENTS
parameter possibleEfficiency(Goals, Barriers) 'total possible efficiency at a barrier for a goal';
parameter cntEffOOB 'number of Goal/Barrier pairs for which the total possible efficiency is outside [0, 1], which violates assumptions';
possibleEfficiency(Goals, Barriers) = baseEfficiency(Goals, Barriers) + sum(Projects, projPropEfficiency(Goals, Barriers, Projects)) + sum(Projects, projSingleEfficiency(Goals, Barriers, Projects));
cntEffOOB = sum((Goals, Barriers)$((possibleEfficiency(Goals, Barriers) > (1 + epsilon)) or (possibleEfficiency(Goals, Barriers) < (0 - epsilon))), 1);
if (cntEffOOB > 0, abort 'Total possible efficiency for a goal at a barrier must be in the closed interval [0, 1].');


* VARIABLE AND EQUATION DECLARATIONS

free variable
    totalBenefit 'total weighted benefit across all goals',
    benefit(Goals) 'total benefit to a particular goal across all barriers',
    totalEfficiency(Goals, Barriers) 'total efficiency of delivering a benefit to a goal across all projects at a barrier',
    totalPropEfficiency(Goals, Barriers) 'total efficiency of delivering a benefit to a goal across all projects at a barrier that propogates up/down stream';

positive variable
    actionXeff(Goals, Barriers, Projects) 'actionXeff(Goals, Barriers, Projects) = actions(Barriers, Projects)*totalPropEfficiency(Goals, Downstream(Barriers))';

binary variable
    actions(Barriers, Projects) 'Complete project at barrier: yes or no';


* EQUATION (MODEL) DEFINITION

equations
eq_objective 'maximize the weighted sum of project benefits',
eq_benefit 'benefits at a barrier of all projects are the maximum possible benefit times the final efficiency at delivering that benefit by all projects',
eq_totalEfficiency 'efficiency of delivering benefits at a barrier from both downstream and non-propogating actions',
eq_totalPropEfficiency 'efficiency of delivering benefits at barriers from all projects at and at downstream barriers',
cn_actionXeff_totalPropEfficiency 'part of equality constraint for actionXeff',
cn_actionXeff_actions 'part of equality constraint for actionXeff',
cn_actionXeff_effAndAction 'part of equality constraint for actionXeff',
cn_budget 'budget constraint',
cn_benefits 'ensure minimum (or maximum) benefit thresholds are met';

eq_objective..
    totalBenefit =e= sum((Goals), weight(Goals) * benefit(Goals));

eq_benefit(Goals)..
    benefit(Goals) =e= sum((Barriers), maxBenefit(Goals, Barriers) * totalEfficiency(Goals, Barriers));

eq_totalEfficiency(Goals, Barriers)..
    totalEfficiency(Goals, Barriers) =e= sum(Projects, projSingleEfficiency(Goals, Barriers, Projects) * actions(Barriers, Projects)) + totalPropEfficiency(Goals, Barriers);

eq_totalPropEfficiency(Goals, J, K)$(Downstream(J,K) and (not Dummy(J)))..
    totalPropEfficiency(Goals, J) =e= baseEfficiency(Goals, J) * totalPropEfficiency(Goals, K) + sum(Projects, projPropEfficiency(Goals, J, Projects) * actionXeff(Goals, J, Projects));

cn_actionXeff_totalPropEfficiency(Goals, J, Projects, K)$(Downstream(J,K) and (not Dummy(J)))..
    actionXeff(Goals, J, Projects) =l= totalPropEfficiency(Goals, K);

cn_actionXeff_actions(Goals, Barriers, Projects)..
    actionXeff(Goals, Barriers, Projects) =l= actions(Barriers, Projects);

cn_actionXeff_effAndAction(Goals, J, Projects, K)$(Downstream(J,K) and (not Dummy(J)))..
    actionXeff(Goals, J, Projects) =g= totalPropEfficiency(Goals, K) + actions(J, Projects) - 1;

cn_budget..
    sum((Barriers, Projects), projectCost(Barriers, Projects) * actions(Barriers, Projects)) =l= budget;

cn_benefits(Goals)..
    sign(weight(Goals)) * (benefit(Goals) - cap(Goals)) =g= -epsilon;


model barrierModel /all/;


* SOLVE
option optcr = 1e-6;
barrierModel.optfile=1;
barrierModel.reslim = 3600;
barrierModel.holdfixed = 1;
barrierModel.limcol    = 0;
barrierModel.limrow    = 0;

* fix downstream efficiency of roots at 1 to avoid issues in referencing
totalPropEfficiency.fx(Goals, Barriers)$(Dummy(Barriers)) = 1;

solve barrierModel using mip max totalBenefit;
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
$unload ActionsToPerform RemainingBudget weight maxBenefit projPropEfficiency projSingleEfficiency baseEfficiency projectCost cap
$GDXOUT
