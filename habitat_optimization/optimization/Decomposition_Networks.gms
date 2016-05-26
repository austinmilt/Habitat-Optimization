$title Barrier Decomposition SubNetwork solver
* Based on O'Hanley model formulation v2, model 1, modified to allow
*   multiple projects and differentiate candidate from non-candidate barriers
* Decomposition as coded by Nate Pelc but adapted for newest version
option solprint=off, limrow=0, limcol=0;
scalar starttime; starttime=jnow;


* DEFINE COMMAND-LINE OPTIONS

* input gdx (including output from master solve)
$if not set inputgdx $set inputgdx 'results.gdx'


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
	NonnetworkedBarriers(J) 'barriers left out of network assignment',
	BarrierAssociations(J,N) 'associations of leftout barriers to effected networks',
	BarriersIncluded(J) 'barriers within the current decomposed network to use',
	BarriersAccounted(J) 'barrires within a network that count towards network budget',
	doActions(J,P) 'set of actions to take, analogous to actions variable';
alias
    (TargetsBeneficiary, TB),
    (TargetsControl, TC),
    (ProjectsBenefit, PB),
    (ProjectsPassability, PP),
	(BarrierNetwork, JN),
	(BarrierAssociations, JA),
	(BarriersAccounted, JC)
	(BarriersIncluded, JI);
parameter
	Candidates(J,P) 'set of candidate barriers for removal',
    Root(J) 'root nodes of river-system (barriers with no downstream node)';
	passBase(J,T) 'current passability at barrier j for target t',
    passChange(J,P,T) 'change in passability for target t by doing project p at barrier j',
    benefitMaxBase(J,T) 'baseline potential quality-adjusted benefit above barrier j for target t',
    benefitMaxChange(J,P,T) 'change in potential quality-adjusted benefit in area j for target t from doing project p',
    cost(J,P) 'cost of doing project p at barrier J',
    cap(T) 'max (min) allowed accessibility-weighted benefit for TargetsControl (TargetsBeneficiary)',
    weight(T) 'weight/priority of target t',
    budget(B) 'budget amounts from which projects draw money',
	controlNetworkHabitat(T,N) 'total control species habitat in each network',
	networkBudgets(N,B) 'available budget to spend on each project within each network',
	speciesHabitat(T) 'total available habitat for target species';
scalar
    obj2Weight 'weight on secondary objective (here to do with control targets)';



* VARIABLE AND EQUATION DECLARATIONS
free variable
    totalBenefit 'total weighted benefit across targets for entire system',
    cumPass(J,T) 'cumulative passability of barrier j for target t',
    cumBenBar(J,T) 'accessibility-weighted benefit at barrier j for target t';
positive variable
    action_benXcumPass(J,P,T) 'action_benXcumPass(J,P,T) = actions(J,benefit_actions P)*cumPass(Downstream(J),T)',
    action_passXcumPass(J,P,T) 'action_passXcumPass(J,P,T) = actionBen(J, passability_actions P)*cumPass(J,T)';
binary variable
    actions(J,P) 'perform project p at barrier j: yes or no';
	
	
* LOAD MODEL DATA
$GDXIN %inputgdx%
$load Targets, Barriers, Projects, BudgetNames, Networks
$load doActions=action_set, actions, networkBudgets=network_budgets
$load Downstream, TargetsBeneficiary, TargetsControl, ProjectsPassability
$load ProjectsBenefit, passBase, passChange, benefitMaxBase
$load benefitMaxChange, cost, budget, weight, cap, ProjectToBudget, obj2Weight
$load NonnetworkedBarriers, BarrierAssociations, Candidates, Root
$load controlNetworkHabitat=control_habitat, speciesHabitat
$gdxin
$endif


* set up decision variable constraints
actions.lo(J,Projects) = 0;
actions.up(J,Projects) = 1;
actions.prior(J,Projects) = 3;
actions.prior(doActions) = 2;
actions.prior(NonnetworkedBarriers,Projects) = 1;
actions.l(J,Projects)$(not NonnetworkedBarriers(J)) = 0;
actions.fx(NonnetworkedBarriers,Projects) = round(actions.l(NonnetworkedBarriers,P));


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
    totalBenefit =e= sum((JC,TB), weight(TB)*cumBenBar(J,TB)) + obj2Weight*sum((JC,TC), weight(TC)*cumBenBar(JC,TC));

eq_cumBenBar(JI,T)..
    cumBenBar(JI,T) =e= benefitMaxBase(JI,T)*cumPass(JI,T) + sum(PB(P), benefitMaxChange(JI,PB,T)*action_benXcumPass(JI,PB,T));

eq_cumPass_root(J,T)$(JI(Root(J)))..
    cumPass(JI,T) =e= passBase(JI,T) + sum(PP(P), passChange(JI,PP,T)*actions(JI,PP));
*   cumPass(J,T) =e= passBase(J,T) + sum(ProjectsPassability(P), passChange(J,PP,T)*action_passXcumPass(J,PP,T));

eq_cumPass_upstream(JI,K,T)$((not Root(JI)) and Downstream(JI,K))..
    cumPass(JI,T) =e= passBase(JI,T)*cumPass(K,T) + sum(PP(P), passChange(JI,PP,T)*action_passXcumPass(JI,PP,T));

cn_budget(B)..
    sum((JC,P)$(Candidates(JC,P) and ProjectToBudget(JC,B)), cost(JC,P)*actions(JC,P)) =l= budget(B);

cn_cap_TC(T)$(TargetsControl(T))..
    sum(JC, cumBenBar(JC,T)) =l= cap(T);

cn_cap_TB(T)$(TargetsBeneficiary(T))..
    sum(JI, cumBenBar(JI,T)) =g= cap(T);

cn_action_benXcumPass_actionBen(JI,P,T)$(ProjectsBenefit(P))..
    action_benXcumPass(JI,P,T) =l= actions(JI,P);

cn_action_benXcumPass_cumPass(JI,P,T)$(ProjectsBenefit(P))..
    action_benXcumPass(JI,P,T) =l= cumPass(JI,T);

cn_action_passXcumPass_actionPass(JI,P,T)$(ProjectsPassability(P))..
    action_passXcumPass(JI,P,T) =l= actions(JI,P);

cn_action_passXcumPass_Root(JI,P,T)$(Root(JI) and TargetsControl(T) and ProjectsPassability(P))..
    action_passXcumPass(JI,P,T) =g= actions(JI,P);
* Austin Milt 02/11/2015 The specification for TargetsControl at Roots is
*   necessary to enforce non-negative passabilities for TargetsControl
*   throughout the network

cn_action_passXcumPass_cumPass(JI,K,P,T)$((not Root(JI)) and Downstream(JI,K) and ProjectsPassability(P))..
    action_passXcumPass(JI,P,T) =l= cumPass(K,T);

cn_action_passXcumPass_upstream(JI,K,P,T)$((not Root(JI)) and TargetsControl(T) and Downstream(JI,K) and ProjectsPassability(P))..
    action_passXcumPass(JI,P,T) =g= cumPass(K,T) + actions(JI,P) - 1;

* Checked by Austin Milt 11/05/2015 and does not change results (appears to not be necessary)
*cn_controlXcumPass_equality(J,T)..
*    action_benXcumPass(J,T) =g= cumPass(J,T) + actionBen(J) - 1;

model fishHabitat /all/;
option optcr = 1e-6;
fishHabitat.prioropt = 1;

* CALCULATE CONTROL SPECIES LIMITS ADJUSTMENT (TO RELAX TO FULL CAP OVER NETWORKS)
parameter theta(T) 'Relaxiton amount for invasives in networks';
theta(TC) = cap(TC) / speciesHabitat(TC);

* SOLVE
sets
	NetworkProjects(J,P,N) 'projects performed at each barrier in each network',
	ActionSet(J,P) 'projects to perform at each barrier';
parameters
	speciesNetworkHabitat(T,N) 'available habitat for each species in each network',
	networkSpending(N, B) 'amount spent in each network',
	networkLeftover(N,B) 'amount of budget remaining in each network',
	networkObjective(N) 'value of objective in each network',
	networkBest(N) 'best estimate for objective value in each sub-solve',
	solGap(N) 'absolute gap from optimal for each sub-solve',
	unused(B) 'unused part of budget';

Loop(N,
	
	JI(J) = yes$(BarrierNetwork(J,N) or BarrierAssociations(J,N));
	JC(J) = yes$(BarrierNetwork(J,N));
	
	cap(TC) = theta(TC)*controlNetworkHabitat(TC,N);
	budget(B) = networkBudgets(N,B) + unused(B);
	
	solve fishHabitat using mip max totalBenefit;
	abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';
	
	NetworkProjects(J,P,N)$(actions.l(J,P) and JN(J,N)) = yes;
	ActionSet(JI)$(actions.l(JI,P)) = yes;
	
	speciesNetworkHabitat(T,N) = sum(J$(BarrierNetwork(J,N)), cumBenBar.l(J,T));
	networkBudgets(N,B) = networkBudgets(N,B) + eps;
	networkSpending(N,B) = cn_budget.l(B) + eps;
	unused(B) = budget(B) - networkSpending(N) + eps;
	networkLeftover(N,B) = unused(B);
	
	networkObjective(N) = fishHabitat.objval + eps;
	networkObjective(N)$(fishHabitat.solveStat ne 1 or fishHabitat.modelStat ne 1) = totalBenefit.l + eps;
	networkBest(N) = fishHabitatobjest + eps;
	solGap(N) = abs(networkBest(N) - networkObjective(N)) + eps;
);


* WRITE OUTPUT GDX
Execute_Unload 'results',
    totalBenefit.l=objective, NetworkProjects, ActionSet, speciesNetworkHabitat,
	networkSpending, unused, networkLeftover, networkObjective,
	networkBest, solGap;
	
	
* write cplex options file
$ifthen set start
$onecho > cplex.opt
mipstart 1
$offecho
$endif
