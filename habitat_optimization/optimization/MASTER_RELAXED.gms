$title Decomposition Linear Relaxtion - Budget Determination
* Based on O'Hanley model formulation v2, model 1, modified to allow
*   multiple projects and differentiate candidate from non-candidate barriers
* Decomposition as coded by Nate Pelc but adapted for newest version
option solprint=off, limrow=0, limcol=0;

* DEFINE COMMAND-LINE OPTIONS

* input gdx (not including output from previous run)
$if not set defaultgdx $set defaultgdx 'data_all.gdx'
$if not set rungdx $set rungdx 'data_run.gdx'


* SETS AND DEFINITIONS

sets
    Targets(*) 'set of targets to be affected by project actions',
    Barriers(*) 'set of barriers dams/road culverts in the network (by ID number)',
    Projects(*) 'projects that can be done to affect barrier passability or upstream benefit potential',
    BudgetNames(*) 'spending budgets from which projects can draw money',
	Networks(*) 'Independent barrier networks for decomposition';
alias
    (Targets,T),
    (Barriers,J,K),
    (Projects,P),
    (BudgetNames,B),
	(Networks, N);
sets
    Downstream(J,K) 'K is the barrier immediately downstream from J; used for tracing upstream/downstream effects of actions',
    TargetsBeneficiary(T) 'set of beneficiary targets',
    TargetsControl(T) 'set of targets to reduce/control',
    ProjectsBenefit(P) 'projects that affect potential benefit',
    ProjectsPassability(P) 'projects that affect barrier passability',
    ProjectToBudget(P,B) 'budget from which project draws money',
	BarrierNetwork(J,N) 'assignment of barrier to its network',
	NonnetworkedBarriers(J) 'barriers left out of network assignment';
alias
    (TargetsBeneficiary, TB),
    (TargetsControl, TC),
    (ProjectsBenefit, PB),
    (ProjectsPassability, PP),
	(BarrierNetwork, JN);
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
$GDXIN %defaultgdx%
$load Targets, Barriers, Projects, BudgetNames, Networks
$gdxin

$GDXIN %rungdx%
$loadm Targets, Barriers, Projects, BudgetNames, Networks
$gdxin

$GDXIN %defaultgdx%
$load Downstream, TargetsBeneficiary, TargetsControl, ProjectsPassability
$load ProjectsBenefit, passBase, passChange, benefitMaxBase
$load benefitMaxChange, cost, budget, weight, cap, ProjectToBudget, obj2Weight
$load isCandidate, isRoot, NonnetworkedBarriers
$gdxin

$GDXIN %rungdx%
$loadm Downstream, TargetsBeneficiary, TargetsControl, ProjectsPassability
$loadm ProjectsBenefit, passBase, passChange, benefitMaxBase
$loadm benefitMaxChange, cost, budget, weight, cap, ProjectToBudget, obj2Weight
$loadm isCandidate, isRoot, NonnetworkedBarriers
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
    Candidates(J,P) 'set of candidate barriers for removal',
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
$ifthen set start
set doActions(J,P);
$GDXIN %start%
$load doActions=actions
$gdxin
$endif

* set up relaxation
actions.prior(J,Projects) = inf;
actions.prior(NonnetworkedBarriers,Projects) = 1;


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
fishHabitat.reslim = 3600;
fishHabitat.holdfixed = 1;
fishHabitat.limcol    = 0;
fishHabitat.limrow    = 0;
fishHabitat.prioropt = 1;
$ifthen set start
    fishHabitat.optfile=1;
    actions.l(J,P)$(doActions(J,P)) = 1;
$endif

* fix all non-candidate barrier passChange and benMaxChange to 0 to avoid
*   having them selected for removal or treatment
passChange(J,P,T)$(not Candidates(J,P)) = 0;
actions.fx(J,P)$(not Candidates(J,P)) = 0;
benefitMaxChange(J,P,T)$(not Candidates(J,P)) = 0;

solve fishHabitat using mip max totalBenefit;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';


* DISPLAY SUMMARY RESULTS

parameters
    speciesHabitat(T) 'total available habitat for target species',
	controlNetworkHabitat(TC,N) 'total habitat for control species in each network',
	expenditures(N,B) 'total spent on each project in each network'
	nonnetworkedCost(P) 'cost of each project for non-networked barriers'
	
sets
    doActions(J,P) "Barriers that should be removed",
    negHab(J,T) "Barrier/Fish pairs for which cumBenBar comes out negative which would require additional constraints";


actions.l(J,P) = round(actions.l(J,P));
doActions(J,P) = yes$(actions.l(J,P));

negHab(J,T) = yes$(cumBenBar.l(J,T) < 0);

speciesHabitat(T) = sum(J, cumBenBar.l(J,T));

controlNetworkHabitat(TC,N) = sum(J$(BarrierNetwork(J,N)), cumBenBar.l(J,TC));

expenditures(N,B) = sum((J,P)$(BarrierNetwork(J,N) and ProjectToBudget(P,B)), cost(J,P));

nonnetworkedCost(P) = sum(NonnetworkedBarriers, cost(NonnetworkedBarriers,P)*actions.l(NonnetworkedBarriers,P));

display nonnetworkedCost, doActions, actions.l;


* WRITE OUTPUT GDX
Execute_Unload 'results',
    totalBenefit.l=objective, doActions=action_set, speciesHabitat=target_benefits,
    remainingBudget=remaining_budget, negHab=negative_benefits,
	controlNetworkHabitat=control_habitat, expenditures=network_budgets,
	nonnetworkedCost=nonnetworked_cost, Barriers, Targets, Downstream, Root,
	TC, TB, Networks, BarrierNetwork, NonnetworkedBarriers, actions, PP, PB,
	passBase, passChange, benefitMaxBase, benefitMaxChange, cost, budget,
	weight, cap, ProjectToBudget, obj2Weight;
	
	
* write cplex options file
$ifthen set start
$onecho > cplex.opt
mipstart 1
$offecho
$endif
