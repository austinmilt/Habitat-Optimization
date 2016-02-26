$title Habitat Optimization with Generic Barrier or Habitat Actions (Fishworks v6)
* Based on O'Hanley model formulation v2, model 1, modified to allow
*   multiple projects and differentiate candidate from non-candidate barriers

* DEFINE COMMAND-LINE OPTIONS

* input gdx
$if not set inputfile $set inputfile 'data_run_1.gdx'


* SETS AND DEFINITIONS

sets
    Targets(*) 'set of targets to be affected by project actions',
    Barriers(*) 'set of barriers dams/road culverts in the network (by ID number)',
    Projects(*) 'projects that can be done to affect barrier passability or upstream benefit potential',
    BudgetNames(*) 'spending budgets from which projects can draw money';
alias
    (Targets,T),
    (Barriers,J,K),
    (Projects,P),
    (BudgetNames,B);
sets
    Downstream(J,K) 'K is the barrier immediately downstream from J; used for tracing upstream/downstream effects of actions',
    TargetsBeneficiary(T) 'set of beneficiary targets',
    TargetsControl(T) 'set of targets to reduce/control',
    ProjectsBenefit(P) 'projects that affect potential benefit',
    ProjectsPassability(P) 'projects that affect barrier passability',
    ProjectToBudget(P,B) 'budget from which project draws money';
alias
    (TargetsBeneficiary, TB),
    (TargetsControl, TC),
    (ProjectsBenefit, PB)
    (ProjectsPassability, PP);
parameter
    isCandidate(J,P) 'Boolean indicating that a barrier is a candidate for a project',
    isRoot(J) 'Boolean indicating that a barrier is a root barrier (has no downstream barriers)',
    passBase(J,T) 'current passability at barrier j for target t',
    passChange(J,P,T) 'change in passability for target t by doing project p at barrier j',
    benefitMaxBase(J,T) 'baseline potential quality-adjusted benefit above barrier j for target t',
    benefitMaxChange(J,P,T) 'change in potential quality-adjusted benefit in area j for target t from doing project p',
    cost(J,P) 'cost of doing project p at barrier J',
    cap(T) 'max (min) allowed accessibility-weighted benefit for TargetsControl (TargetsBeneficiary)',
    weight(T) 'weight/priority of target t',
    budget(B) 'budget amounts from which projects draw money';
scalar
    obj2Weight 'weight on secondary objective (here to do with control targets)';


* LOAD MODEL DATA
$GDXIN %inputfile%
$load Targets, Barriers, Downstream, TargetsBeneficiary
$load TargetsControl, Projects, ProjectsPassability, ProjectsBenefit
$load BudgetNames, passBase, passChange, benefitMaxBase, benefitMaxChange, cost
$load budget, weight, cap, ProjectToBudget, obj2Weight,  isCandidate, isRoot
$gdxin


* CHECK DATA REQUIREMENTS
parameter
    cntHabMag 'Barrier/Fish pairs for which ||benefitMaxBase|| < ||benefitMaxChange|| which would violate model assumptions.',
    possiblePassability(J,T) 'total possible passability of a barrier for a target',
    cntEffOOB 'number of Target/Barrier pairs for which the total possible passability is outside [0, 1], which violates assumptions';

cntHabMag = sum((J,P,T)$(abs(benefitMaxBase(J,T)) < abs(benefitMaxChange(J,P,T))), 1);
if (cntHabMag > 0, abort 'Magnitude of baseline benefitMaxBase values must be larger than magnitude of benefitMaxBase change with action.');
possiblePassability(J,T) = passBase(J,T) + sum(P$(ProjectsPassability(P)), passChange(J,P,T));
cntEffOOB = sum((J,T)$((possiblePassability(J,T) > (1.00001)) or (possiblePassability(J,T) < (-0.00001))), 1);
if (cntEffOOB > 0, abort 'Total possible passability for a target at a barrier must be in the closed interval [0, 1].');


* VARIABLE AND EQUATION DECLARATIONS
set
    Candidates(J, P) 'set of candidate barriers for removal',
    Root(J) 'root nodes of river-system (barriers with no downstream node)';
free variable
    totalBenefit 'total weighted benefit across targets for entire system',
    cumPass(J,T) 'cumulative passability of barrier j for target t',
    cumBenBar(J,T) 'accessibility-weighted benefit at barrier j for target t';
positive variable
    action_benXcumPass(J,P,T) 'action_benXcumPass(J,P,T) = actions(J,benefit_actions P)*cumPass(Downstream(J),T)',
    action_passXcumPass(J,P,T) 'action_passXcumPass(J,P,T) = actionBen(J, passability_actions P)*cumPass(J,T)';
binary variable
    actions(J,P) 'perform project p at barrier j: yes or no';

* set up derived parameters from inputs
Candidates(J,P) = yes$(isCandidate(J,P));
Root(J) = yes$(isRoot(J));


* EQUATION (MODEL) DEFINITION

equations
eq_objective 'first maximize beneficiary targets benefits, secondarily minimize control targets benefits',
eq_cumBenBar(J,T) 'calculate cumBenBar(j,t)',
eq_cumPass_root(J,T) 'calculate cumPass(j,t) at each root node',
eq_cumPass_upstream(J,K,T) 'calculate cumPass(j,t) at each upstream node',
cn_budget(B) 'enforce budget constraints',
cn_cap_TC(T) 'limit available accessibility-weighted benefit for control targets',
cn_cap_TB(T) 'enforce minimum accessibility-weighted benefit for beneficiary targets',
cn_action_benXcumPass_actionBen(J,P,T) 'first part of probability chain to linearize action_benXcumPass',
cn_action_benXcumPass_cumPass(J,P,T) 'second part of probability chain to linearize action_benXcumPass',
cn_action_passXcumPass_actionPass(J,P,T) 'first part of probability chain to linearize action_passXcumPass',
cn_action_passXcumPass_Root(J,P,T) 'second part of probability chain to linearize action_passXcumPass',
cn_action_passXcumPass_cumPass(J,K,P,T) 'third part of probability chain to linearize action_passXcumPass',
cn_action_passXcumPass_upstream(J,K,P,T) 'third part of probability chain to linearize action_passXcumPass, specific for upstream nodes and control targets';
*cn_controlXcumPass_equality(J,T) 'Check that action_benXcumPass meets its equality constraint.';

eq_objective..
    totalBenefit =e= sum((J,TB), weight(TB)*cumBenBar(J,TB)) + obj2Weight*sum((J,TC), weight(TC)*cumBenBar(J,TC));

eq_cumBenBar(J,T)..
    cumBenBar(J,T) =e= benefitMaxBase(J,T)*cumPass(J,T) + sum(PB(P), benefitMaxChange(J,PB,T)*action_benXcumPass(J,PB,T));

eq_cumPass_root(J,T)$(Root(J))..
    cumPass(J,T) =e= passBase(J,T) + sum(PP(P), passChange(J,PP,T)*actions(J,PP));
*   cumPass(J,T) =e= passBase(J,T) + sum(ProjectsPassability(P), passChange(J,PP,T)*action_passXcumPass(J,PP,T));

eq_cumPass_upstream(J,K,T)$((not Root(J)) and Downstream(J,K))..
    cumPass(J,T) =e= passBase(J,T)*cumPass(K,T) + sum(PP(P), passChange(J,PP,T)*action_passXcumPass(J,PP,T));

cn_budget(B)..
    sum((J,P)$(Candidates(J,P) and ProjectToBudget(P,B)), cost(J,P)*actions(J,P)) =l= budget(B);

cn_cap_TC(T)$(TargetsControl(T))..
    sum(J, cumBenBar(J,T)) =l= cap(T);

cn_cap_TB(T)$(TargetsBeneficiary(T))..
    sum(J, cumBenBar(J,T)) =g= cap(T);

cn_action_benXcumPass_actionBen(J,P,T)$(ProjectsBenefit(P))..
    action_benXcumPass(J,P,T) =l= actions(J,P);

cn_action_benXcumPass_cumPass(J,P,T)$(ProjectsBenefit(P))..
    action_benXcumPass(J,P,T) =l= cumPass(J,T);

cn_action_passXcumPass_actionPass(J,P,T)$(ProjectsPassability(P))..
    action_passXcumPass(J,P,T) =l= actions(J,P);

cn_action_passXcumPass_Root(J,P,T)$(Root(J) and TargetsControl(T) and ProjectsPassability(P))..
    action_passXcumPass(J,P,T) =g= actions(J,P);
* Austin Milt 02/11/2015 The specification for TargetsControl at Roots is
*   necessary to enforce non-negative passabilities for TargetsControl
*   throughout the network

cn_action_passXcumPass_cumPass(J,K,P,T)$((not Root(J)) and Downstream(J,K) and ProjectsPassability(P))..
    action_passXcumPass(J,P,T) =l= cumPass(K,T);

cn_action_passXcumPass_upstream(J,K,P,T)$((not Root(J)) and TargetsControl(T) and Downstream(J,K) and ProjectsPassability(P))..
    action_passXcumPass(J,P,T) =g= cumPass(K,T) + actions(J,P) - 1;

* Checked by Austin Milt 11/05/2015 and does not change results (appears to not be necessary)
*cn_controlXcumPass_equality(J,T)..
*    action_benXcumPass(J,T) =g= cumPass(J,T) + actionBen(J) - 1;

model fishHabitat /all/;


* SOLVE
option optcr = 1e-6;
fishHabitat.optfile=1;
fishHabitat.reslim = 3600;
fishHabitat.holdfixed = 1;
fishHabitat.limcol    = 0;
fishHabitat.limrow    = 0;

* fix all non-candidate barrier passChange and benMaxChange to 0 to avoid
*   having them selected for removal or treatment
passChange(J,P,T)$(not Candidates(J,P)) = 0;
actions.fx(J,P)$(not Candidates(J,P)) = 0;
benefitMaxChange(J,P,T)$(not Candidates(J,P)) = 0;

solve fishHabitat using mip max totalBenefit;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';


* DISPLAY SUMMARY RESULTS

parameter
    remainingBudget(B) 'leftover budget',
    speciesHabitat(T) 'total available benefitMaxBase for target species';
sets
    doActions(J,P) "Barriers that should be removed",
    negHab(J,T) "Barrier/Fish pairs for which cumBenBar comes out negative which would require additional constraints";


actions.l(J,P) = round(actions.l(J,P));
doActions(J,P) = yes$(actions.l(J,P));

negHab(J,T) = yes$(cumBenBar.l(J,T) < 0);

remainingBudget(B) = budget(B) - sum((J,P)$(Candidates(J,P) and ProjectToBudget(P,B)), cost(J,P)*actions.l(J,P));

speciesHabitat(T) = sum(J, cumBenBar.l(J,T));

display totalBenefit.l;
option doActions:0:0:2;
display doActions;
display speciesHabitat;
display remainingBudget;
option negHab:0:0:2;
display negHab;


* WRITE OUTPUT GDX
Execute_Unload 'results', 
    totalBenefit.l=objective, doActions=actions, speciesHabitat=target_benefits,
    remainingBudget=remaining_budget, negHab=negative_benefits;