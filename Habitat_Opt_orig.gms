$title Habitat Optimization with Generic Barrier or Habitat Actions (Fishworks v6)
* Based on O'Hanley model formulation v2, model 1

* DEFINE COMMAND-LINE OPTIONS

* input gdx
$if not set inputfile $set inputfile 'data.gdx'


* SETS AND DEFINITIONS

sets
    Targets(*) 'set of targets to be affected by project actions',
    Barriers(*) 'set of candidate dams/road culverts for removal/upgrade (by ID number)';
alias
    (Targets,T),
    (Barriers,J,K);
sets
    Downstream(J,K) 'K is the barrier immediately downstream from J; used for tracing upstream/downstream effects of actions',
    Root(J) 'root nodes of river-system (barriers with no downstream node)',
    TargetsBeneficiary(T) 'set of beneficiary targets',
    TargetsControl(T) 'set of targets to reduce/control';
alias
    (TargetsBeneficiary,TB),
    (TargetsControl,TC);
parameter
    passBase(J,T) 'current passability at barrier j for target t',
    passChange(J,T) 'increase in passability due to barrier removal',
    benefitMaxBase(J,T) 'baseline potential quality-adjusted benefit above barrier j for target t',
    benefitMaxChange(J,T) 'change in potential quality-adjusted benefit in area j for target t',
    costPass(J) 'cost of executing action that affects the passability of barrier j',
    costBen(J) 'cost of executing action that affects total potential benefit above barrier j',
    cap(T) 'max (min) allowed accessibility-weighted benefit for TargetsControl (TargetsBeneficiary)',
    weight(T) 'weight/priority of target t';
scalar
    budget 'management budget (barrier passability + potential benefit actions)',
    obj2Weight 'weight on secondary objective (here to do with control targets)' / 1e-3 /;


* LOAD MODEL DATA
$GDXIN %inputfile%
$load Targets, Barriers, Downstream, Root, TargetsBeneficiary, TargetsControl
$load passBase, passChange, benefitMaxBase, benefitMaxChange, costBen, costPass
$load budget, weight, cap
$gdxin


* CHECK DATA REQUIREMENTS

parameter cntHabMag 'Barrier/Fish pairs for which ||benefitMaxBase|| < ||benefitMaxChange|| which would violate model assumptions.';
cntHabMag = sum((J,T)$(abs(benefitMaxBase(J,T)) < abs(benefitMaxChange(J,T))), 1);
if (cntHabMag > 0, abort 'Magnitude of baseline benefitMaxBase values must be larger than magnitude of benefitMaxBase change with action.');



* VARIABLE AND EQUATION DECLARATIONS
free variable
    totalBenefit 'total weighted benefit across targets for entire system',
    cumPass(J,T) 'cumulative passability of barrier j for target t',
    cumBenBar(J,T) 'accessibility-weighted benefit at barrier j for target t';
positive variable
    actionPassXcumPass(J,T) 'actionPassXcumPass(J) = actionPass(J)*cumPass(Downstream(J),T)',
    actionBenXcumPass(J,T) 'actionBenXcumPass(J) = actionBen(J)*cumPass(J,T)';
binary variable
    actionPass(J) 'take action to change passability at j: yes or no',
    actionBen(J) 'take action to change potential benefit above barrier j: yes or no';

    
* EQUATION (MODEL) DEFINITION

equations
eq_objective 'first maximize beneficiary targets benefits, secondarily minimize control targets benefits',
eq_cumBenBar(J,T) 'calculate cumBenBar(j,t)',
eq_cumPass_root(J,T) 'calculate cumPass(j,t) at each root node',
eq_cumPass_upstream(J,K,T) 'calculate cumPass(j,t) at each upstream node',
cn_budget 'enforce budget constraint',
cn_cap_TC(T) 'limit available accessibility-weighted benefit for control targets',
cn_cap_TB(T) 'enforce minimum accessibility-weighted benefit for beneficiary targets',
cn_actionBenXcumPass_actionBen(J,T) 'first part of probability chain to linearize actionBenXcumPass',
cn_actionBenXcumPass_cumPass(J,T) 'second part of probability chain to linearize actionBenXcumPass',
cn_actionPassXcumPass_actionPass(J,T) 'first part of probability chain to linearize actionPassXcumPass',
cn_actionPassXcumPass_Root(J,T) 'first part of probability chain to linearize actionPassXcumPass',
cn_actionPassXcumPass_cumPass(J,K,T) 'third part of probability chain to linearize actionPassXcumPass',
cn_actionPassXcumPass_upstream(J,K,T) 'third part of probability chain to linearize actionPassXcumPass, specific for upstream nodes and control targets';
*cn_controlXcumPass_equality(J,T) 'Check that actionBenXcumPass meets its equality constraint.';

eq_objective..
    totalBenefit =e= sum((J,TB), weight(TB)*cumBenBar(J,TB)) + obj2Weight*sum((J,TC), weight(TC)*cumBenBar(J,TC));

eq_cumBenBar(J,T)..
    cumBenBar(J,T) =e= benefitMaxBase(J,T)*cumPass(J,T) + benefitMaxChange(J,T)*actionBenXcumPass(J,T);

eq_cumPass_root(J,T)$(Root(J))..
    cumPass(J,T) =e= passBase(J,T) + passChange(J,T)*actionPassXcumPass(J,T);

eq_cumPass_upstream(J,K,T)$(not Root(J) and Downstream(J,K))..
    cumPass(J,T) =e= passBase(J,T)*cumPass(K,T) + passChange(J,T)*actionPassXcumPass(J,T);

cn_budget..
    sum(J, costPass(J)*actionPass(J) + costBen(J)*actionBen(J)) =l= budget;

cn_cap_TC(T)$(TargetsControl(T))..
    sum(J, cumBenBar(J,T)) =l= cap(T);

cn_cap_TB(T)$(TargetsBeneficiary(T))..
    sum(J, cumBenBar(J,T)) =g= cap(T);

cn_actionBenXcumPass_actionBen(J,T)..
    actionBenXcumPass(J,T) =l= actionBen(J);

cn_actionBenXcumPass_cumPass(J,T)..
    actionBenXcumPass(J,T) =l= cumPass(J,T);

cn_actionPassXcumPass_actionPass(J,T)..
    actionPassXcumPass(J,T) =l= actionPass(J);
    
cn_actionPassXcumPass_Root(J,T)$(Root(J) and TargetsControl(T))..
    actionPassXcumPass(J,T) =g= actionpass(J);

cn_actionPassXcumPass_cumPass(J,K,T)$(not Root(J) and Downstream(J,K))..
    actionPassXcumPass(J,T) =l= cumPass(K,T);
    
cn_actionPassXcumPass_upstream(J,K,T)$((not Root(J)) and TargetsControl(T) and Downstream(J,K))..
    actionPassXcumPass(J,T) =g= cumPass(K,T) + actionPass(J) - 1;
    
* Checked by Austin Milt 11/05/2015 and does not change results (appears to not be necessary)    
*cn_controlXcumPass_equality(J,T)..
*    actionBenXcumPass(J,T) =g= cumPass(J,T) + actionBen(J) - 1;

model fishHabitat /all/;


* SOLVE
option optcr = 1e-6;
fishHabitat.optfile=1;
fishHabitat.reslim = 3600;
fishHabitat.holdfixed = 1;
fishHabitat.limcol    = 0;
fishHabitat.limrow    = 0;

solve fishHabitat using mip max totalBenefit;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';


* DISPLAY SUMMARY RESULTS

parameter
    remainingBudget 'leftover budget',
    speciesHabitat(T) 'total available benefitMaxBase for target species';
sets
    toRemove(J) "Barriers that should be removed",
    toControl(J) "Barriers that should have control actions",
    negHab(J,T) "Barrier/Fish pairs for which cumBenBar comes out negative which would require additional constraints";


actionPass.l(J) = round(actionPass.l(J));
toRemove(J) = yes$(actionPass.l(J));

actionBen.l(J) = round(actionBen.l(J));
toControl(J) = yes$(actionBen.l(J));

negHab(J,T) = yes$(cumBenBar.l(J,T) < 0);

remainingBudget = budget - sum(J, costBen(J)*actionBen.l(J) + costPass(J)*actionPass.l(J));

speciesHabitat(T) = sum(J, cumBenBar.l(J,T));

display totalBenefit.l;
option toRemove:0:0:2;
display toRemove;
option toControl:0:0:2;
display toControl;
display speciesHabitat;
display remainingBudget;
option negHab:0:0:2;
display negHab;
