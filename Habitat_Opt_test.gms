$title Barrier Removal and Lampricide Applicaiton (Fishworks v5)

* DEFINE COMMAND-LINE OPTIONS

* input gdx


* SETS AND DEFINITIONS

set Projects 'projects that can be undertaken at barriers' / 'remove', 'lampricide' /;
set Barriers 'points at which actions can be taken' / 'A', 'B', 'C', 'D' /;
alias (Barriers, J, K);
set Downstream(J, K) 'barrier immediately downstream of another' / 'A'.'B', 'B'.'C', 'C'.'D'/;
set Dummy(Barriers) 'dummy barriers the upstream-barrier of which is a root barrier' / 'D' /;
set Goals 'conservation goals to be achieved by taking actions at barriers' / 'fish1', 'fish2', 'lamprey' /;

parameter weight(Goals) 'objective weight of goal'
    /   'fish1' 1, 'fish2' 1, 'lamprey' -1 /;

parameter maxBenefit(Goals, Barriers) 'maximum possible contribution to goal at a barrier'
    /   'fish1'.'A' 0,      'fish1'.'B' 0,      'fish1'.'C' 1,      'fish1'.'D' 0,
        'fish2'.'A' 0,      'fish2'.'B' 0,      'fish2'.'C' 1,      'fish2'.'D' 0,
        'lamprey'.'A' 0,    'lamprey'.'B' 0,    'lamprey'.'C' 1,    'lamprey'.'D' 0 /;

parameter baseEfficiency(Goals, Barriers) 'base level efficiency of goal contribution at barrier'
    /   'fish1'.'A' 0,    'fish1'.'B' 0,    'fish1'.'C' 0.5,    'fish1'.'D' 1,
        'fish2'.'A' 0,    'fish2'.'B' 0,    'fish2'.'C' 0.5,    'fish2'.'D' 1,
        'lamprey'.'A' 0,  'lamprey'.'B' 0,  'lamprey'.'C' 0.5,  'lamprey'.'D' 1 /;

parameter projectEfficiency(Goals, Barriers, Projects) 'efficiency increase of delivering a goal at a barrier by doing a project'
    /   'fish1'.'A'.'remove' 0,         'fish1'.'B'.'remove' 0,         'fish1'.'C'.'remove' 0.5,           'fish1'.'D'.'remove' 0,
        'fish1'.'A'.'lampricide' 0,     'fish1'.'B'.'lampricide' 0,     'fish1'.'C'.'lampricide' 0,         'fish1'.'D'.'lampricide' 0,
        'fish2'.'A'.'remove' 0,         'fish2'.'B'.'remove' 0,         'fish2'.'C'.'remove' 0.5,           'fish2'.'D'.'remove' 0,
        'fish2'.'A'.'lampricide' 0,     'fish2'.'B'.'lampricide' 0,     'fish2'.'C'.'lampricide' 0,         'fish2'.'D'.'lampricide' 0,
        'lamprey'.'A'.'remove' 0,       'lamprey'.'B'.'remove' 0,       'lamprey'.'C'.'remove' 0.5,         'lamprey'.'D'.'remove' 0,
        'lamprey'.'A'.'lampricide' 0,   'lamprey'.'B'.'lampricide' 0,   'lamprey'.'C'.'lampricide' -1,    'lamprey'.'D'.'lampricide' 0 /;

parameter projectCost(Barriers, Projects) 'cost of successfully completing project at barrier'
    /   'A'.'remove' 2000,  'A'.'lampricide' 2000,
        'B'.'remove' 2000,  'B'.'lampricide' 2000,
        'C'.'remove' 2000,  'C'.'lampricide' 2000,
        'D'.'remove' 5001,  'D'.'lampricide' 5001 /;

parameter cap(Goals) 'minimum (or maximum) allowable value of each goals total benefit'
    /   'fish1' 0, 'fish2' 0, 'lamprey' 5 /;

scalar budget 'total budget for spending on all projects' / 5000 /;


* LOAD MODEL DATA


* CHECK DATA REQUIREMENTS
parameter possibleEfficiency(Goals, Barriers) 'total possible efficiency at a barrier for a goal';
parameter cntEffOOB 'number of Goal/Barrier pairs for which the total possible efficiency is outside [0, 1], which violates assumptions';
possibleEfficiency(Goals, Barriers) = baseEfficiency(Goals, Barriers) + sum(Projects, projectEfficiency(Goals, Barriers, Projects));
cntEffOOB = sum((Goals, Barriers)$((possibleEfficiency(Goals, Barriers) > 1) or (possibleEfficiency(Goals, Barriers) < 0)), 1);
if (cntEffOOB > 0, abort 'Total possible efficiency for a goal at a barrier must be in the closed interval [0, 1].');


* VARIABLE AND EQUATION DECLARATIONS

free variable
    totalBenefit 'total weighted benefit across all goals',
    benefit(Goals) 'total benefit to a particular goal across all barriers';

positive variable
    totalEfficiency(Goals, Barriers) 'total efficiency of delivering a benefit to a goal across all projects at a barrier',
    actionXeff(Goals, Barriers, Projects) 'actionXeff(Goals, Barriers, Projects) = actions(Barriers, Projects)*totalEfficiency(Goals, Downstream(Barriers))';

binary variable
    actions(Barriers, Projects) 'Complete project at barrier: yes or no';


* EQUATION (MODEL) DEFINITION

equations
eq_objective 'maximize the weighted sum of project benefits',
eq_benefit 'benefits at a barrier of all projects are the maximum possible benefit times the final efficiency at delivering that benefit by all projects',
eq_totalEfficiency 'efficiency of delivering benefits at barriers from all projects at and at downstream barriers',
cn_actionXeff_totalEfficiency 'part of equality constraint for actionXeff',
cn_actionXeff_actions 'part of equality constraint for actionXeff',
cn_actionXeff_effAndAction 'part of equality constraint for actionXeff',
cn_budget 'budget constraint',
cn_benefits 'ensure minimum (or maximum) benefit thresholds are met';

eq_objective..
    totalBenefit =e= sum((Goals), weight(Goals) * benefit(Goals));

eq_benefit(Goals)..
    benefit(Goals) =e= sum((Barriers), maxBenefit(Goals, Barriers) * totalEfficiency(Goals, Barriers));

eq_totalEfficiency(Goals, J, K)$(Downstream(J,K) and (not Dummy(J)))..
    totalEfficiency(Goals, J) =e= baseEfficiency(Goals, J) * totalEfficiency(Goals, K) + sum(Projects, projectEfficiency(Goals, J, Projects) * actionXeff(Goals, J, Projects));

cn_actionXeff_totalEfficiency(Goals, J, Projects, K)$(Downstream(J,K) and (not Dummy(J)))..
    actionXeff(Goals, J, Projects) =l= totalEfficiency(Goals, K);

cn_actionXeff_actions(Goals, Barriers, Projects)..
    actionXeff(Goals, Barriers, Projects) =l= actions(Barriers, Projects);

cn_actionXeff_effAndAction(Goals, J, Projects, K)$(Downstream(J,K) and (not Dummy(J)))..
    actionXeff(Goals, J, Projects) =g= totalEfficiency(Goals, K) + actions(J, Projects) - 1;
    
cn_budget..
    sum((Barriers, Projects), projectCost(Barriers, Projects) * actions(Barriers, Projects)) =l= budget;

cn_benefits(Goals)..
    weight(Goals) * (benefit(Goals) - cap(Goals)) =g= 0;


model barrierModel /all/;


* SOLVE
option optcr = 1e-6;
barrierModel.optfile=1;
barrierModel.reslim = 3600;
barrierModel.holdfixed = 1;
barrierModel.limcol    = 0;
barrierModel.limrow    = 0;

* fix downstream efficiency of roots at 1 to avoid issues in referencing
totalEfficiency.fx(Goals, Dummy(Barriers)) = 1;

solve barrierModel using mip max totalBenefit;
abort$(barrierModel.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';
